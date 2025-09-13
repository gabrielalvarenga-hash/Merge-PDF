#!/usr/bin/env python3
"""
Sistema de preview de PDFs - Premium Design
Responsável por gerar e exibir previews de arquivos PDF com interface premium
"""

import tkinter as tk
from typing import List, Optional
from io import BytesIO

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
        """Configura grid responsivo para diferentes tamanhos de tela com centralização melhorada"""
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
            
            # Limpar configurações anteriores
            for i in range(10):
                try:
                    self.content_frame.grid_columnconfigure(i, weight=0, minsize=0)
                except:
                    pass
            
            # MELHOR CENTRALIZAÇÃO: Configurar colunas com espaçamento lateral
            if self.columns == 1:
                # 1 coluna: espaço lateral maior para centralizar melhor
                self.content_frame.grid_columnconfigure(0, weight=2)  # Espaço esquerda  
                self.content_frame.grid_columnconfigure(1, weight=0, minsize=400)  # Conteúdo fixo
                self.content_frame.grid_columnconfigure(2, weight=2)  # Espaço direita
                self._content_start_col = 1
            else:
                # Múltiplas colunas: espaçamento lateral para centralização
                self.content_frame.grid_columnconfigure(0, weight=1)  # Espaço esquerda
                for i in range(self.columns):
                    self.content_frame.grid_columnconfigure(i + 1, weight=3, uniform="preview_columns")  # Conteúdo
                self.content_frame.grid_columnconfigure(self.columns + 1, weight=1)  # Espaço direita  
                self._content_start_col = 1
                
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
        Gera preview ultra-otimizado com carregamento lazy das páginas
        
        Args:
            pdf_info: Informações do PDF
        """
        colors = self.theme_manager.get_colors()
        
        try:
            # Reconfigurar grid baseado na largura atual
            self._configure_responsive_grid()
            
            # Abrir documento PDF
            doc = fitz.open(pdf_info.path)
            total_pages = len(doc)
            
            # OTIMIZAÇÃO: Carregar apenas as primeiras páginas para início rápido
            initial_pages_to_load = min(4, total_pages)  # Máximo 4 páginas iniciais
            
            # Carregar páginas iniciais imediatamente
            for page_num in range(initial_pages_to_load):
                self._create_page_preview(doc, page_num, colors)
            
            # Fechar documento temporariamente para economizar memória
            doc.close()
            
            # Se há mais páginas, criar placeholders e carregar assincronamente
            if total_pages > initial_pages_to_load:
                self._create_remaining_page_placeholders(pdf_info, initial_pages_to_load, total_pages, colors)
                
                # Carregar páginas restantes em background após 200ms
                self.content_frame.after(200, lambda: self._load_remaining_pages_async(pdf_info, initial_pages_to_load))
            
            # Atualizar região de scroll de forma assíncrona
            self.scrollable_frame.canvas.after_idle(self._update_scroll_region)
            
            # Forçar refresh visual imediato
            self.content_frame.update_idletasks()
            
        except Exception as e:
            raise RuntimeError(f"Erro ao processar páginas do PDF: {str(e)}")
    
    def _create_page_preview(self, doc, page_num, colors):
        """Cria preview de uma página específica otimizado para velocidade"""
        page = doc[page_num]
        
        # OTIMIZAÇÃO: Resolução ainda menor para velocidade máxima
        mat = fitz.Matrix(0.7, 0.7)  # 70% da resolução - mais rápido
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        
        # Converter para PIL Image
        img = Image.open(BytesIO(img_data))
        
        # Tamanho otimizado menor para carregamento mais rápido
        if self.columns == 1:
            card_image_width = 350  # Menor que antes
        elif self.columns == 2:
            card_image_width = 240  # Menor que antes
        else:  # 3 colunas
            card_image_width = 180  # Menor que antes
        
        card_image_height = int(card_image_width * (img.height / img.width))
        
        # Redimensionar com algoritmo mais rápido
        img = img.resize((card_image_width, card_image_height), Image.Resampling.NEAREST)  # Mais rápido que LANCZOS
        
        # Converter para PhotoImage
        photo = ImageTk.PhotoImage(img)
        self.preview_images.append(photo)  # Manter referência
        
        # Calcular posição no grid centralizado
        row = page_num // self.columns
        col = (page_num % self.columns) + getattr(self, '_content_start_col', 0)
        
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
        
        # Configurar scroll para todos os widgets do card
        self._bind_scroll_to_card_widgets(page_card)
        
        # Adicionar à lista de cards
        self.page_cards.append(page_card)
    
    def _create_remaining_page_placeholders(self, pdf_info, start_page, total_pages, colors):
        """Cria placeholders para páginas que serão carregadas depois"""
        for page_num in range(start_page, total_pages):
            row = page_num // self.columns
            col = (page_num % self.columns) + getattr(self, '_content_start_col', 0)
            
            # Criar placeholder simples
            placeholder = self._create_page_placeholder(page_num + 1, colors)
            placeholder.grid(row=row, column=col, padx=12, pady=12, sticky='ew')
            
            # Configurar scroll para o placeholder
            self._bind_scroll_to_card_widgets(placeholder)
            
            self.page_cards.append(placeholder)
    
    def _create_page_placeholder(self, page_number, colors):
        """Cria um placeholder para página que será carregada"""
        card = tk.Frame(
            self.content_frame,
            bg=colors['bg_secondary'],
            relief='solid',
            borderwidth=1,
            cursor='hand2'
        )
        
        # Placeholder visual
        placeholder_label = tk.Label(
            card,
            text=f"Carregando\npágina {page_number}...",
            font=(DEFAULT_FONT_FAMILY, 10),
            fg=colors['text_secondary'],
            bg=colors['bg_secondary'],
            height=8,  # Altura padrão do placeholder
            width=20
        )
        placeholder_label.pack(pady=10)
        
        return card
    
    def _load_remaining_pages_async(self, pdf_info, start_page):
        """Carrega páginas restantes em background de forma assíncrona"""
        try:
            import threading
            
            def load_in_background():
                try:
                    doc = fitz.open(pdf_info.path)
                    total_pages = len(doc)
                    
                    for page_num in range(start_page, total_pages):
                        # Carregar página
                        page = doc[page_num]
                        mat = fitz.Matrix(0.7, 0.7)  # Mesma resolução otimizada
                        pix = page.get_pixmap(matrix=mat)
                        img_data = pix.tobytes("ppm")
                        
                        img = Image.open(BytesIO(img_data))
                        
                        # Mesmo tamanho otimizado
                        if self.columns == 1:
                            card_image_width = 350
                        elif self.columns == 2:
                            card_image_width = 240
                        else:
                            card_image_width = 180
                        
                        card_image_height = int(card_image_width * (img.height / img.width))
                        img = img.resize((card_image_width, card_image_height), Image.Resampling.NEAREST)
                        photo = ImageTk.PhotoImage(img)
                        
                        # Atualizar UI na thread principal
                        self.content_frame.after(0, lambda p=page_num, ph=photo: self._replace_placeholder_with_image(p, ph))
                    
                    doc.close()
                    
                except Exception as e:
                    print(f"Erro ao carregar páginas em background: {e}")
            
            # Executar em thread separada
            thread = threading.Thread(target=load_in_background, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"Erro ao iniciar carregamento assíncrono: {e}")
    
    def _replace_placeholder_with_image(self, page_num, photo):
        """Substitui placeholder pela imagem real carregada"""
        try:
            if page_num < len(self.page_cards):
                placeholder = self.page_cards[page_num]
                colors = self.theme_manager.get_colors()
                
                # Limpar placeholder
                for widget in placeholder.winfo_children():
                    widget.destroy()
                
                # Adicionar imagem real
                self.preview_images.append(photo)  # Manter referência
                
                image_label = tk.Label(
                    placeholder,
                    image=photo,
                    bg=colors['bg_secondary'],
                    cursor='hand2'
                )
                image_label.pack(pady=5)
                
                # Adicionar número da página
                page_number_label = tk.Label(
                    placeholder,
                    text=f"Página {page_num + 1}",
                    font=(DEFAULT_FONT_FAMILY, 10, 'bold'),
                    fg=colors['text_primary'],
                    bg=colors['bg_secondary']
                )
                page_number_label.pack(pady=(0, 8))
                
        except Exception as e:
            print(f"Erro ao substituir placeholder: {e}")
    
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
    
    def _bind_scroll_to_card_widgets(self, parent_widget):
        """Aplica eventos de scroll recursivamente para todos os widgets de um card de página"""
        try:
            # Aplicar scroll no widget pai
            parent_widget.bind("<MouseWheel>", self.scrollable_frame._on_mousewheel)
            parent_widget.bind("<Button-4>", self.scrollable_frame._on_mousewheel)
            parent_widget.bind("<Button-5>", self.scrollable_frame._on_mousewheel)
            parent_widget.bind("<Enter>", lambda e: parent_widget.focus_set())
            
            # Aplicar recursivamente em todos os widgets filhos
            for child in parent_widget.winfo_children():
                self._bind_scroll_to_card_widgets(child)
        except Exception:
            # Ignora erros em widgets que não suportam eventos
            pass
    
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
        
        # Aplicar scroll ao placeholder
        self._bind_scroll_to_card_widgets(placeholder_container)
        
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
        
        # Aplicar scroll ao container de erro
        self._bind_scroll_to_card_widgets(error_container)
        
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
        
        # Aplicar scroll ao container de erro
        self._bind_scroll_to_card_widgets(error_container)
        
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
