#!/usr/bin/env python3
"""
Componentes UI reutilizáveis para o PDF Merger App
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, Any

from .themes import ThemeManager
from config import DEFAULT_FONT_FAMILY, BUTTON_FONT_SIZE

class ModernButton(tk.Button):
    """Botão customizado com estilo moderno e efeitos hover"""
    
    def __init__(self, parent, theme_manager: ThemeManager, button_type: str = 'primary', **kwargs):
        self.theme_manager = theme_manager
        self.button_type = button_type
        
        # Obter cores do tema
        button_colors = self.theme_manager.get_button_colors(button_type)
        self.original_bg = button_colors['bg']
        self.original_fg = button_colors['fg']
        self.hover_bg = button_colors['hover_bg']
        
        # Configurações padrão
        default_config = {
            'bg': self.original_bg,
            'fg': self.original_fg,
            'relief': 'flat',
            'borderwidth': 0,
            'highlightthickness': 0,
            'font': (DEFAULT_FONT_FAMILY, BUTTON_FONT_SIZE),
            'cursor': 'hand2',
            'activebackground': self.original_bg,
            'activeforeground': self.original_fg
        }
        
        # Mesclar com kwargs fornecidos
        final_config = {**default_config, **kwargs}
        
        super().__init__(parent, **final_config)
        
        # Configurar eventos hover
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
    
    def _on_enter(self, event):
        """Efeito hover - mouse entra"""
        self.config(bg=self.hover_bg)
    
    def _on_leave(self, event):
        """Efeito hover - mouse sai"""
        self.config(bg=self.original_bg)
    
    def update_theme(self, theme_manager: ThemeManager):
        """Atualiza as cores baseado no tema atual"""
        self.theme_manager = theme_manager
        button_colors = self.theme_manager.get_button_colors(self.button_type)
        
        self.original_bg = button_colors['bg']
        self.original_fg = button_colors['fg'] 
        self.hover_bg = button_colors['hover_bg']
        
        self.config(
            bg=self.original_bg,
            fg=self.original_fg,
            activebackground=self.original_bg,
            activeforeground=self.original_fg
        )

class ScrollableFrame(tk.Frame):
    """Frame com scroll personalizado"""
    
    def __init__(self, parent, theme_manager: ThemeManager, **kwargs):
        self.theme_manager = theme_manager
        colors = theme_manager.get_colors()
        
        super().__init__(parent, bg=colors['bg_primary'], **kwargs)
        
        # Configurar grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Canvas para scroll
        self.canvas = tk.Canvas(
            self, 
            bg=colors['bg_primary'], 
            highlightthickness=0
        )
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self, 
            orient='vertical', 
            command=self.canvas.yview
        )
        
        # Frame scrollável
        self.scrollable_frame = tk.Frame(self.canvas, bg=colors['bg_primary'])
        
        # Configurar scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Criar janela no canvas
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Posicionar elementos
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Configurar eventos de scroll
        self._bind_scroll_events()
    
    def _bind_scroll_events(self):
        """Configura eventos de scroll com mouse wheel"""
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<Button-4>", self._on_mousewheel)
        self.scrollable_frame.bind("<Button-5>", self._on_mousewheel)
        
        # Focus para receber eventos
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())
        self.scrollable_frame.bind("<Enter>", lambda e: self.scrollable_frame.focus_set())
    
    def _on_mousewheel(self, event):
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
    
    def update_theme(self, theme_manager: ThemeManager):
        """Atualiza tema do componente"""
        self.theme_manager = theme_manager
        colors = theme_manager.get_colors()
        
        self.config(bg=colors['bg_primary'])
        self.canvas.config(bg=colors['bg_primary'])
        self.scrollable_frame.config(bg=colors['bg_primary'])

class StatusLabel(tk.Label):
    """Label para exibição de status com auto-hide"""
    
    def __init__(self, parent, theme_manager: ThemeManager, **kwargs):
        self.theme_manager = theme_manager
        colors = theme_manager.get_colors()
        
        default_config = {
            'bg': colors['bg_primary'],
            'fg': colors['text_primary'],
            'font': (DEFAULT_FONT_FAMILY, 11),
            'text': ''
        }
        
        final_config = {**default_config, **kwargs}
        super().__init__(parent, **final_config)
        
        self.auto_hide_id = None
    
    def show_message(self, message: str, message_type: str = 'info', auto_hide: bool = True):
        """Mostra uma mensagem com tipo específico"""
        colors = self.theme_manager.get_colors()
        
        # Definir cor baseada no tipo
        color_map = {
            'info': colors['text_primary'],
            'success': colors['success_color'],
            'error': colors['error_color'],
            'warning': colors['warning_color']
        }
        
        self.config(
            text=message,
            fg=color_map.get(message_type, colors['text_primary'])
        )
        
        # Auto-hide após 5 segundos se solicitado
        if auto_hide:
            if self.auto_hide_id:
                self.after_cancel(self.auto_hide_id)
            self.auto_hide_id = self.after(5000, self.hide)
    
    def hide(self):
        """Esconde o label"""
        self.config(text='')  # Limpar texto ao invés de esconder widget
        if self.auto_hide_id:
            self.after_cancel(self.auto_hide_id)
            self.auto_hide_id = None
    
    def update_theme(self, theme_manager: ThemeManager):
        """Atualiza tema do componente"""
        self.theme_manager = theme_manager
        colors = theme_manager.get_colors()
        self.config(bg=colors['bg_primary'])

class ProgressFrame(tk.Frame):
    """Frame com barra de progresso e label de status"""
    
    def __init__(self, parent, theme_manager: ThemeManager, **kwargs):
        self.theme_manager = theme_manager
        colors = theme_manager.get_colors()
        
        super().__init__(parent, bg=colors['bg_primary'], **kwargs)
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self,
            variable=self.progress_var,
            maximum=100,
            length=300,
            mode='determinate'
        )
        
        # Label de status
        self.status_label = StatusLabel(self, theme_manager)
        
        self.is_visible = False
    
    def show(self, message: str = ""):
        """Mostra barra de progresso"""
        if not self.is_visible:
            self.progress_bar.pack(pady=10)
            if message:
                self.status_label.show_message(message, auto_hide=False)
            self.is_visible = True
    
    def hide(self):
        """Esconde barra de progresso"""
        if self.is_visible:
            self.progress_bar.pack_forget()
            self.status_label.hide()
            self.progress_var.set(0)
            self.is_visible = False
    
    def update_progress(self, value: float, message: str = ""):
        """Atualiza progresso"""
        self.progress_var.set(value)
        if message:
            self.status_label.show_message(message, auto_hide=False)
        
        # Forçar atualização da UI
        self.update_idletasks()
    
    def update_theme(self, theme_manager: ThemeManager):
        """Atualiza tema do componente"""
        self.theme_manager = theme_manager
        colors = theme_manager.get_colors()
        self.config(bg=colors['bg_primary'])
        self.status_label.update_theme(theme_manager)

class FileListItem(tk.Frame):
    """Item individual da lista de arquivos"""
    
    def __init__(
        self, 
        parent, 
        theme_manager: ThemeManager, 
        index: int,
        filename: str,
        file_info: str,
        is_selected: bool = False,
        on_click: Optional[Callable] = None,
        on_remove: Optional[Callable] = None,
        on_move_up: Optional[Callable] = None,
        on_move_down: Optional[Callable] = None,
        can_move_up: bool = True,
        can_move_down: bool = True,
        **kwargs
    ):
        self.theme_manager = theme_manager
        self.index = index
        self.on_click = on_click
        self.on_remove = on_remove
        self.on_move_up = on_move_up
        self.on_move_down = on_move_down
        
        colors = theme_manager.get_colors()
        bg_color = colors['selected'] if is_selected else colors['bg_primary']
        
        super().__init__(
            parent,
            bg=bg_color,
            relief='solid',
            borderwidth=1,
            cursor='hand2',
            **kwargs
        )
        
        self.pack(fill='x', padx=5, pady=3)
        
        # Container interno (padding reduzido para economizar espaço)
        inner_frame = tk.Frame(self, bg=bg_color)
        inner_frame.pack(fill='x', padx=15, pady=12)
        
        # Área de informações
        info_frame = tk.Frame(inner_frame, bg=bg_color)
        info_frame.pack(side='left', fill='x', expand=True)
        
        # Nome do arquivo
        name_label = tk.Label(
            info_frame,
            text=f"📄 {filename}",
            font=(DEFAULT_FONT_FAMILY, 14, 'bold'),
            fg=colors['text_primary'],
            bg=bg_color,
            anchor='w'
        )
        name_label.pack(anchor='w')
        
        # Informações do arquivo
        info_label = tk.Label(
            info_frame,
            text=file_info,
            font=(DEFAULT_FONT_FAMILY, 12),
            fg=colors['text_secondary'],
            bg=bg_color,
            anchor='w'
        )
        info_label.pack(anchor='w')
        
        # Controles
        self._create_controls(inner_frame, bg_color, can_move_up, can_move_down)
        
        # Configurar eventos
        self._bind_events([self, inner_frame, info_frame, name_label, info_label])
    
    def _create_controls(self, parent, bg_color, can_move_up, can_move_down):
        """Cria controles do item"""
        colors = self.theme_manager.get_colors()
        
        controls_frame = tk.Frame(parent, bg=bg_color)
        controls_frame.pack(side='right')
        
        # Setas de reordenação
        arrows_frame = tk.Frame(controls_frame, bg=bg_color)
        arrows_frame.pack(side='right', padx=(0, 10))
        
        # Seta para cima
        up_btn = tk.Button(
            arrows_frame,
            text="▲",
            font=(DEFAULT_FONT_FAMILY, 10, 'bold'),
            fg=colors['progress_color'],
            bg=bg_color,
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            padx=6,
            pady=1,
            command=lambda: self.on_move_up(self.index) if self.on_move_up else None,
            state='normal' if can_move_up else 'disabled'
        )
        up_btn.pack(pady=(0, 2))
        
        # Seta para baixo
        down_btn = tk.Button(
            arrows_frame,
            text="▼",
            font=(DEFAULT_FONT_FAMILY, 10, 'bold'),
            fg=colors['progress_color'],
            bg=bg_color,
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            padx=6,
            pady=1,
            command=lambda: self.on_move_down(self.index) if self.on_move_down else None,
            state='normal' if can_move_down else 'disabled'
        )
        down_btn.pack()
        
        # Ícone de drag
        drag_icon = tk.Label(
            controls_frame,
            text="⋮⋮",
            font=(DEFAULT_FONT_FAMILY, 14, 'bold'),
            fg=colors['text_secondary'],
            bg=bg_color,
            cursor='hand2'
        )
        drag_icon.pack(side='right', padx=(10, 5))
        
        # Botão remover
        remove_btn = tk.Button(
            controls_frame,
            text="✕",
            font=(DEFAULT_FONT_FAMILY, 14, 'bold'),
            fg=colors['error_color'],
            bg=bg_color,
            relief='flat',
            borderwidth=0,
            cursor='hand2',
            padx=8,
            pady=2,
            command=lambda: self.on_remove(self.index) if self.on_remove else None
        )
        remove_btn.pack(side='right')
        
        # Adicionar aos elementos com eventos
        self._bind_events([controls_frame, arrows_frame, drag_icon])
    
    def _bind_events(self, widgets):
        """Configura eventos para widgets"""
        for widget in widgets:
            widget.bind("<Button-1>", lambda e: self.on_click(e, self.index) if self.on_click else None)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<ButtonRelease-1>", self._on_drop)
    
    def _on_drag(self, event):
        """Placeholder para drag - será implementado pela aplicação principal"""
        pass
    
    def _on_drop(self, event):
        """Placeholder para drop - será implementado pela aplicação principal"""
        pass
