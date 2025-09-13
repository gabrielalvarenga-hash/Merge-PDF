#!/usr/bin/env python3
"""
Sistema de Drag & Drop para o PDF Merger
Gerencia tanto drag & drop interno (reordenação) quanto externo (arquivos)
"""

import tkinter as tk
import os
from typing import Optional, Callable, List, Dict, Any

from .themes import ThemeManager
from config import DRAG_ITEM_HEIGHT, DEFAULT_FONT_FAMILY

# Import condicional para tkinterdnd2
HAS_DND = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

class DragDropManager:
    """Gerenciador de drag & drop para a aplicação"""
    
    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager
        
        # Estado do drag interno
        self.drag_data = {"item": None, "y": 0, "started": False}
        self.drag_overlay: Optional[tk.Toplevel] = None
        self.drag_threshold = 1  # Pixels para começar drag visual (bem sensível)
        
        # Canvas e auto-scroll
        self.canvas: Optional[tk.Canvas] = None
        self.autoscroll_margin = 36
        self.autoscroll_step = 2
        
        # Overlay leve (desativado para performance)
        self.use_overlay = False
        
        # Callbacks auxiliares para lista arrastável
        self.get_drop_index = None  # function(event, from_index) -> int
        self.show_drop_indicator = None  # function(target_index) -> None
        self.hide_drop_indicator = None  # function() -> None
        
        # Callbacks
        self.on_files_dropped: Optional[Callable[[List[str]], None]] = None
        self.on_item_moved: Optional[Callable[[int, int], None]] = None
        self.on_item_clicked: Optional[Callable[[int], None]] = None
    
    def set_callbacks(
        self,
        on_files_dropped: Optional[Callable[[List[str]], None]] = None,
        on_item_moved: Optional[Callable[[int, int], None]] = None,
        on_item_clicked: Optional[Callable[[int], None]] = None
    ):
        """Define callbacks para eventos de drag & drop"""
        if on_files_dropped:
            self.on_files_dropped = on_files_dropped
        if on_item_moved:
            self.on_item_moved = on_item_moved
        if on_item_clicked:
            self.on_item_clicked = on_item_clicked
    
    def setup_external_drag_drop(self, *widgets):
        """
        Configura drag & drop de arquivos externos em widgets
        
        Args:
            *widgets: Widgets que aceitarão arquivos arrastados
        """
        if not HAS_DND:
            return False
        
        try:
            for widget in widgets:
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind('<<Drop>>', self._on_external_file_drop)
            
            return True
        except Exception as e:
            print(f"❌ Erro ao configurar drag & drop externo: {e}")
            return False
    
    def setup_internal_drag_drop(self, canvas: tk.Canvas):
        """
        Configura drag & drop interno para reordenação
        
        Args:
            canvas: Canvas que conterá os itens arrastáveis
        """
        self.canvas = canvas
        canvas.bind("<Button-1>", self._on_click)
        canvas.bind("<B1-Motion>", self._on_internal_drag)
        canvas.bind("<ButtonRelease-1>", self._on_internal_drop)

    def set_drop_helpers(self, get_drop_index=None, show_drop_indicator=None, hide_drop_indicator=None):
        """
        Define funções auxiliares para melhorar a UX do drag & drop interno.
        
        Args:
            get_drop_index: função que recebe (event, from_index) e retorna índice alvo
            show_drop_indicator: função que recebe (target_index) e desenha indicador
            hide_drop_indicator: função que remove indicador
        """
        if get_drop_index:
            self.get_drop_index = get_drop_index
        if show_drop_indicator:
            self.show_drop_indicator = show_drop_indicator
        if hide_drop_indicator:
            self.hide_drop_indicator = hide_drop_indicator
    
    def start_item_drag(self, event, item_index: int):
        """
        Inicia drag de um item da lista
        
        Args:
            event: Evento do mouse
            item_index: Índice do item sendo arrastado
        """
        # Limpar qualquer drag anterior
        self._clear_drag_state()
        
        # Iniciar novo drag
        self.drag_data["item"] = item_index
        self.drag_data["y"] = event.y_root
        self.drag_data["started"] = False
        
        # Notificar clique no item
        if self.on_item_clicked:
            self.on_item_clicked(item_index)
    
    def _on_click(self, event):
        """Handler para clique inicial"""
        # O clique é tratado pelos itens individuais
        pass
    
    def _on_internal_drag(self, event):
        """
        Handler para arrastar interno
        
        Args:
            event: Evento do mouse
        """
        if self.drag_data["item"] is not None:
            # Verificar se movimento é suficiente para iniciar drag visual
            if not self.drag_data["started"]:
                y_diff = abs(event.y_root - self.drag_data["y"])
                if y_diff >= self.drag_threshold:
                    self.drag_data["started"] = True
                    # Overlay desativado por padrão para leveza
                    self._create_drag_overlay(event)
            
            # Atualizar posição do overlay se já foi criado
            if self.drag_data["started"]:
                self._update_overlay_position(event)
                # Atualizar indicador de destino durante o arraste
                if self.get_drop_index and self.show_drop_indicator:
                    try:
                        target_index = self.get_drop_index(event, self.drag_data["item"])
                        self.show_drop_indicator(target_index)
                    except Exception:
                        pass
                # Auto-scroll ao aproximar das bordas
                self._autoscroll_if_needed(event)
    
    def _on_internal_drop(self, event):
        """
        Handler para soltar item interno
        
        Args:
            event: Evento do mouse
        """
        if self.drag_data["item"] is not None:
            try:
                # Encontrar o canvas pai se o widget atual não for um canvas
                widget = event.widget
                canvas = None
                
                # Subir na hierarquia até encontrar um Canvas
                while widget and not isinstance(widget, tk.Canvas):
                    widget = widget.master
                
                if widget and isinstance(widget, tk.Canvas):
                    canvas = widget
                    canvas_y = canvas.canvasy(event.y)
                    
                    # Índice de origem
                    old_index = self.drag_data["item"]
                    
                    # Calcular índice alvo com função auxiliar se disponível
                    if self.get_drop_index:
                        new_index = self.get_drop_index(event, old_index)
                    else:
                        new_index = int(canvas_y // DRAG_ITEM_HEIGHT)
                    
                    if old_index != new_index and self.on_item_moved:
                        self.on_item_moved(old_index, new_index)
                        
            except Exception as e:
                print(f"Erro no drop interno: {e}")
        
        # Remover indicador e limpar estado do drag
        try:
            if self.hide_drop_indicator:
                self.hide_drop_indicator()
        except Exception:
            pass
        self._clear_drag_state()
    
    def _on_external_file_drop(self, event):
        """
        Handler para arquivos arrastados externamente
        
        Args:
            event: Evento do drag & drop externo
        """
        try:
            # Obter lista de arquivos arrastados
            files = event.data.split()
            
            pdf_files = []
            for file_path in files:
                # Remover aspas se houver
                file_path = file_path.strip('{}').strip('"').strip("'")
                
                # Verificar se é PDF válido
                if self._is_valid_pdf_file(file_path):
                    pdf_files.append(file_path)
            
            # Notificar arquivos dropados
            if pdf_files and self.on_files_dropped:
                self.on_files_dropped(pdf_files)
                
        except Exception as e:
            print(f"Erro no drop externo: {e}")
    
    def _create_drag_overlay(self, event):
        """
        Cria overlay visual durante drag interno
        
        Args:
            event: Evento do mouse
        """
        if not self.use_overlay:
            return
        # Limpar overlay anterior se existir
        self._clear_overlay()
        
        try:
            root = event.widget.winfo_toplevel()
            colors = self.theme_manager.get_colors()
            
            # Criar overlay semi-transparente
            self.drag_overlay = tk.Toplevel(root)
            self.drag_overlay.wm_overrideredirect(True)
            self.drag_overlay.configure(bg=colors['bg_secondary'])
            self.drag_overlay.attributes('-alpha', 0.7)
            
            # Label com ícone de arquivo
            drag_label = tk.Label(
                self.drag_overlay,
                text="📄 Movendo...",
                font=(DEFAULT_FONT_FAMILY, 10, 'bold'),
                fg=colors['text_primary'],
                bg=colors['bg_secondary'],
                padx=8,
                pady=4
            )
            drag_label.pack()
            
            # Posicionar inicialmente
            self._update_overlay_position(event)
            
        except Exception as e:
            print(f"Erro ao criar overlay: {e}")
            self.drag_overlay = None
    
    def _update_overlay_position(self, event):
        """
        Atualiza posição do overlay
        
        Args:
            event: Evento do mouse
        """
        if self.drag_overlay and self.use_overlay:
            try:
                # Posicionar overlay próximo ao cursor
                x = event.x_root + 10
                y = event.y_root + 10
                
                self.drag_overlay.geometry(f"+{x}+{y}")
                self.drag_overlay.lift()  # Manter na frente
                
            except Exception:
                pass

    def _autoscroll_if_needed(self, event):
        """Rola o canvas automaticamente quando o cursor se aproxima do topo/rodapé."""
        try:
            if not self.canvas:
                return
            canvas_height = self.canvas.winfo_height()
            if canvas_height <= 1:
                return
            # y relativo ao canvas
            y_in_canvas = event.y_root - self.canvas.winfo_rooty()
            if y_in_canvas < self.autoscroll_margin:
                self.canvas.yview_scroll(-self.autoscroll_step, "units")
            elif y_in_canvas > canvas_height - self.autoscroll_margin:
                self.canvas.yview_scroll(self.autoscroll_step, "units")
        except Exception:
            pass
    
    def _clear_overlay(self):
        """Limpa overlay atual"""
        if self.drag_overlay:
            try:
                self.drag_overlay.destroy()
            except Exception:
                pass
            self.drag_overlay = None
    
    def _clear_drag_state(self):
        """Limpa estado do drag e remove overlay"""
        # Remover overlay visual
        self._clear_overlay()
        
        # Reset dados do drag
        self.drag_data = {"item": None, "y": 0, "started": False}
    
    def _is_valid_pdf_file(self, file_path: str) -> bool:
        """
        Verifica se um arquivo é PDF válido
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se for PDF válido
        """
        if not os.path.exists(file_path):
            return False
        
        return file_path.lower().endswith('.pdf')
    
    def cancel_current_drag(self):
        """Cancela drag atual se houver"""
        self._clear_drag_state()
    
    def is_dragging(self) -> bool:
        """Retorna True se está no meio de um drag"""
        return self.drag_data["item"] is not None
    
    @staticmethod
    def has_external_dnd_support() -> bool:
        """Retorna True se suporte a drag & drop externo está disponível"""
        return HAS_DND

class DraggableListManager:
    """Gerenciador especializado para listas arrastáveis"""
    
    def __init__(self, canvas: tk.Canvas, drag_drop_manager: DragDropManager):
        self.canvas = canvas
        self.drag_drop = drag_drop_manager
        self.items: List[Dict[str, Any]] = []
        
        # Configurar drag & drop no canvas
        self.drag_drop.setup_internal_drag_drop(canvas)
    
    def add_draggable_item(
        self, 
        widget: tk.Widget, 
        item_data: Dict[str, Any],
        on_select_callback: Optional[Callable] = None
    ):
        """
        Adiciona um item arrastável à lista
        
        Args:
            widget: Widget do item
            item_data: Dados associados ao item
            on_select_callback: Callback para seleção do item
        """
        index = len(self.items)
        
        # Armazenar item
        item_info = {
            'widget': widget,
            'data': item_data,
            'index': index
        }
        self.items.append(item_info)
        
        # Configurar apenas seleção no item inteiro (sem iniciar drag)
        widget.bind("<Button-1>", lambda e: self._on_item_select(e, index, on_select_callback))
        
        # Configurar seleção recursiva em filhos (sem drag)
        self._bind_select_events_recursive(widget, index, on_select_callback)
    
    def bind_drag_handle(
        self,
        handle_widget: tk.Widget,
        index: int,
        on_select_callback: Optional[Callable] = None
    ):
        """
        Vincula o início do drag apenas ao widget handle (ex.: ícone ⋮⋮).
        """
        handle_widget.bind("<Button-1>", lambda e: self._on_handle_click(e, index, on_select_callback))
        handle_widget.bind("<B1-Motion>", self.drag_drop._on_internal_drag)
        handle_widget.bind("<ButtonRelease-1>", self.drag_drop._on_internal_drop)
    
    def _bind_select_events_recursive(
        self, 
        widget: tk.Widget, 
        index: int,
        on_select_callback: Optional[Callable]
    ):
        """
        Configura eventos de seleção recursivamente em widgets filhos (não inicia drag)
        
        Args:
            widget: Widget pai
            index: Índice do item
            on_select_callback: Callback para seleção
        """
        try:
            for child in widget.winfo_children():
                # Sempre permitir seleção com clique simples
                child.bind("<Button-1>", lambda e: self._on_item_select(e, index, on_select_callback))
                # Recursão para filhos
                self._bind_select_events_recursive(child, index, on_select_callback)
        except Exception:
            pass
    
    def _on_item_select(self, event, index: int, callback: Optional[Callable]):
        """Seleciona o item sem iniciar drag."""
        if callback:
            callback(event, index)
    
    def _on_handle_click(self, event, index: int, callback: Optional[Callable]):
        """Inicia drag a partir do handle e também seleciona o item."""
        self.drag_drop.start_item_drag(event, index)
        if callback:
            callback(event, index)
    
    def clear_items(self):
        """Remove todos os itens da lista"""
        self.items.clear()
    
    def get_item_count(self) -> int:
        """Retorna número de itens na lista"""
        return len(self.items)
    
    def get_item_data(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Retorna dados de um item específico
        
        Args:
            index: Índice do item
            
        Returns:
            Dados do item ou None se índice inválido
        """
        if 0 <= index < len(self.items):
            return self.items[index]['data']
        return None
