import sys
import tkinter as tk
from tkinter import messagebox
from typing import Tuple, List

# Constantes para dependências
REQUIRED_DEPENDENCIES = [
    ('PyPDF2', 'PyPDF2 ou PyPDF4 não encontrado.\nExecute: pip install PyPDF2'),
    ('PyCryptodome', 'PyCryptodome não encontrado. Necessário para PDFs criptografados.\nExecute: pip install PyCryptodome')
]

OPTIONAL_DEPENDENCIES = [
    ('tkinterdnd2', 'tkinterdnd2 não encontrado. Drag & drop desabilitado.\nPara habilitar: pip install tkinterdnd2'),
    ('PIL', 'Pillow não encontrado. Ícones desabilitados.\nPara habilitar: pip install Pillow'),
    ('fitz', 'PyMuPDF não encontrado. Preview desabilitado.\nPara habilitar: pip install PyMuPDF')
]

def _check_pypdf_availability() -> bool:
    """Verifica se PyPDF2 ou PyPDF4 está disponível."""
    try:
        import PyPDF2
        return True
    except ImportError:
        try:
            import PyPDF4 as PyPDF2
            return True
        except ImportError:
            return False

def _check_dependency(module_name: str) -> bool:
    """Verifica se um módulo específico está disponível."""
    try:
        if module_name == 'PyPDF2':
            return _check_pypdf_availability()
        elif module_name == 'PIL':
            from PIL import Image, ImageTk
            return True
        elif module_name == 'PyCryptodome':
            import Crypto
            return True
        else:
            __import__(module_name)
            return True
    except ImportError:
        return False

def check_dependencies() -> Tuple[List[str], List[str]]:
    """Verifica se as dependências necessárias estão instaladas.
    
    Returns:
        Tuple contendo listas de dependências ausentes e avisos
    """
    missing_deps = []
    warnings = []
    
    # Verificar dependências obrigatórias
    for module, error_msg in REQUIRED_DEPENDENCIES:
        if not _check_dependency(module):
            missing_deps.append(error_msg)
    
    # Verificar dependências opcionais
    for module, warning_msg in OPTIONAL_DEPENDENCIES:
        if not _check_dependency(module):
            warnings.append(warning_msg)
    
    return missing_deps, warnings

def _show_missing_dependencies_error(missing_deps: List[str]) -> None:
    """Exibe erro para dependências obrigatórias ausentes."""
    error_msg = "❌ Dependências obrigatórias não encontradas:\n\n" + "\n\n".join(missing_deps)
    messagebox.showerror("Dependências não encontradas", error_msg)

def _show_optional_dependencies_warning(warnings: List[str]) -> None:
    """Exibe aviso para dependências opcionais ausentes."""
    warning_msg = "⚠️ Algumas funcionalidades estarão desabilitadas:\n\n" + "\n\n".join(warnings)
    warning_msg += "\n\n✅ A aplicação funcionará, mas com funcionalidades limitadas."
    print(warning_msg)

def show_dependency_info(missing_deps: List[str], warnings: List[str]) -> bool:
    """Mostra informações sobre dependências e retorna se pode continuar.
    
    Args:
        missing_deps: Lista de dependências obrigatórias ausentes
        warnings: Lista de avisos sobre dependências opcionais
        
    Returns:
        True se a aplicação pode continuar, False caso contrário
    """
    if missing_deps:
        _show_missing_dependencies_error(missing_deps)
        return False
    
    if warnings:
        _show_optional_dependencies_warning(warnings)
    
    return True

def create_root_window() -> tk.Tk:
    """Cria janela root com suporte a drag & drop se disponível.
    
    Returns:
        Instância de Tk com ou sem suporte a drag & drop
    """
    try:
        from tkinterdnd2 import TkinterDnD
        return TkinterDnD.Tk()
    except ImportError:
        return tk.Tk()

def _print_startup_message() -> None:
    """Imprime mensagem de inicialização."""
    print("🚀 Iniciando PDF Merger App...")

def _print_feature_status() -> None:
    """Imprime status dos recursos disponíveis."""
    print("✅ Aplicação iniciada com sucesso!")
    print("📋 Recursos disponíveis:")
    print("   • Merge e compressão de PDFs ✅")
    
    features = {
        'tkinterdnd2': 'Drag & drop de arquivos',
        'PIL': 'Ícones e logos',
        'fitz': 'Preview de PDFs'
    }
    
    for module, feature in features.items():
        status = "✅" if module in sys.modules else "❌"
        print(f"   • {feature} {status}")

def _handle_import_error(error: ImportError) -> None:
    """Trata erros de importação de módulos."""
    error_msg = (
        f"❌ Erro ao importar módulos da aplicação:\n{str(error)}\n\n"
        "Verifique se todos os arquivos estão presentes."
    )
    messagebox.showerror("Erro de importação", error_msg)
    print(error_msg)
    sys.exit(1)

def _handle_unexpected_error(error: Exception) -> None:
    """Trata erros inesperados durante inicialização."""
    error_msg = f"❌ Erro inesperado ao inicializar aplicação:\n{str(error)}"
    messagebox.showerror("Erro", error_msg)
    print(error_msg)
    sys.exit(1)

def _initialize_application() -> None:
    """Inicializa a aplicação principal."""
    print("🪟 Criando janela principal...")
    root = create_root_window()
    
    from main_window import PDFMergerMainWindow
    
    print("⚙️ Inicializando interface...")
    app = PDFMergerMainWindow(root)
    
    _print_feature_status()
    app.run()

def main() -> None:
    """Função principal da aplicação."""
    _print_startup_message()
    
    missing_deps, warnings = check_dependencies()
    
    if not show_dependency_info(missing_deps, warnings):
        print("❌ Encerrando devido a dependências faltando.")
        sys.exit(1)
    
    try:
        _initialize_application()
    except ImportError as e:
        _handle_import_error(e)
    except Exception as e:
        _handle_unexpected_error(e)

if __name__ == "__main__":
    main()
