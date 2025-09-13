#!/usr/bin/env python3
"""
Sistema de preview de PDFs - Premium Design
Responsável por gerar e exibir previews de arquivos PDF com interface premium
"""

import tkinter as tk
from typing import List, Optional
from io import BytesIO
import math

from .themes import ThemeManager
from .components import ScrollableFrame
from core.pdf_handler import PDFInfo
from config import PREVIEW_SCALE, PREVIEW_MAX_WIDTH, DEFAULT_FONT_FAMILY, MESSAGES

# Imports condicionais para preview
HAS_PREVIEW = False
try:
    from PIL import Image, ImageTk
    import fitz  # PyMuPDF
    HAS_PREVIEW = True
except ImportError:
    try:
        from PIL import Image, ImageTk
        HAS_PREVIEW = False
    except ImportError:
        HAS_PREVIEW = False

class PDFPreviewManager:
    """Gerenciador de preview de PDFs - Design Premium"""
    
    def __init__(self, parent_frame: tk.Frame, theme_manager: ThemeManager):
        self.parent = parent_frame
        self.theme_manager = theme_manager
        self.preview_images: List = []  # Cache de imagens
        self.page_cards: List = []  # Cards das páginas para efeitos hover
        self.columns = 2  # Número de colunas no grid
        
        self._setup_preview_area()
    
    def _setup_preview_area(self):
        """Configura a área de preview com design premium"""
        colors = self.theme_manager.get_colors()
        
        # Frame principal com gradiente simulado e sombra
        self.preview_frame = tk.Frame(
            self.parent,
            bg=colors['bg_primary'],
            relief='flat',
            borderwidth=0
        )
        
        # CRUCIAL: Fazer o preview_frame ocupar todo o parent
        self.preview_frame.pack(fill='both', expand=True, padx=8, pady=8)
        
        # Header com design limpo
        self._create_clean_header()
        
        # Área de conteúdo em grid responsivo
        self._create_responsive_content_area()
        
        # Mostrar mensagem inicial simples
        self._show_simple_placeholder()
    
    def _create_clean_header(self):
        """Cria header com design limpo e elegante"""
        colors = self.theme_manager.get_colors()
        
        # Header container com fundo elegante
        self.header_frame = tk.Frame(
            self.preview_frame, 
            bg=colors['bg_secondary'],
            relief='flat',
            borderwidth=0
        )
        self.header_frame.pack(fill='x', padx=15, pady=(15, 12))
        
        # Container interno para centralizanção
        header_content = tk.Frame(self.header_frame, bg=colors['bg_secondary'])
        header_content.pack(fill='x', padx=10, pady=8)
        
        # Título simples e limpo
        self.title_label = tk.Label(
            header_content,
            text="📖 Preview do Documento",
            font=(DEFAULT_FONT_FAMILY, 20, 'bold'),
            fg=colors['text_primary'],
            bg=colors['bg_secondary']
        )
        self.title_label.pack(side='left')
        
        # Nome do arquivo
        self.subtitle_label = tk.Label(
            header_content,
            text="",
            font=(DEFAULT_FONT_FAMILY, 13),
            fg=colors['text_secondary'],
            bg=colors['bg_secondary']
        )
        self.subtitle_label.pack(side='left', padx=(20, 0))
        
        # Container dos indicadores à direita
        indicator_frame = tk.Frame(header_content, bg=colors['bg_secondary'])
        indicator_frame.pack(side='right')
        
        # Contador de páginas simples
        self.page_counter = tk.Label(
            indicator_frame,
            text="",
            font=(DEFAULT_FONT_FAMILY, 14, 'bold'),
            fg=colors['progress_color'],
            bg=colors['bg_secondary']
        )
        self.page_counter.pack(side='right')
    
    def _create_responsive_content_area(self):
        """Cria área de conteúdo responsivo com layout em grid"""
        colors = self.theme_manager.get_colors()
        
        # Container principal com design elegante
        content_container = tk.Frame(
            self.preview_frame,
            bg=colors['bg_primary'],
            relief='flat',
            borderwidth=0
        )
        content_container.pack(fill='both', expand=True, padx=15, pady=(5, 15))
        
        # Frame scrollável premium
        self.scrollable_frame = ScrollableFrame(content_container, self.theme_manager)
        self.scrollable_frame.pack(fill='both', expand=True)
        
        # Área de conteúdo das páginas com padding elegante
        self.content_frame = self.scrollable_frame.scrollable_frame
        
        # Configurar grid responsivo
        self._configure_responsive_grid()
    
    def _configure_responsive_grid(self):
        """Configura grid responsivo para diferentes tamanhos de tela"""
        # Grid otimizado - ajustar colunas baseado no espaço disponível
        try:
            self.content_frame.update_idletasks()
            frame_width = max(self.content_frame.winfo_width(), 400)
            
            # Calcular número de colunas baseado na largura (mais responsivo)
            if frame_width < 500:
                self.columns = 1
            elif frame_width < 800:
                self.columns = 2
            else:
                self.columns = 3
            
            # Configurar peso das colunas para distribuição equilibrada e centralizada
            for i in range(self.columns):
                self.content_frame.grid_columnconfigure(i, weight=1, uniform="preview_columns")
            
            # Configurar padding para centralização horizontal
            self.content_frame.grid_columnconfigure(self.columns, weight=1)  # Coluna extra para centralizar
                
        except Exception:
            # Fallback seguro
            self.columns = 2
            for i in range(2):
                self.content_frame.grid_columnconfigure(i, weight=1, uniform="preview_columns")
    
    def show_pdf_preview(self, pdf_info: PDFInfo):
        """
        Mostra preview premium de um PDF com layout em grid
        
        Args:
            pdf_info: Informações do PDF a ser visualizado
        """
        if not HAS_PREVIEW:
            self._show_no_preview_message()
            return
        
        try:
            self._clear_preview()
            
            # Atualizar contador de páginas
            if pdf_info.pages == 1:
                page_text = "1 página"
            else:
                page_text = f"{pdf_info.pages} páginas"
            
            self.page_counter.config(text=page_text)
            
            # Atualizar nome do arquivo
            filename = pdf_info.name if len(pdf_info.name) <= 35 else pdf_info.name[:32] + "..."
            self.subtitle_label.config(text=filename)
            
            # Gerar preview otimizado
            self._generate_optimized_preview_grid(pdf_info)
            
        except Exception as e:
            print(f"Erro ao gerar preview: {e}")
            self._show_simple_error_message(f"Erro ao carregar preview: {str(e)}")
    
    def _generate_optimized_preview_grid(self, pdf_info: PDFInfo):
        """
        Gera preview otimizado e rápido em layout de grid
        
        Args:
            pdf_info: Informações do PDF
        """
        colors = self.theme_manager.get_colors()
        
        try:
            # Reconfigurar grid baseado na largura atual
            self._configure_responsive_grid()
            
            # Abrir documento PDF
            doc = fitz.open(pdf_info.path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Renderizar com resolução otimizada para velocidade
                mat = fitz.Matrix(1.0, 1.0)  # Resolução 1:1 - muito mais rápido
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                
                # Converter para PIL Image
                img = Image.open(BytesIO(img_data))
                
                # Tamanho dinâmico baseado no número de colunas - maiores
                if self.columns == 1:
                    card_image_width = 450  # Maior para coluna única
                elif self.columns == 2:
                    card_image_width = 300  # Maior para duas colunas
                else:  # 3 colunas
                    card_image_width = 220  # Ligeiramente maior
                
                card_image_height = int(card_image_width * (img.height / img.width))
                
                # Redimensionar otimizado
                img = img.resize((card_image_width, card_image_height), Image.Resampling.LANCZOS)
                
                # Converter para PhotoImage
                photo = ImageTk.PhotoImage(img)
                self.preview_images.append(photo)  # Manter referência
                
                # Calcular posição no grid
                row = page_num // self.columns
                col = page_num % self.columns
                
                # Criar card simples e otimizado
                page_card = self._create_simple_page_card(page_num + 1, photo, colors)
                
                # Posicionar no grid centralizado
                page_card.grid(
                    row=row, 
                    column=col, 
                    padx=12, 
                    pady=12, 
                    sticky='ew'  # Expandir horizontalmente
                )
                
                # Adicionar à lista de cards
                self.page_cards.append(page_card)
            
            doc.close()
            
            # Atualizar região de scroll de forma assíncrona
            self.scrollable_frame.canvas.after_idle(self._update_scroll_region)
            
            # Forçar refresh visual imediato
            self.content_frame.update_idletasks()
            
        except Exception as e:
            raise RuntimeError(f"Erro ao processar páginas do PDF: {str(e)}")
    
    def _create_simple_page_card(self, page_number: int, photo, colors: dict):
        """
        Cria card simples e rápido para uma página do preview
        
        Args:
            page_number: Número da página
            photo: Imagem da página
            colors: Dicionário de cores do tema
            
        Returns:
            Frame: Card da página configurado
        """
        # Card principal simples com tamanho mínimo
        card_frame = tk.Frame(
            self.content_frame,
            bg=colors['bg_secondary'],
            relief='solid',
            borderwidth=1,
            highlightbackground=colors['border'],
            highlightthickness=0,
            width=320,  # Largura mínima
            height=400  # Altura mínima
        )
        
        # Header simples
        header_frame = tk.Frame(card_frame, bg=colors['bg_secondary'])
        header_frame.pack(fill='x', padx=8, pady=(8, 5))
        
        # Número da página simples
        page_label = tk.Label(
            header_frame,
            text=f"Página {page_number}",
            font=(DEFAULT_FONT_FAMILY, 10, 'bold'),
            fg=colors['text_primary'],
            bg=colors['bg_secondary']
        )
        page_label.pack(side='left')
        
        # Container da imagem
        img_container = tk.Frame(
            card_frame,
            bg=colors['bg_secondary'],
            relief='flat'
        )
        img_container.pack(fill='both', expand=True, padx=8, pady=(0, 8))
        
        # Imagem da página centralizada
        img_label = tk.Label(
            img_container,
            image=photo,
            bg=colors['bg_secondary'],
            relief='flat',
            borderwidth=0,
            cursor='hand2'
        )
        img_label.pack(expand=True, anchor='center')
        
        # Configurar hover simples
        self._setup_simple_hover_effects(card_frame, colors)
        
        # Configurar scroll
        widgets_to_bind = [card_frame, header_frame, img_container, img_label]
        self._bind_scroll_events(widgets_to_bind)
        
        return card_frame
    
    def _setup_simple_hover_effects(self, card_frame, colors):
        """
        Configura efeitos hover simples e rápidos para os cards
        
        Args:
            card_frame: Frame do card
            colors: Dicionário de cores
        """
        original_bg = card_frame.cget('bg')
        hover_bg = colors['accent_blue'] if not self.theme_manager.is_dark_mode else colors['bg_tertiary']
        
        def on_enter(event):
            card_frame.config(bg=hover_bg)
        
        def on_leave(event):
            card_frame.config(bg=original_bg)
        
        # Aplicar eventos hover aos principais widgets
        widgets_for_hover = [card_frame]
        for child in card_frame.winfo_children():
            widgets_for_hover.append(child)
            for grandchild in child.winfo_children():
                widgets_for_hover.append(grandchild)
        
        for widget in widgets_for_hover:
            try:
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
            except:
                pass
    
    def _setup_card_hover_effects(self, shadow_frame, card_frame, colors):
        """
        Configura efeitos hover premium para os cards
        
        Args:
            shadow_frame: Frame da sombra
            card_frame: Frame do card
            colors: Dicionário de cores
        """
        original_shadow_color = shadow_frame.cget('bg')
        original_card_color = card_frame.cget('bg')
        
        # Cores de hover mais elegantes
        hover_shadow_color = '#CCCCCC' if not self.theme_manager.is_dark_mode else '#444444'
        hover_card_color = colors['accent_blue'] if not self.theme_manager.is_dark_mode else colors['bg_tertiary']
        
        def on_enter(event):
            shadow_frame.config(bg=hover_shadow_color)
            card_frame.config(bg=hover_card_color)
            shadow_frame.config(cursor='hand2')
        
        def on_leave(event):
            shadow_frame.config(bg=original_shadow_color)
            card_frame.config(bg=original_card_color)
            shadow_frame.config(cursor='arrow')
        
        # Aplicar eventos a todos os widgets do card
        widgets_for_hover = [shadow_frame, card_frame]
        for child in card_frame.winfo_children():
            widgets_for_hover.append(child)
            # Aplicar também aos filhos dos filhos
            for grandchild in child.winfo_children():
                widgets_for_hover.append(grandchild)
        
        for widget in widgets_for_hover:
            try:
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
            except:
                pass
    
    def _bind_scroll_events(self, widgets: List[tk.Widget]):
        """
        Configura eventos de scroll para widgets
        
        Args:
            widgets: Lista de widgets para configurar
        """
        for widget in widgets:
            widget.bind("<MouseWheel>", self.scrollable_frame._on_mousewheel)
            widget.bind("<Button-4>", self.scrollable_frame._on_mousewheel)
            widget.bind("<Button-5>", self.scrollable_frame._on_mousewheel)
            widget.bind("<Enter>", lambda e, w=widget: w.focus_set())
    
    def _show_simple_placeholder(self):
        """Mostra mensagem inicial simples quando nenhum PDF está selecionado"""
        self._clear_preview()
        
        colors = self.theme_manager.get_colors()
        
        # Limpar contador de páginas
        self.page_counter.config(text="")
        self.subtitle_label.config(text="")
        
        # Container central que ocupa todo o espaço
        placeholder_container = tk.Frame(
            self.content_frame,
            bg=colors['bg_primary']
        )
        placeholder_container.pack(expand=True, fill='both')
        
        # Frame interno para centralizar
        center_frame = tk.Frame(placeholder_container, bg=colors['bg_primary'])
        center_frame.pack(expand=True, fill='both')
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        
        # Container do conteúdo centralizado
        content_frame = tk.Frame(center_frame, bg=colors['bg_primary'])
        content_frame.grid(row=0, column=0)
        
        # Ícone maior e mais moderno
        icon_label = tk.Label(
            content_frame,
            text="📄",
            font=(DEFAULT_FONT_FAMILY, 64),
            fg=colors['text_secondary'],
            bg=colors['bg_primary']
        )
        icon_label.pack(pady=(0, 20))
        
        # Título mais elegante
        title_label = tk.Label(
            content_frame,
            text="Selecione um PDF para visualizar",
            font=(DEFAULT_FONT_FAMILY, 18, 'bold'),
            fg=colors['text_primary'],
            bg=colors['bg_primary']
        )
        title_label.pack(pady=(0, 12))
        
        # Descrição mais limpa
        desc_label = tk.Label(
            content_frame,
            text="Clique em um arquivo da lista para\nver o preview de todas as páginas",
            font=(DEFAULT_FONT_FAMILY, 14),
            fg=colors['text_secondary'],
            bg=colors['bg_primary'],
            justify='center',
            wraplength=300
        )
        desc_label.pack()
    
    def _show_no_preview_message(self):
        """Mostra mensagem quando preview não está disponível"""
        self._clear_preview()
        
        colors = self.theme_manager.get_colors()
        self.page_counter.config(text="")
        self.subtitle_label.config(text="")
        
        # Container simples
        error_container = tk.Frame(self.content_frame, bg=colors['bg_primary'])
        error_container.pack(expand=True, fill='both')
        
        # Ícone de alerta
        icon_label = tk.Label(
            error_container,
            text="⚠️",
            font=(DEFAULT_FONT_FAMILY, 48),
            fg=colors['warning_color'],
            bg=colors['bg_primary']
        )
        icon_label.pack(pady=(80, 15))
        
        # Título
        title_label = tk.Label(
            error_container,
            text="Preview Indisponível",
            font=(DEFAULT_FONT_FAMILY, 16, 'bold'),
            fg=colors['text_primary'],
            bg=colors['bg_primary']
        )
        title_label.pack(pady=(0, 8))
        
        # Mensagem
        message_label = tk.Label(
            error_container,
            text=MESSAGES['preview_unavailable'],
            font=(DEFAULT_FONT_FAMILY, 12),
            fg=colors['text_secondary'],
            bg=colors['bg_primary'],
            justify='center'
        )
        message_label.pack(pady=(0, 20))
    
    def _show_simple_error_message(self, error_text: str):
        """
        Mostra mensagem de erro simples
        
        Args:
            error_text: Texto do erro
        """
        self._clear_preview()
        
        colors = self.theme_manager.get_colors()
        self.page_counter.config(text="")
        self.subtitle_label.config(text="")
        
        # Container para erro
        error_container = tk.Frame(self.content_frame, bg=colors['bg_primary'])
        error_container.pack(expand=True, fill='both')
        
        # Ícone de erro
        icon_label = tk.Label(
            error_container,
            text="❌",
            font=(DEFAULT_FONT_FAMILY, 48),
            fg=colors['error_color'],
            bg=colors['bg_primary']
        )
        icon_label.pack(pady=(80, 15))
        
        # Título
        title_label = tk.Label(
            error_container,
            text="Erro no Preview",
            font=(DEFAULT_FONT_FAMILY, 16, 'bold'),
            fg=colors['error_color'],
            bg=colors['bg_primary']
        )
        title_label.pack(pady=(0, 8))
        
        # Mensagem do erro
        error_label = tk.Label(
            error_container,
            text=error_text,
            font=(DEFAULT_FONT_FAMILY, 12),
            fg=colors['text_secondary'],
            bg=colors['bg_primary'],
            justify='center'
        )
        error_label.pack(pady=(0, 20))
    
    def _clear_preview(self):
        """Limpa o preview atual"""
        # Limpar widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Limpar cache de imagens e cards
        self.preview_images.clear()
        self.page_cards.clear()
        
        # Reconfigurar grid
        for i in range(10):  # Limpar configuração de grid
            try:
                self.content_frame.grid_columnconfigure(i, weight=0)
            except:
                break
    
    def _update_scroll_region(self):
        """Atualiza região de scroll"""
        self.content_frame.update_idletasks()
        self.scrollable_frame.canvas.configure(
            scrollregion=self.scrollable_frame.canvas.bbox("all")
        )
    
    def clear_preview(self):
        """Limpa preview e mostra mensagem placeholder"""
        self._show_simple_placeholder()
    
    def pack(self, **kwargs):
        """Empacota o frame principal - forçar ocupar todo espaço"""
        kwargs.setdefault('fill', 'both')
        kwargs.setdefault('expand', True)
        self.preview_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Posiciona o frame principal no grid - forçar ocupar todo espaço"""
        kwargs.setdefault('sticky', 'nsew')
        self.preview_frame.grid(**kwargs)
    
    def update_theme(self, theme_manager: ThemeManager):
        """
        Atualiza tema premium do preview
        
        Args:
            theme_manager: Novo gerenciador de tema
        """
        self.theme_manager = theme_manager
        colors = theme_manager.get_colors()
        
        # Atualizar cores dos componentes principais
        self.preview_frame.config(bg=colors['bg_primary'])
        self.header_frame.config(bg=colors['bg_secondary'])
        self.title_label.config(fg=colors['text_primary'], bg=colors['bg_secondary'])
        self.subtitle_label.config(fg=colors['text_secondary'], bg=colors['bg_secondary'])
        
        # Atualizar contador de páginas
        if hasattr(self, 'page_counter'):
            self.page_counter.config(fg=colors['progress_color'], bg=colors['bg_secondary'])
        
        # Atualizar frame scrollável
        self.scrollable_frame.update_theme(theme_manager)
        
        # Se houver cards ativos, recriar com novo tema
        if self.page_cards:
            # Salvar estado atual e recriar preview
            current_preview_active = len(self.page_cards) > 0
            if current_preview_active:
                # Recriar preview mantém a funcionalidade, mas é melhor deixar 
                # para o controle externo decidir quando recriar
                pass
