#!/usr/bin/env python3
"""
Configurações e constantes do PDF Merger App
"""

import os
import sys

# Configurações da aplicação
APP_NAME = "PDF Merger - Junte seus PDFs"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "1400x900"
MIN_WINDOW_SIZE = (1000, 700)

# Configurações de fonte
DEFAULT_FONT_FAMILY = 'Helvetica'
DEFAULT_FONT_SIZE = 13
BUTTON_FONT_SIZE = 14

# Configurações de preview
PREVIEW_SCALE = 1.3  # Escala otimizada para qualidade
PREVIEW_MAX_WIDTH = 700  # Largura máxima para ocupar toda área
DRAG_ITEM_HEIGHT = 60


# Configurações de layout
WIDGET_SPACING = 8   # Espaçamento reduzido

# Configurações de arquivos
SUPPORTED_EXTENSIONS = ('.pdf',)
LOGO_FILENAME = 'logo.png'

def get_script_dir():
    """Retorna o diretório onde está o script principal"""
    if getattr(sys, 'frozen', False):
        # Se for um executável compilado
        return os.path.dirname(sys.executable)
    else:
        # Se for um script Python normal
        return os.path.dirname(os.path.abspath(__file__))

def get_logo_path():
    """Retorna o caminho para o logo da aplicação"""
    return os.path.join(get_script_dir(), LOGO_FILENAME)

# Mensagens da aplicação
MESSAGES = {
    'empty_list': "📄 Nenhum PDF adicionado\n\nClique em 'Adicionar PDFs' para começar",
    'empty_list_with_dnd': "📄 Nenhum PDF adicionado\n\nClique em 'Adicionar PDFs' ou\narraste arquivos PDF para cá",
    'preview_placeholder': "📄 Selecione um PDF para ver o preview\n\nClique em um arquivo da lista\npara visualizar todas as páginas",
    'preview_unavailable': "📄 Preview não disponível\n\nInstale PyMuPDF para visualizar:\npip install PyMuPDF",
    'dnd_warning': "⚠️ tkinterdnd2 não encontrado. Drag & drop de arquivos desabilitado.\nPara habilitar: pip install tkinterdnd2",
    'dnd_install_tip': "Para habilitar: pip install tkinterdnd2",
    'pymupdf_warning': "PyMuPDF não encontrado. Preview desabilitado. Execute: pip install PyMuPDF",
    'pillow_warning': "Pillow e PyMuPDF não encontrados. Execute: pip install Pillow PyMuPDF",
    'pypdf_error': "PyPDF2 não encontrado. Execute: pip install PyPDF2"
}

# Configurações de UI
UI_CONFIG = {
    'drag_hint_text': "Use ▲▼ ou arraste ⋮⋮ para reordenar",
    'subtitle_text': "Setas ▲▼ e drag & drop para reordenar • Preview completo • Contador de páginas • Temas",
    'button_texts': {
        'add_files': "📁 Adicionar PDFs",
        'clear_list': "🗑️ Limpar",
        'sort_az': "🔄 Ordem A-Z", 
        'sort_za': "🔄 Ordem Z-A",
        'merge': "🚀 Juntar PDFs",
        'theme_light': "🌙 Modo Escuro",
        'theme_dark': "☀️ Modo Claro"
    }
}