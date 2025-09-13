#!/usr/bin/env python3
"""
Janela principal do PDF Merger App
Integra todos os módulos e componentes da aplicação
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import sys
import os

# Imports dos módulos da aplicação
from config import *
from ui.themes import ThemeManager, ThemeMode
from ui.components import ModernButton, StatusLabel, ProgressFrame
from ui.preview import PDFPreviewManager
from ui.drag_drop import DragDropManager, DraggableListManager
from core.file_manager import PDFFileManager
from core.pdf_handler import PDFMerger, format_file_size

# Imports condicionais
try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

class PDFMergerMainWindow:
    """Janela principal da aplicação PDF Merger"""
    
    def __init__(self, root):
        # Configurar root com drag & drop se disponível
        if HAS_DND and not isinstance(root, TkinterDnD.Tk):
            self.root = TkinterDnD.Tk()
            root.destroy()  # Limpar root original se necessário
        else:
            self.root = root
        
        # Componentes principais
        self.theme_manager = ThemeManager(ThemeMode.LIGHT)
        self.file_manager = PDFFileManager()
        self.drag_drop_manager = DragDropManager(self.theme_manager)
        self.pdf_merger = PDFMerger()
        
        # Componentes UI
        self.preview_manager = None
        self.status_label = None
        self.progress_frame = None
        self.draggable_list = None
        
        # Variáveis de controle
        self.compression_var = None
        self.standardize_a4_var = None
        
        # Referências dos widgets e estado visual para DnD/centralização
        self.item_widgets = []
        self.drop_indicator = None
        self._last_drop_raw_target = None
        
        # Configurar callbacks
        self._setup_callbacks()
        
        # Inicializar interface
        self._setup_window()
        self._setup_icon()
        self._create_interface()
        
        # Configurar drag & drop
        self._setup_drag_drop()
    
    def _setup_callbacks(self):
        """Configura callbacks entre componentes"""
        # Callbacks do file manager
        self.file_manager.set_callbacks(
            on_files_changed=self._on_files_changed,
            on_selection_changed=self._on_selection_changed
        )
        
        # Callbacks do drag & drop
        self.drag_drop_manager.set_callbacks(
            on_files_dropped=self._on_files_dropped,
            on_item_moved=self._on_item_moved,
            on_item_clicked=self._on_item_clicked
        )
        
        # Callback do PDF merger
        self.pdf_merger.set_progress_callback(self._on_merge_progress)
    
    def _setup_window(self):
        """Configura a janela principal"""
        self.root.title(APP_NAME)
        
        # Posicionar janela mais à direita da tela
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Janela 1200x800 posicionada mais à direita (30% da largura da tela)
        window_x = int(screen_width * 0.25)  # 25% para a direita
        window_y = int((screen_height - 800) / 2)  # Centralizada verticalmente
        
        self.root.geometry(f"1200x800+{window_x}+{window_y}")
        self.root.minsize(*MIN_WINDOW_SIZE)
        
        # Aplicar cores do tema
        colors = self.theme_manager.get_colors()
        self.root.configure(bg=colors['bg_primary'])
        
        # Configurar fonte padrão
        try:
            self.root.option_add('*Font', f'{DEFAULT_FONT_FAMILY} {DEFAULT_FONT_SIZE}')
        except:
            self.root.option_add('*Font', f'Arial {DEFAULT_FONT_SIZE}')
        
        # Centralizar na tela
        self._center_window()
        
        # Configurar redimensionamento
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
    
    def _center_window(self):
        """Centraliza a janela na tela"""
        self.root.update_idletasks()
        
        # Obter dimensões
        width = int(WINDOW_SIZE.split('x')[0])
        height = int(WINDOW_SIZE.split('x')[1])
        
        # Calcular posição central
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        
        self.root.geometry(f"{WINDOW_SIZE}+{x}+{y}")
    
    def _setup_icon(self):
        """Configura ícone da janela"""
        try:
            logo_path = get_logo_path()
            
            if os.path.exists(logo_path):
                from PIL import Image, ImageTk
                
                # Carregar e otimizar logo
                logo_img = Image.open(logo_path)
                original_size = logo_img.size
                
                # Redimensionar se necessário
                max_size = 256
                if max(original_size) > max_size:
                    ratio = min(max_size / original_size[0], max_size / original_size[1])
                    new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
                    logo_img = logo_img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Definir como ícone
                self.logo_icon = ImageTk.PhotoImage(logo_img)
                self.root.iconphoto(True, self.logo_icon)
                
                print(f"✅ Logo carregado: {logo_path}")
            else:
                print(f"⚠️ Logo não encontrado: {logo_path}")
                
        except Exception as e:
            print(f"❌ Erro ao carregar logo: {e}")
    
    def _create_interface(self):
        """Cria a interface principal"""
        # Container principal
        main_container = tk.Frame(self.root, bg=self.theme_manager.get_color('bg_primary'))
        main_container.grid(row=0, column=0, sticky='nsew', padx=20, pady=16)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=4, minsize=600) # Lista de arquivos - mais espaço para inserção e controles
        main_container.grid_columnconfigure(1, weight=2)  # Preview - área menor para dar mais espaço à lista
        
        # Criar seções da interface
        self._create_header(main_container)
        self._create_main_content(main_container)
    
    def _create_header(self, parent):
        """Cria header minimalista da aplicação"""
        colors = self.theme_manager.get_colors()
        
        header_frame = tk.Frame(parent, bg=colors['bg_primary'], height=90)
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 35))
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_propagate(False)
        
        # Botão de tema minimalista
        self.theme_btn = ModernButton(
            header_frame,
            self.theme_manager,
            'secondary',
            text=UI_CONFIG['button_texts']['theme_light'],
            padx=12,
            pady=6,
            command=self._toggle_theme,
            font=(DEFAULT_FONT_FAMILY, 10)
        )
        self.theme_btn.grid(row=0, column=0, sticky='nw', padx=(0, 20), pady=10)
        
        # Título minimalista centralizado
        title_container = tk.Frame(header_frame, bg=colors['bg_primary'])
        title_container.grid(row=0, column=1, sticky='ew')
        
        title_label = tk.Label(
            title_container,
            text="PDF Merger",
            font=(DEFAULT_FONT_FAMILY, 36, 'bold'),
            fg=colors['text_primary'],
            bg=colors['bg_primary']
        )
        title_label.pack(pady=(15, 8))
        
        subtitle_label = tk.Label(
            title_container,
            text="Junte e otimize seus PDFs",
            font=(DEFAULT_FONT_FAMILY, 16, 'normal'),
            fg=colors['text_secondary'],
            bg=colors['bg_primary']
        )
        subtitle_label.pack()
    
    def _create_main_content(self, parent):
        """Cria conteúdo principal"""
        # Área de conteúdo esquerda (lista de arquivos)
        self._create_file_list_area(parent)
        
        # Área de preview direita
        self._create_preview_area(parent)
    
    def _create_file_list_area(self, parent):
        """Cria área da lista de arquivos"""
        colors = self.theme_manager.get_colors()
        
        content_frame = tk.Frame(parent, bg=colors['bg_primary'])
        content_frame.grid(row=1, column=0, sticky='nsew', padx=(0, WIDGET_SPACING))
        content_frame.grid_rowconfigure(1, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Botões de ação
        self._create_action_buttons(content_frame)
        
        # Lista de arquivos
        self._create_file_list(content_frame)
        
        # Botão de merge destacado
        self._create_merge_button(content_frame)
        
        # Controles inferiores (sem botão merge)
        self._create_bottom_controls(content_frame)
    
    def _create_action_buttons(self, parent):
        """Cria botões de ação minimalistas"""
        buttons_frame = tk.Frame(parent, bg=self.theme_manager.get_color('bg_primary'))
        buttons_frame.grid(row=0, column=0, sticky='ew', pady=(0, 25))
        
        # Botão Adicionar - destaque principal
        self.add_btn = ModernButton(
            buttons_frame,
            self.theme_manager,
            'primary',
            text="+ Adicionar PDFs",
            font=(DEFAULT_FONT_FAMILY, 13, 'bold'),
            padx=24,
            pady=16,
            command=self._add_files
        )
        self.add_btn.pack(side='left', padx=(0, 16))
        
        # Botão Limpar - mais discreto
        self.clear_btn = ModernButton(
            buttons_frame,
            self.theme_manager,
            'secondary',
            text="Limpar",
            font=(DEFAULT_FONT_FAMILY, 12),
            padx=20,
            pady=14,
            command=self._clear_files
        )
        self.clear_btn.pack(side='left', padx=(0, 16))
        
        # Botão Ordenar - mais discreto
        self.sort_btn = ModernButton(
            buttons_frame,
            self.theme_manager,
            'secondary',
            text="A-Z",
            font=(DEFAULT_FONT_FAMILY, 12),
            padx=20,
            pady=14,
            command=self._toggle_sort_order
        )
        self.sort_btn.pack(side='left')
    
    def _create_file_list(self, parent):
        """Cria lista de arquivos minimalista com drag & drop"""
        colors = self.theme_manager.get_colors()
        
        list_container = tk.Frame(
            parent, 
            bg=colors['bg_tertiary'], 
            relief='flat', 
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=colors.get('border_color', '#E0E0E0'),
            highlightbackground=colors.get('border_color', '#E0E0E0')
        )
        list_container.grid(row=1, column=0, sticky='nsew', pady=(0, 20))
        list_container.grid_rowconfigure(1, weight=1)
        list_container.grid_columnconfigure(0, weight=1)
        
        # Header minimalista da lista
        self._create_list_header(list_container)
        
        # Área scrollável da lista
        self._create_scrollable_list(list_container)
    
    def _create_list_header(self, parent):
        """Cria header minimalista da lista de arquivos"""
        colors = self.theme_manager.get_colors()
        
        list_header = tk.Frame(parent, bg=colors['bg_tertiary'])
        list_header.grid(row=0, column=0, sticky='ew', padx=24, pady=(24, 18))
        
        # Título mais limpo
        list_title = tk.Label(
            list_header,
            text="Arquivos",
            font=(DEFAULT_FONT_FAMILY, 18, 'bold'),
            fg=colors['text_primary'],
            bg=colors['bg_tertiary']
        )
        list_title.pack(side='left')
        
        # Container para indicadores - design mais limpo
        indicators_frame = tk.Frame(list_header, bg=colors['bg_tertiary'])
        indicators_frame.pack(side='right')
        
        # Contador combinado mais elegante
        self.total_pages_label = tk.Label(
            indicators_frame,
            text="0 páginas",
            font=(DEFAULT_FONT_FAMILY, 13, 'normal'),
            fg=colors['text_secondary'],
            bg=colors['bg_tertiary']
        )
        self.total_pages_label.pack(side='right', padx=(0, 20))
        
        self.total_size_label = tk.Label(
            indicators_frame,
            text="0 MB",
            font=(DEFAULT_FONT_FAMILY, 13, 'bold'),
            fg=colors['text_secondary'],
            bg=colors['bg_tertiary']
        )
        self.total_size_label.pack(side='right', padx=(0, 12))
    
    def _create_scrollable_list(self, parent):
        """Cria área scrollável da lista"""
        # Frame da lista
        list_frame = tk.Frame(parent, bg=self.theme_manager.get_color('bg_primary'))
        list_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 20))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas com scroll
        self.canvas = tk.Canvas(
            list_frame, 
            bg=self.theme_manager.get_color('bg_primary'), 
            highlightthickness=0
        )
        self.scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.theme_manager.get_color('bg_primary'))
        
        # Configurar scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Criar janela do frame dentro do canvas e manter referência
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Garantir que a largura do frame scrollável acompanhe a largura do canvas
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.canvas_window, width=e.width)
        )
        
        # Posicionar elementos
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Configurar eventos de scroll
        self._bind_scroll_events(self.canvas)
        self._bind_scroll_events(self.scrollable_frame)
        
        # Criar gerenciador de lista arrastável
        self.draggable_list = DraggableListManager(self.canvas, self.drag_drop_manager)
        # Helpers para UX de arrastar mais fluida
        try:
            self.drag_drop_manager.set_drop_helpers(
                get_drop_index=self._get_drop_index,
                show_drop_indicator=self._show_drop_indicator,
                hide_drop_indicator=self._hide_drop_indicator
            )
        except Exception:
            pass
        
        # Mostrar lista vazia inicial
        self._show_empty_list_message()
    
    def _create_merge_button(self, parent):
        """Cria botão de merge destacado"""
        merge_container = tk.Frame(parent, bg=self.theme_manager.get_color('bg_primary'))
        merge_container.grid(row=2, column=0, sticky='ew', pady=(15, 0))
        
        # Botão de merge principal destacado
        self.merge_btn = ModernButton(
            merge_container,
            self.theme_manager,
            'primary',
            text="🔗 Juntar PDFs",
            font=(DEFAULT_FONT_FAMILY, 16, 'bold'),
            padx=60,
            pady=20,
            command=self._merge_pdfs
        )
        self.merge_btn.pack()
        
        # Barra de progresso
        self.progress_frame = ProgressFrame(merge_container, self.theme_manager)
        self.progress_frame.pack()
    
    def _bind_scroll_events(self, widget):
        """Configura eventos de scroll"""
        widget.bind("<MouseWheel>", self._on_list_mousewheel)
        widget.bind("<Button-4>", self._on_list_mousewheel)
        widget.bind("<Button-5>", self._on_list_mousewheel)
        widget.bind("<Enter>", lambda e: widget.focus_set())
    
    def _on_list_mousewheel(self, event):
        """Handler para scroll com mouse wheel"""
        try:
            delta = getattr(event, 'delta', 0)
            if delta != 0:
                scroll_amount = 1 if abs(delta) <= 5 else 2
                direction = -scroll_amount if delta > 0 else scroll_amount
                self.canvas.yview_scroll(direction, "units")
            elif hasattr(event, 'num'):
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
        except Exception:
            pass
    
    def _create_preview_area(self, parent):
        """Cria área de preview"""
        # Criar preview manager
        preview_container = tk.Frame(parent)
        self.preview_manager = PDFPreviewManager(preview_container, self.theme_manager)
        self.preview_manager.grid(sticky='nsew', row=0, column=0)
        
        # Posicionar container
        preview_container.grid(row=1, column=1, sticky='nsew', padx=(WIDGET_SPACING, 0))
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)
    
    def _create_bottom_controls(self, parent):
        """Cria controles inferiores"""
        colors = self.theme_manager.get_colors()
        
        bottom_frame = tk.Frame(parent, bg=colors['bg_primary'])
        bottom_frame.grid(row=3, column=0, sticky='ew')
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        # Opções de compressão
        self._create_compression_options(bottom_frame)
        
        # Opção de padronização A4
        self._create_a4_standardization_option(bottom_frame)
        
        # Status label
        self.status_label = StatusLabel(bottom_frame, self.theme_manager)
        self.status_label.grid(row=2, column=0, sticky='ew', pady=5)
    
    def _create_compression_options(self, parent):
        """Cria seção minimalista sobre processamento A4"""
        colors = self.theme_manager.get_colors()
        
        processing_frame = tk.Frame(parent, bg=colors['bg_primary'])
        processing_frame.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        
        # Variável de controle - sempre A4 obrigatório
        self.compression_var = tk.StringVar(value="a4_only")
        
        # Card informativo minimalista
        info_card = tk.Frame(
            processing_frame, 
            bg=colors.get('bg_secondary', colors['bg_tertiary']),
            relief='flat',
            borderwidth=0,
            highlightthickness=1,
            highlightcolor=colors.get('border_color', '#E8E8E8'),
            highlightbackground=colors.get('border_color', '#E8E8E8')
        )
        info_card.pack(fill='x', pady=(0, 0))
        
        # Conteúdo do card
        card_content = tk.Frame(info_card, bg=colors.get('bg_secondary', colors['bg_tertiary']))
        card_content.pack(fill='x', padx=16, pady=12)
        
        # Ícone e título
        title_frame = tk.Frame(card_content, bg=colors.get('bg_secondary', colors['bg_tertiary']))
        title_frame.pack(fill='x', pady=(0, 8))
        
        icon_label = tk.Label(
            title_frame,
            text="📐",
            font=(DEFAULT_FONT_FAMILY, 16),
            fg=colors['text_primary'],
            bg=colors.get('bg_secondary', colors['bg_tertiary'])
        )
        icon_label.pack(side='left', padx=(0, 8))
        
        title_label = tk.Label(
            title_frame,
            text="Formato A4 Padrão",
            font=(DEFAULT_FONT_FAMILY, 14, 'bold'),  # Fonte maior
            fg=colors['text_primary'],
            bg=colors.get('bg_secondary', colors['bg_tertiary'])
        )
        title_label.pack(side='left')
        
        # Descrição limpa
        desc_label = tk.Label(
            card_content,
            text="Todas as páginas serão automaticamente padronizadas para o formato A4 profissional",
            font=(DEFAULT_FONT_FAMILY, 12),  # Fonte maior
            fg=colors['text_secondary'],
            bg=colors.get('bg_secondary', colors['bg_tertiary']),
            wraplength=500,
            justify='left'
        )
        desc_label.pack(anchor='w')
    
    def _create_a4_standardization_option(self, parent):
        """Configura variável A4 sempre como obrigatória"""
        # Variável para controlar opção A4 - SEMPRE MARCADA E OBRIGATÓRIA
        self.standardize_a4_var = tk.BooleanVar(value=True)
        # Não precisa criar interface visual adicional pois já está no método anterior
    
    
    def _setup_drag_drop(self):
        """Configura sistema de drag & drop"""
        # Drag & drop externo se disponível
        if HAS_DND:
            success = self.drag_drop_manager.setup_external_drag_drop(
                self.canvas,
                self.scrollable_frame
            )
            if success:
                print("✅ Drag & drop de arquivos habilitado")
            else:
                print("❌ Erro ao configurar drag & drop")
        else:
            print(MESSAGES['dnd_warning'])
    
    # Event Handlers
    def _on_files_changed(self):
        """Callback quando lista de arquivos muda"""
        self._update_file_list()
        self._update_total_pages()
        self._update_total_size()
        
        # Centralizar item selecionado após atualização
        self.root.after(80, self._center_selected_item)
    
    def _on_selection_changed(self, selected_index):
        """Callback quando seleção muda"""
        self._update_file_list()  # Atualizar destaque
        
        if selected_index is not None:
            selected_pdf = self.file_manager.selected_pdf
            if selected_pdf and self.preview_manager:
                self.preview_manager.show_pdf_preview(selected_pdf)
                
                # Forçar atualização do layout após mostrar preview
                self.root.after(100, lambda: [
                    self.root.update_idletasks(),
                    self.preview_manager.preview_frame.update_idletasks(),
                    self._center_selected_item()
                ])
        else:
            if self.preview_manager:
                self.preview_manager.clear_preview()
    
    def _on_files_dropped(self, file_paths):
        """Callback quando arquivos são arrastados"""
        added_count = self.file_manager.add_files(file_paths)
        if added_count > 0:
            self._show_status(f"{added_count} PDF(s) adicionado(s) por drag & drop")
        else:
            self._show_status("Nenhum PDF válido foi adicionado")
    
    def _on_item_moved(self, from_index, to_index):
        """Callback quando item é movido por drag"""
        # Limitar índices
        max_index = self.file_manager.total_files - 1
        to_index = max(0, min(to_index, max_index))
        
        if self.file_manager.move_file_to_position(from_index, to_index):
            self._show_status("Ordem alterada")
    
    def _on_item_clicked(self, index):
        """Callback quando item é clicado"""
        self.file_manager.set_selection(index)
    
    def _on_merge_progress(self, value, message):
        """Callback para progresso do merge"""
        if self.progress_frame:
            self.progress_frame.update_progress(value, message)
    
    # UI Update Methods
    def _update_file_list(self):
        """Atualiza visualização da lista de arquivos"""
        # Limpar lista atual
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.draggable_list.clear_items()
        self._hide_drop_indicator()
        self.item_widgets = []
        
        if self.file_manager.is_empty():
            self._show_empty_list_message()
        else:
            self._show_file_items()
    
    def _show_empty_list_message(self):
        """Mostra mensagem de lista vazia"""
        colors = self.theme_manager.get_colors()
        
        message = MESSAGES['empty_list_with_dnd'] if HAS_DND else MESSAGES['empty_list']
        
        empty_label = tk.Label(
            self.scrollable_frame,
            text=message,
            font=(DEFAULT_FONT_FAMILY, BUTTON_FONT_SIZE),
            fg=colors['text_secondary'],
            bg=colors['bg_primary'],
            justify='center'
        )
        empty_label.pack(expand=True, fill='both', pady=50)
    
    def _show_file_items(self):
        """Mostra itens da lista de arquivos"""
        for i, pdf_info in enumerate(self.file_manager.pdf_files):
            self._create_file_item(i, pdf_info)
    
    def _create_file_item(self, index, pdf_info):
        """Cria item visual para arquivo PDF"""
        colors = self.theme_manager.get_colors()
        is_selected = index == self.file_manager.selected_index
        bg_color = colors['selected'] if is_selected else colors['bg_primary']
        
        # Frame do item com espaçamento melhorado
        item_frame = tk.Frame(
            self.scrollable_frame,
            bg=bg_color,
            relief='solid',
            borderwidth=1,
            cursor='hand2'
        )
        item_frame.pack(fill='x', padx=12, pady=8)
        
        # Container interno com padding melhorado
        inner_frame = tk.Frame(item_frame, bg=bg_color)
        inner_frame.pack(fill='x', padx=20, pady=16)
        inner_frame.grid_columnconfigure(0, weight=1)  # Info ocupa espaço disponível
        inner_frame.grid_columnconfigure(1, weight=0, minsize=140)  # Controles com largura mínima
        
        # Informações do arquivo
        info_frame = tk.Frame(inner_frame, bg=bg_color)
        info_frame.grid(row=0, column=0, sticky='ew', padx=(0, 20))
        
        name_label = tk.Label(
            info_frame,
            text=f"📄 {pdf_info.name}",
            font=(DEFAULT_FONT_FAMILY, 15, 'bold'),
            fg=colors['text_primary'],
            bg=bg_color,
            anchor='w'
        )
        name_label.pack(anchor='w', pady=(0, 4))
        
        # Info do arquivo
        file_info = self.file_manager.get_file_info_summary(index)
        size_label = tk.Label(
            info_frame,
            text=file_info,
            font=(DEFAULT_FONT_FAMILY, 12),
            fg=colors['text_secondary'],
            bg=bg_color,
            anchor='w'
        )
        size_label.pack(anchor='w')
        
        # Controles
        self._create_item_controls(inner_frame, index, bg_color)
        
        # Adicionar à lista arrastável
        item_data = {'index': index, 'pdf_info': pdf_info}
        self.draggable_list.add_draggable_item(
            item_frame,
            item_data,
            lambda e, idx=index: self._on_item_clicked(idx)
        )
        
        # Vincular drag apenas ao handle (ícone ⋮⋮)
        try:
            handle_widget = None
            # Procurar pelo label do handle dentro do inner_frame coluna 1
            for child in parent.winfo_children():
                pass
        except Exception:
            pass
        
        # Guardar referência para centralização posterior
        if index >= len(self.item_widgets):
            self.item_widgets.extend([None] * (index - len(self.item_widgets) + 1))
        self.item_widgets[index] = item_frame

    def _center_selected_item(self):
        """Centraliza o item selecionado na área visível da lista"""
        try:
            selected_index = self.file_manager.selected_index
            if selected_index is None:
                return
            if selected_index >= len(self.item_widgets) or self.item_widgets[selected_index] is None:
                return
            
            # Garantir que dimensões estejam calculadas
            self.root.update_idletasks()
            
            item = self.item_widgets[selected_index]
            item_y = item.winfo_y()  # posição do topo no frame scrollável
            item_h = max(1, item.winfo_height())
            
            canvas_h = max(1, self.canvas.winfo_height())
            scroll_h = max(1, self.scrollable_frame.winfo_height())
            
            # Posição desejada do topo para centralizar o item
            desired_top = max(0, item_y + (item_h / 2) - (canvas_h / 2))
            max_top = max(0, scroll_h - canvas_h)
            
            if max_top == 0:
                fraction = 0
            else:
                fraction = min(1, max(0, desired_top / max_top))
            
            self.canvas.yview_moveto(fraction)
        except Exception:
            pass

    # ===== Helpers de Drag & Drop para alvo preciso e indicador =====
    def _get_drop_index(self, event, from_index):
        """Calcula índice de destino com base no meio de cada item e posição do cursor."""
        try:
            # Encontrar canvas
            widget = event.widget
            while widget and not isinstance(widget, tk.Canvas):
                widget = widget.master
            if not widget or not isinstance(widget, tk.Canvas):
                return from_index
            canvas = widget
            canvas_y = canvas.canvasy(event.y)
            
            items = [w for w in self.item_widgets if w is not None]
            n = len(items)
            if n == 0:
                self._last_drop_raw_target = 0
                return 0
            
            # Antes do primeiro
            first_top = items[0].winfo_y()
            first_h = max(1, items[0].winfo_height())
            if canvas_y < first_top + first_h / 2:
                self._last_drop_raw_target = 0
                return 0
            
            # Entre itens
            for i in range(n - 1):
                top_i = items[i].winfo_y()
                h_i = max(1, items[i].winfo_height())
                mid_i = top_i + h_i / 2
                top_next = items[i+1].winfo_y()
                h_next = max(1, items[i+1].winfo_height())
                mid_next = top_next + h_next / 2
                if mid_i <= canvas_y < mid_next:
                    raw = i + 1
                    self._last_drop_raw_target = raw
                    return min(raw, n - 1)
            
            # Após o último
            self._last_drop_raw_target = n
            return n - 1
        except Exception:
            return from_index

    def _show_drop_indicator(self, target_index):
        """Desenha uma linha horizontal indicando a posição de inserção."""
        try:
            colors = self.theme_manager.get_colors()
            items = [w for w in self.item_widgets if w is not None]
            n = len(items)
            if n == 0:
                self._hide_drop_indicator()
                return
            
            raw = self._last_drop_raw_target if self._last_drop_raw_target is not None else target_index
            if raw <= 0:
                y = items[0].winfo_y()
            elif raw >= n:
                last = items[-1]
                y = last.winfo_y() + max(1, last.winfo_height())
            else:
                y = items[raw].winfo_y()
            
            if self.drop_indicator is None:
                self.drop_indicator = tk.Frame(self.scrollable_frame, bg=colors['progress_color'], height=2)
            
            self.root.update_idletasks()
            self.drop_indicator.place(x=0, y=max(0, int(y) - 1), relwidth=1, height=2)
        except Exception:
            self._hide_drop_indicator()

    def _hide_drop_indicator(self):
        """Remove o indicador visual, se existir."""
        try:
            if self.drop_indicator is not None:
                self.drop_indicator.place_forget()
        except Exception:
            pass
    
    def _create_item_controls(self, parent, index, bg_color):
        """Cria controles do item da lista"""
        colors = self.theme_manager.get_colors()
        
        controls_frame = tk.Frame(parent, bg=bg_color)
        controls_frame.grid(row=0, column=1, sticky='e', padx=(20, 0))
        
        # Layout em grid para melhor responsividade
        can_move_up = index > 0
        can_move_down = index < self.file_manager.total_files - 1
        
        # Container para as setas de reordenação
        arrows_frame = tk.Frame(controls_frame, bg=bg_color)
        arrows_frame.grid(row=0, column=0, padx=(0, 12))
        
        # Seta para cima
        up_btn = tk.Button(
            arrows_frame,
            text="▲",
            font=(DEFAULT_FONT_FAMILY, 12, 'bold'),
            fg=colors['progress_color'] if can_move_up else colors['text_secondary'],
            bg=bg_color,
            relief='flat',
            borderwidth=0,
            cursor='hand2' if can_move_up else 'arrow',
            padx=6,
            pady=2,
            command=lambda: self.file_manager.move_file_up(index) if can_move_up else None,
            state='normal' if can_move_up else 'disabled',
            disabledforeground=colors['text_secondary'],
            activebackground=bg_color,
            width=3
        )
        up_btn.pack(side='top', pady=(0, 1))
        
        # Seta para baixo
        down_btn = tk.Button(
            arrows_frame,
            text="▼",
            font=(DEFAULT_FONT_FAMILY, 12, 'bold'),
            fg=colors['progress_color'] if can_move_down else colors['text_secondary'],
            bg=bg_color,
            relief='flat',
            borderwidth=0,
            cursor='hand2' if can_move_down else 'arrow',
            padx=6,
            pady=2,
            command=lambda: self.file_manager.move_file_down(index) if can_move_down else None,
            state='normal' if can_move_down else 'disabled',
            disabledforeground=colors['text_secondary'],
            activebackground=bg_color,
            width=3
        )
        down_btn.pack(side='top')
        
        # Ícone de drag
        drag_icon = tk.Label(
            controls_frame,
            text="⋮⋮",
            font=(DEFAULT_FONT_FAMILY, 16, 'bold'),
            fg=colors['text_secondary'],
            bg=bg_color,
            cursor='hand2',
            padx=8
        )
        drag_icon.grid(row=0, column=1, padx=(8, 12))
        
        # Ativar drag somente pelo handle
        try:
            self.draggable_list.bind_drag_handle(drag_icon, index, lambda e, idx=index: self._on_item_clicked(idx))
        except Exception:
            pass
        
        # Botão remover
        remove_btn = tk.Button(
            controls_frame,
            text="✕",
            font=(DEFAULT_FONT_FAMILY, 18, 'bold'),
            fg=colors['error_color'],
            bg=bg_color,
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            padx=8,
            pady=6,
            activebackground=bg_color,
            activeforeground=colors['error_color'],
            command=lambda: self._remove_file(index),
            width=3
        )
        remove_btn.grid(row=0, column=2, padx=(0, 0))
    
    def _update_total_pages(self):
        """Atualiza contador de páginas totais"""
        total = self.file_manager.total_pages
        text = f"{total} página{'s' if total != 1 else ''}"
        self.total_pages_label.config(text=text)
    
    def _update_total_size(self):
        """Atualiza contador de tamanho total dos arquivos"""
        total_bytes = self.file_manager.total_size
        if total_bytes == 0:
            self.total_size_label.config(text="0 MB")
        else:
            # Formatar tamanho em MB com 1 decimal
            size_mb = total_bytes / (1024 * 1024)
            if size_mb < 0.1:
                size_kb = total_bytes / 1024
                text = f"{size_kb:.0f} KB"
            elif size_mb < 10:
                text = f"{size_mb:.1f} MB"
            else:
                text = f"{size_mb:.0f} MB"
            self.total_size_label.config(text=text)
    
    def _show_status(self, message, message_type='info'):
        """Mostra mensagem de status"""
        if self.status_label:
            self.status_label.show_message(message, message_type)
    
    # Action Methods
    def _add_files(self):
        """Adiciona arquivos via diálogo"""
        added_count = self.file_manager.add_files_dialog()
        if added_count > 0:
            self._show_status(f"{added_count} arquivo(s) adicionado(s)")
    
    def _clear_files(self):
        """Limpa lista de arquivos"""
        self.file_manager.clear_all()
        self._show_status("Lista limpa")
    
    def _remove_file(self, index):
        """Remove arquivo específico"""
        removed_pdf = self.file_manager.remove_file(index)
        if removed_pdf:
            self._show_status(f"Removido: {removed_pdf.name}")
    
    def _toggle_sort_order(self):
        """Alterna ordem de classificação"""
        self.file_manager.toggle_sort_order()
        
        # Atualizar texto do botão
        if self.file_manager.sort_order == "asc":
            self.sort_btn.config(text="A-Z")
        else:
            self.sort_btn.config(text="Z-A")
        
        order_text = 'A-Z' if self.file_manager.sort_order == 'asc' else 'Z-A'
        self._show_status(f"Ordenado: {order_text}")
    
    
    def _toggle_theme(self):
        """Alterna entre temas claro e escuro"""
        self.theme_manager.toggle_theme()
        self._refresh_ui()
    
    def _refresh_ui(self):
        """Atualiza toda a interface com novo tema"""
        # Limpar estado de drag se houver
        self.drag_drop_manager.cancel_current_drag()
        
        # Salvar estados das opções antes de recriar interface
        current_compression = None
        current_a4_standardize = None
        
        if hasattr(self, 'compression_var') and self.compression_var:
            current_compression = self.compression_var.get()
        if hasattr(self, 'standardize_a4_var') and self.standardize_a4_var:
            current_a4_standardize = self.standardize_a4_var.get()
        
        # Atualizar tema dos componentes
        colors = self.theme_manager.get_colors()
        self.root.configure(bg=colors['bg_primary'])
        # Remover configuração global que interfere com cores individuais
        
        # Atualizar texto do botão tema
        if self.theme_manager.is_dark_mode:
            self.theme_btn.config(text=UI_CONFIG['button_texts']['theme_dark'])
        else:
            self.theme_btn.config(text=UI_CONFIG['button_texts']['theme_light'])
        
        # Recriar interface completa
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self._create_interface()
        self._setup_drag_drop()
        
        # Restaurar estados das opções
        if current_compression and hasattr(self, 'compression_var') and self.compression_var:
            self.compression_var.set(current_compression)
        if current_a4_standardize is not None and hasattr(self, 'standardize_a4_var') and self.standardize_a4_var:
            self.standardize_a4_var.set(current_a4_standardize)
        
        # CRÍTICO: Restaurar lista de arquivos após trocar tema
        if not self.file_manager.is_empty():
            self._update_file_list()
            self._update_total_pages()
            self._update_total_size()
        
        # Manter seleção se houver
        selected_index = self.file_manager.selected_index
        if selected_index is not None and self.preview_manager:
            selected_pdf = self.file_manager.selected_pdf
            if selected_pdf:
                self.preview_manager.show_pdf_preview(selected_pdf)
    
    def _merge_pdfs(self):
        """Inicia processo de merge dos PDFs"""
        if not self.file_manager.has_enough_files_to_merge():
            messagebox.showwarning("Aviso", "Selecione pelo menos 2 arquivos PDF")
            return
        
        # Diálogo para salvar arquivo
        output_file = filedialog.asksaveasfilename(
            title="Salvar PDF combinado como...",
            defaultextension=".pdf",
            filetypes=[("Arquivos PDF", "*.pdf")]
        )
        
        if not output_file:
            return
        
        # Executar em thread separada
        thread = threading.Thread(
            target=self._merge_worker,
            args=(output_file,)
        )
        thread.start()
    
    def _merge_worker(self, output_file):
        """Worker thread para merge de PDFs"""
        try:
            # Mostrar progresso
            self.progress_frame.show("Iniciando merge...")
            
            # Obter lista de PDFs
            pdf_files = self.file_manager.pdf_files
            
            # Configuração fixa: sempre A4 obrigatório
            actual_compression = "none"  # Sem compressão adicional para preservar qualidade
            actual_a4 = True  # SEMPRE padronizar para A4
            
            print("📐 MODO ÚNICO: Juntar PDFs + Padronizar A4 obrigatório")
            print("✓ Todas as páginas serão padronizadas para formato A4 (595.276 x 841.890 pts)")
            
            # Executar merge com A4 obrigatório
            result = self.pdf_merger.merge_pdfs(
                pdf_files,
                output_file,
                actual_compression,
                actual_a4
            )
            
            # Esconder progresso
            self.progress_frame.hide()
            
            # Mostrar resultado na thread principal
            self.root.after(0, lambda: self._show_merge_success_dialog(result))
            
        except Exception as e:
            # Esconder progresso e mostrar erro na thread principal
            self.progress_frame.hide()
            # Usar root.after para mostrar messagebox na thread principal
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Erro ao processar PDFs: {str(e)}"))
            self._show_status("Erro no processamento", 'error')
    
    def _show_merge_success_dialog(self, result):
        """Mostra diálogo de sucesso do merge"""
        message = f"""✅ PDF criado com sucesso!

📁 Arquivo salvo em: {result['output_path']}
📊 Tamanho original: {format_file_size(result['original_size'])}
📊 Tamanho final: {format_file_size(result['final_size'])}
📄 Total de páginas: {result['total_pages']}
📋 Arquivos unidos: {result['files_merged']}

📐 FORMATO A4 APLICADO - Todas as páginas padronizadas (595.276 x 841.890 pts)
✅ Compatível com sistemas bancários, bandeiras de crédito e impressão profissional"""
        
        messagebox.showinfo("Sucesso", message)
        self._show_status("PDF criado com sucesso em formato A4!", 'success')
    
    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()
