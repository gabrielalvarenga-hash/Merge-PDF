#!/usr/bin/env python3
"""
Gerenciador de arquivos PDF
Responsável pela lista de arquivos, reordenação e operações de arquivo
"""

import os
from typing import List, Optional, Callable, Dict, Any
from tkinter import filedialog

from .pdf_handler import PDFInfo, PDFValidator
from config import SUPPORTED_EXTENSIONS

# Constantes para gerenciamento de arquivos
class FileManagerConstants:
    """Constantes para gerenciamento de arquivos PDF."""
    MIN_FILES_FOR_MERGE = 2
    
    # Ordens de classificação
    SORT_ORDER_ASC = "asc"
    SORT_ORDER_DESC = "desc"
    
    # Diálogos
    DIALOG_TITLE = "Selecione os arquivos PDF"
    PDF_FILETYPES = [("Arquivos PDF", "*.pdf"), ("Todos os arquivos", "*.*")]

class PDFFileManager:
    """Gerenciador da lista de arquivos PDF"""
    
    def __init__(self):
        self._pdf_files: List[PDFInfo] = []
        self._selected_index: Optional[int] = None
        self._sort_order = FileManagerConstants.SORT_ORDER_ASC
        
        # Callbacks
        self.on_files_changed: Optional[Callable[[], None]] = None
        self.on_selection_changed: Optional[Callable[[Optional[int]], None]] = None
    
    @property
    def pdf_files(self) -> List[PDFInfo]:
        """Retorna lista de arquivos PDF"""
        return self._pdf_files.copy()
    
    @property
    def selected_index(self) -> Optional[int]:
        """Retorna índice do arquivo selecionado"""
        return self._selected_index
    
    @property
    def selected_pdf(self) -> Optional[PDFInfo]:
        """Retorna PDF selecionado"""
        if self._selected_index is not None and 0 <= self._selected_index < len(self._pdf_files):
            return self._pdf_files[self._selected_index]
        return None
    
    @property
    def total_files(self) -> int:
        """Retorna número total de arquivos"""
        return len(self._pdf_files)
    
    @property
    def total_pages(self) -> int:
        """Retorna número total de páginas"""
        return sum(pdf.pages for pdf in self._pdf_files)
    
    @property
    def total_size(self) -> int:
        """Retorna tamanho total dos arquivos em bytes"""
        return sum(pdf.size for pdf in self._pdf_files)
    
    @property
    def sort_order(self) -> str:
        """Retorna ordem de classificação atual"""
        return self._sort_order
    
    def set_callbacks(
        self,
        on_files_changed: Optional[Callable[[], None]] = None,
        on_selection_changed: Optional[Callable[[Optional[int]], None]] = None
    ):
        """Define callbacks para eventos"""
        if on_files_changed:
            self.on_files_changed = on_files_changed
        if on_selection_changed:
            self.on_selection_changed = on_selection_changed
    
    def add_files_dialog(self) -> int:
        """
        Abre diálogo para selecionar arquivos PDF.
        
        Returns:
            Número de arquivos adicionados
        """
        files = filedialog.askopenfilenames(
            title=FileManagerConstants.DIALOG_TITLE,
            filetypes=FileManagerConstants.PDF_FILETYPES
        )
        
        return self.add_files(files)
    
    def add_files(self, file_paths: List[str]) -> int:
        """
        Adiciona arquivos à lista.
        
        Args:
            file_paths: Lista de caminhos de arquivos
            
        Returns:
            Número de arquivos adicionados com sucesso
        """
        was_empty = self.is_empty()
        added_count = self._process_file_additions(file_paths)
        
        if added_count > 0:
            self._notify_files_changed()
            
            if was_empty:
                self.set_selection(0)
        
        return added_count
    
    def _process_file_additions(self, file_paths: List[str]) -> int:
        """Processa adição de múltiplos arquivos."""
        added_count = 0
        
        for file_path in file_paths:
            if self.add_file(file_path):
                added_count += 1
        
        return added_count
    
    def add_file(self, file_path: str) -> bool:
        """
        Adiciona um arquivo individual.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se adicionado com sucesso, False caso contrário
        """
        if self._file_already_exists(file_path):
            return False
        
        pdf_info = PDFValidator.get_pdf_info(file_path)
        if pdf_info:
            self._pdf_files.append(pdf_info)
            return True
        
        return False
    
    def _file_already_exists(self, file_path: str) -> bool:
        """Verifica se arquivo já existe na lista."""
        return any(pdf.path == file_path for pdf in self._pdf_files)
    
    def remove_file(self, index: int) -> Optional[PDFInfo]:
        """
        Remove arquivo por índice
        
        Args:
            index: Índice do arquivo a ser removido
            
        Returns:
            PDFInfo removido ou None se índice inválido
        """
        if not self._is_valid_index(index):
            return None
        
        removed_pdf = self._pdf_files.pop(index)
        
        # Ajustar seleção
        if self._selected_index == index:
            self._set_selection(None)
        elif self._selected_index is not None and self._selected_index > index:
            self._selected_index -= 1
            self._notify_selection_changed()
        
        self._notify_files_changed()
        return removed_pdf
    
    def move_file_up(self, index: int) -> bool:
        """
        Move arquivo para cima na lista
        
        Args:
            index: Índice do arquivo
            
        Returns:
            True se movido com sucesso
        """
        if not self._is_valid_index(index) or index == 0:
            return False
        
        # Trocar com o item anterior
        self._pdf_files[index], self._pdf_files[index-1] = \
            self._pdf_files[index-1], self._pdf_files[index]
        
        # Atualizar seleção se necessário
        if self._selected_index == index:
            self._selected_index = index - 1
            self._notify_selection_changed()
        elif self._selected_index == index - 1:
            self._selected_index = index
            self._notify_selection_changed()
        
        self._notify_files_changed()
        return True
    
    def move_file_down(self, index: int) -> bool:
        """
        Move arquivo para baixo na lista
        
        Args:
            index: Índice do arquivo
            
        Returns:
            True se movido com sucesso
        """
        if not self._is_valid_index(index) or index >= len(self._pdf_files) - 1:
            return False
        
        # Trocar com o próximo item
        self._pdf_files[index], self._pdf_files[index+1] = \
            self._pdf_files[index+1], self._pdf_files[index]
        
        # Atualizar seleção se necessário
        if self._selected_index == index:
            self._selected_index = index + 1
            self._notify_selection_changed()
        elif self._selected_index == index + 1:
            self._selected_index = index
            self._notify_selection_changed()
        
        self._notify_files_changed()
        return True
    
    def move_file_to_position(self, from_index: int, to_index: int) -> bool:
        """
        Move arquivo para posição específica
        
        Args:
            from_index: Índice de origem
            to_index: Índice de destino
            
        Returns:
            True se movido com sucesso
        """
        if not self._is_valid_index(from_index) or not self._is_valid_index(to_index):
            return False
        
        if from_index == to_index:
            return True
        
        # Mover item
        pdf_info = self._pdf_files.pop(from_index)
        self._pdf_files.insert(to_index, pdf_info)
        
        # Ajustar seleção se necessário
        if self._selected_index == from_index:
            self._selected_index = to_index
            self._notify_selection_changed()
        
        self._notify_files_changed()
        return True
    
    def set_selection(self, index: Optional[int]):
        """
        Define arquivo selecionado
        
        Args:
            index: Índice do arquivo ou None para limpar seleção
        """
        if index is not None and not self._is_valid_index(index):
            return
        
        self._set_selection(index)
    
    def clear_all(self):
        """Remove todos os arquivos da lista"""
        self._pdf_files.clear()
        self._set_selection(None)
        self._notify_files_changed()
    
    def toggle_sort_order(self) -> None:
        """Alterna entre ordem ascendente e descendente."""
        self._sort_order = self._get_opposite_sort_order()
        self._apply_current_sort_order()
        self._adjust_selection_after_sort()
        self._notify_files_changed()
    
    def _get_opposite_sort_order(self) -> str:
        """Retorna ordem oposta à atual."""
        return (FileManagerConstants.SORT_ORDER_DESC 
                if self._sort_order == FileManagerConstants.SORT_ORDER_ASC 
                else FileManagerConstants.SORT_ORDER_ASC)
    
    def _apply_current_sort_order(self) -> None:
        """Aplica ordem de classificação atual."""
        reverse_order = self._sort_order == FileManagerConstants.SORT_ORDER_DESC
        self._pdf_files.sort(key=lambda x: x.name.lower(), reverse=reverse_order)
    
    def is_empty(self) -> bool:
        """Verifica se a lista está vazia"""
        return len(self._pdf_files) == 0
    
    def has_enough_files_to_merge(self) -> bool:
        """Verifica se há arquivos suficientes para merge."""
        return len(self._pdf_files) >= FileManagerConstants.MIN_FILES_FOR_MERGE
    
    def get_file_info_summary(self, index: int) -> Optional[str]:
        """
        Retorna informações resumidas de um arquivo.
        
        Args:
            index: Índice do arquivo
            
        Returns:
            String com informações do arquivo
        """
        if not self._is_valid_index(index):
            return None
        
        pdf = self._pdf_files[index]
        return self._format_file_summary(pdf)
    
    def _format_file_summary(self, pdf: PDFInfo) -> str:
        """Formata resumo de informações do arquivo."""
        from .pdf_handler import format_file_size
        
        size_text = format_file_size(pdf.size)
        page_text = self._format_page_count(pdf.pages)
        
        return f"{size_text} • {page_text}"
    
    def _format_page_count(self, pages: int) -> str:
        """Formata contador de páginas."""
        return f"{pages} página{'s' if pages != 1 else ''}"
    
    def _is_valid_index(self, index: int) -> bool:
        """Verifica se índice é válido"""
        return 0 <= index < len(self._pdf_files)
    
    def _set_selection(self, index: Optional[int]):
        """Define seleção interna"""
        if self._selected_index != index:
            self._selected_index = index
            self._notify_selection_changed()
    
    def _adjust_selection_after_sort(self) -> None:
        """Ajusta seleção após ordenação."""
        if not self._has_valid_selection():
            return
        
        selected_path = self._get_selected_file_path()
        new_index = self._find_file_index_by_path(selected_path)
        
        if new_index is not None:
            self._selected_index = new_index
            self._notify_selection_changed()
    
    def _has_valid_selection(self) -> bool:
        """Verifica se há seleção válida."""
        return (self._selected_index is not None and 
                self._selected_index < len(self._pdf_files))
    
    def _get_selected_file_path(self) -> str:
        """Obtém caminho do arquivo selecionado."""
        return self._pdf_files[self._selected_index].path
    
    def _find_file_index_by_path(self, file_path: str) -> Optional[int]:
        """Encontra índice do arquivo pelo caminho."""
        for i, pdf_info in enumerate(self._pdf_files):
            if pdf_info.path == file_path:
                return i
        return None
    
    def _notify_files_changed(self):
        """Notifica mudança na lista de arquivos"""
        if self.on_files_changed:
            self.on_files_changed()
    
    def _notify_selection_changed(self):
        """Notifica mudança na seleção"""
        if self.on_selection_changed:
            self.on_selection_changed(self._selected_index)
