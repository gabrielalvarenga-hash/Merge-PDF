#!/usr/bin/env python3
"""
Manipulador de arquivos PDF
Responsável por merge e operações com PDFs
"""

import os
import logging
from typing import List, Dict, Any, Optional, Callable, Tuple

# Constantes para processamento PDF
class PDFConstants:
    """Constantes para processamento de PDFs."""
    # Dimensões A4 em pontos
    A4_WIDTH = 595.276
    A4_HEIGHT = 841.890
    
    # Tolerâncias e limites
    SIZE_TOLERANCE = 1.0
    MIN_FILES_TO_MERGE = 2
    
    
    # Progress percentages
    MERGE_PROGRESS = 80
    SAVE_PROGRESS = 85
    VERIFY_PROGRESS = 95
    COMPLETE_PROGRESS = 100

# Configurar logger
logger = logging.getLogger(__name__)

# Imports condicionais para PyPDF
try:
    import PyPDF2
except ImportError:
    raise ImportError("PyPDF2 não encontrado. Execute: pip install PyPDF2")

from config import SUPPORTED_EXTENSIONS

class PDFInfo:
    """Classe para armazenar informações de um PDF"""
    
    def __init__(self, file_path: str):
        self.path = file_path
        self.name = os.path.basename(file_path)
        self.size = 0
        self.pages = 0
        self._load_info()
    
    def _load_info(self):
        """Carrega informações do arquivo PDF"""
        try:
            self.size = os.path.getsize(self.path)
            
            with open(self.path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                self.pages = len(reader.pages)
                
        except Exception as e:
            raise ValueError(f"Erro ao processar {self.path}: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'path': self.path,
            'name': self.name,
            'size': self.size,
            'pages': self.pages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFInfo':
        """Cria instância a partir de dicionário"""
        instance = cls.__new__(cls)
        instance.path = data['path']
        instance.name = data['name']
        instance.size = data['size'] 
        instance.pages = data['pages']
        return instance

class PDFMerger:
    """Classe responsável por juntar e comprimir PDFs"""
    
    def __init__(self):
        self.progress_callback: Optional[Callable[[float, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Define callback para atualização de progresso"""
        self.progress_callback = callback
    
    def _update_progress(self, value: float, message: str = ""):
        """Atualiza progresso se callback estiver definido"""
        if self.progress_callback:
            self.progress_callback(value, message)
    
    def merge_pdfs(
        self, 
        pdf_files: List[PDFInfo], 
        output_path: str,
        standardize_to_a4: bool = False
    ) -> Dict[str, Any]:
        """
        Junta múltiplos PDFs em um arquivo único.
        
        Args:
            pdf_files: Lista de PDFInfo dos arquivos a serem juntados
            output_path: Caminho do arquivo de saída
            standardize_to_a4: Se True, padroniza todas as páginas para formato A4
            
        Returns:
            Dicionário com informações do resultado
        """
        self._validate_merge_inputs(pdf_files)
        
        try:
            self._update_progress(0, "Iniciando merge...")
            
            merger_result = self._execute_merge_process(pdf_files, output_path, standardize_to_a4)
            final_size = self._finalize_merge(output_path, standardize_to_a4)
            
            return self._build_merge_result(
                pdf_files, output_path, merger_result['original_size'], 
                final_size, standardize_to_a4
            )
            
        except Exception as e:
            raise RuntimeError(f"Erro ao processar PDFs: {str(e)}")
    
    def _validate_merge_inputs(self, pdf_files: List[PDFInfo]) -> None:
        """Valida entradas para o processo de merge."""
        if len(pdf_files) < PDFConstants.MIN_FILES_TO_MERGE:
            raise ValueError("Selecione pelo menos 2 arquivos PDF")
    
    def _execute_merge_process(
        self, pdf_files: List[PDFInfo], output_path: str, standardize_to_a4: bool
    ) -> Dict[str, Any]:
        """Executa o processo principal de merge."""
        merger = PyPDF2.PdfMerger()
        original_size = sum(pdf.size for pdf in pdf_files)
        
        try:
            self._merge_files(merger, pdf_files, standardize_to_a4)
            self._save_merged_file(merger, output_path)
            return {'original_size': original_size}
        finally:
            merger.close()
    
    def _merge_files(self, merger: PyPDF2.PdfMerger, pdf_files: List[PDFInfo], standardize_to_a4: bool) -> None:
        """Merge individual dos arquivos PDF."""
        total_files = len(pdf_files)
        
        for i, pdf_info in enumerate(pdf_files):
            progress_message = self._get_processing_message(pdf_info.name, standardize_to_a4)
            progress_value = (i / total_files) * PDFConstants.MERGE_PROGRESS
            
            self._update_progress(progress_value, progress_message)
            self._process_single_file(merger, pdf_info, standardize_to_a4)
    
    def _get_processing_message(self, filename: str, standardize_to_a4: bool) -> str:
        """Gera mensagem de progresso para processamento de arquivo."""
        base_message = f"Processando: {filename}"
        return f"{base_message} (padronizando para A4)" if standardize_to_a4 else base_message
    
    def _process_single_file(self, merger: PyPDF2.PdfMerger, pdf_info: PDFInfo, standardize_to_a4: bool) -> None:
        """Processa um arquivo individual para o merge."""
        try:
            with open(pdf_info.path, 'rb') as file:
                if standardize_to_a4:
                    self._process_file_with_a4_standardization(merger, file, pdf_info.name)
                else:
                    print(f"   📄 Adicionando sem padronização: {pdf_info.name}")
                    merger.append(file)
        except Exception as e:
            raise ValueError(f"Erro ao processar {pdf_info.name}: {str(e)}")
    
    def _process_file_with_a4_standardization(self, merger: PyPDF2.PdfMerger, file, filename: str) -> None:
        """Processa arquivo com padronização A4."""
        print(f"   📐 Padronizando arquivo: {filename}")
        
        temp_writer = PyPDF2.PdfWriter()
        pdf_reader = PyPDF2.PdfReader(file)
        
        page_count = self._standardize_all_pages(temp_writer, pdf_reader)
        print(f"   ✅ {page_count} páginas padronizadas para A4 em {filename}")
        
        self._add_standardized_file_to_merger(merger, temp_writer)
    
    def _standardize_all_pages(self, writer: PyPDF2.PdfWriter, reader: PyPDF2.PdfReader) -> int:
        """Padroniza todas as páginas de um PDF para A4."""
        page_count = 0
        total_pages = len(reader.pages)
        
        for page_num, page in enumerate(reader.pages):
            print(f"   📄 Padronizando página {page_num + 1}/{total_pages}")
            standardized_page = self._standardize_page_to_a4(page)
            writer.add_page(standardized_page)
            page_count += 1
        
        return page_count
    
    def _add_standardized_file_to_merger(self, merger: PyPDF2.PdfMerger, writer: PyPDF2.PdfWriter) -> None:
        """Adiciona arquivo padronizado ao merger usando arquivo temporário."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            writer.write(temp_file)
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as temp_pdf:
                merger.append(temp_pdf)
        finally:
            self._cleanup_temp_file(temp_file_path)
    
    def _cleanup_temp_file(self, temp_file_path: str) -> None:
        """Remove arquivo temporário com tratamento de erro."""
        try:
            os.unlink(temp_file_path)
        except Exception:
            pass  # Ignora erros de limpeza
    
    def _save_merged_file(self, merger: PyPDF2.PdfMerger, output_path: str) -> None:
        """Salva o arquivo merged."""
        self._update_progress(PDFConstants.SAVE_PROGRESS, "Salvando arquivo...")
        
        with open(output_path, 'wb') as output_file:
            merger.write(output_file)
    
    def _finalize_merge(self, output_path: str, standardize_to_a4: bool) -> int:
        """Finaliza o processo de merge com verificação."""
        if standardize_to_a4:
            self._update_progress(PDFConstants.VERIFY_PROGRESS, "Verificando padronização A4...")
            self._verify_a4_standardization(output_path)
        
        self._update_progress(PDFConstants.COMPLETE_PROGRESS, "Concluído!")
        return os.path.getsize(output_path)
    
    def _build_merge_result(
        self, pdf_files: List[PDFInfo], output_path: str, 
        original_size: int, final_size: int, standardize_to_a4: bool
    ) -> Dict[str, Any]:
        """Constrói resultado final do merge."""
        compression_ratio = ((original_size - final_size) / original_size) * 100
        total_pages = sum(pdf.pages for pdf in pdf_files)
        
        return {
            'success': True,
            'output_path': output_path,
            'original_size': original_size,
            'final_size': final_size,
            'compression_ratio': compression_ratio,
            'total_pages': total_pages,
            'files_merged': len(pdf_files),
            'standardized_to_a4': standardize_to_a4
        }
    
    def unify_docs_to_a4_with_blank_space(
        self,
        pdf_files: List[PDFInfo],
        output_path: str,
        blank_space_height: float = 100.0
    ) -> Dict[str, Any]:
        """
        Unifica múltiplos documentos em um único arquivo A4 com áreas em branco para preenchimento.
        
        Args:
            pdf_files: Lista de PDFInfo dos arquivos a serem unificados
            output_path: Caminho do arquivo de saída
            blank_space_height: Altura da área em branco entre documentos (pontos)
            
        Returns:
            Dicionário com informações do resultado
        """
        if len(pdf_files) < 1:
            raise ValueError("Selecione pelo menos 1 arquivo PDF")
        
        try:
            self._update_progress(0, "Iniciando unificação em A4...")
            
            # Dimensões A4 em pontos
            A4_WIDTH = 595.276
            A4_HEIGHT = 841.890
            
            writer = PyPDF2.PdfWriter()
            total_files = len(pdf_files)
            original_size = sum(pdf.size for pdf in pdf_files)
            total_pages = 0
            
            # Processar cada arquivo
            for i, pdf_info in enumerate(pdf_files):
                try:
                    progress_message = f"Unificando: {pdf_info.name}"
                    self._update_progress(
                        (i / total_files) * 80, 
                        progress_message
                    )
                    
                    with open(pdf_info.path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        
                        # Processar cada página do documento
                        for page_num, page in enumerate(reader.pages):
                            # Padronizar para A4
                            a4_page = self._standardize_page_to_a4(page)
                            writer.add_page(a4_page)
                            total_pages += 1
                        
                        # Adicionar página em branco para preenchimento após cada documento
                        # (exceto após o último documento)
                        if i < total_files - 1:
                            blank_page = self._create_blank_a4_page_with_space(blank_space_height)
                            writer.add_page(blank_page)
                            total_pages += 1
                        
                except Exception as e:
                    raise ValueError(f"Erro ao processar {pdf_info.name}: {str(e)}")
            
            # Salvar arquivo unificado
            self._update_progress(85, "Salvando arquivo unificado...")
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            # Finalizar
            self._update_progress(90, "Finalizando...")
            final_size = os.path.getsize(output_path)
            
            self._update_progress(100, "Concluído!")
            
            # Calcular estatísticas
            compression_ratio = ((original_size - final_size) / original_size) * 100
            
            return {
                'success': True,
                'output_path': output_path,
                'original_size': original_size,
                'final_size': final_size,
                'compression_ratio': compression_ratio,
                'total_pages': total_pages,
                'files_unified': len(pdf_files),
                'standardized_to_a4': True,
                'blank_spaces_added': len(pdf_files) - 1 if len(pdf_files) > 1 else 0
            }
            
        except Exception as e:
            raise RuntimeError(f"Erro ao unificar documentos: {str(e)}")
    
    def _create_blank_a4_page_with_space(self, space_height: float):
        """
        Cria uma página A4 em branco para preenchimento.
        
        Args:
            space_height: Altura da área útil para preenchimento (não usado - área completa)
            
        Returns:
            Página A4 em branco para preenchimento
        """
        # Por enquanto, usar página simples - linhas podem ser implementadas depois se necessário
        from PyPDF2 import PageObject
        A4_WIDTH = 595.276
        A4_HEIGHT = 841.890
        
        # Criar página em branco A4
        blank_page = PageObject.create_blank_page(width=A4_WIDTH, height=A4_HEIGHT)
        
        return blank_page
    
    
    
    def _standardize_page_to_a4(self, page):
        """
        Força TODAS as páginas para o MESMO tamanho A4 exato.
        
        Args:
            page: Objeto PyPDF2 PageObject
            
        Returns:
            Página com tamanho A4 EXATO e IDÊNTICO para todas
        """
        try:
            print(f"   📐 FORÇANDO tamanho A4 EXATO: {PDFConstants.A4_WIDTH} x {PDFConstants.A4_HEIGHT} pts")
            
            # Obter dimensões atuais
            current_width = float(page.mediabox.width)
            current_height = float(page.mediabox.height)
            
            print(f"   📊 Tamanho original: {current_width:.1f} x {current_height:.1f} pts")
            
            # Calcular fator de escala para caber em A4 (mantendo proporções)
            scale_x = PDFConstants.A4_WIDTH / current_width
            scale_y = PDFConstants.A4_HEIGHT / current_height
            scale_factor = min(scale_x, scale_y)  # Usar menor fator para não cortar conteúdo
            
            print(f"   🔧 Fator de escala calculado: {scale_factor:.3f}")
            
            # SEMPRE aplicar escala para garantir que conteúdo caiba em A4
            if scale_factor != 1.0:
                if scale_factor < 1.0:
                    print(f"   📏 Reduzindo conteúdo para caber em A4 (escala: {scale_factor:.3f})")
                else:
                    print(f"   📏 Aumentando conteúdo para melhor aproveitamento A4 (escala: {scale_factor:.3f})")
                
                page.scale(scale_factor, scale_factor)
            else:
                print(f"   📏 Conteúdo já tem proporção perfeita para A4")
            
            # FORÇAR MediaBox e CropBox como A4 EXATO - TODAS AS PÁGINAS IDÊNTICAS
            page.mediabox.lower_left = (0, 0)
            page.mediabox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            
            # Garantir que CropBox também seja A4 exato (algumas páginas podem ter cropbox diferente)
            try:
                page.cropbox.lower_left = (0, 0)
                page.cropbox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            except:
                pass  # Nem todas as páginas têm cropbox
                
            # Forçar TrimBox e BleedBox também se existirem
            try:
                if hasattr(page, 'trimbox'):
                    page.trimbox.lower_left = (0, 0)
                    page.trimbox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            except:
                pass
                
            try:
                if hasattr(page, 'bleedbox'):
                    page.bleedbox.lower_left = (0, 0)
                    page.bleedbox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            except:
                pass
            
            print(f"   ✅ PÁGINA FORÇADA PARA A4 EXATO: {PDFConstants.A4_WIDTH} x {PDFConstants.A4_HEIGHT} pts")
            print(f"   🎯 TODAS AS PÁGINAS TERÃO TAMANHO IDÊNTICO!")
            return page
                
        except Exception as e:
            print(f"   ❌ Erro na padronização A4: {e}")
            return self._apply_emergency_fallback(page)
    
    
    def _ensure_a4_mediabox(self, page) -> None:
        """Garante que MediaBox seja exatamente A4."""
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
    
    def _apply_emergency_fallback(self, page):
        """Aplica fallback de emergência FORÇANDO A4 exato em todos os boxes."""
        try:
            print(f"   🆘 FALLBACK DE EMERGÊNCIA - FORÇANDO A4 EXATO!")
            
            # FORÇAR TODOS os boxes para A4 exato
            page.mediabox.lower_left = (0, 0)
            page.mediabox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            
            # Forçar CropBox
            try:
                page.cropbox.lower_left = (0, 0)
                page.cropbox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            except:
                pass
                
            # Forçar TrimBox
            try:
                if hasattr(page, 'trimbox'):
                    page.trimbox.lower_left = (0, 0)
                    page.trimbox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            except:
                pass
                
            # Forçar BleedBox  
            try:
                if hasattr(page, 'bleedbox'):
                    page.bleedbox.lower_left = (0, 0)
                    page.bleedbox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
            except:
                pass
            
            print(f"   ✅ FALLBACK COMPLETO - TODOS OS BOXES FORÇADOS PARA A4!")
            print(f"   📏 Tamanho final garantido: {PDFConstants.A4_WIDTH} x {PDFConstants.A4_HEIGHT} pts")
            return page
            
        except Exception as e2:
            print(f"   💥 Fallback de emergência falhou completamente: {e2}")
            print(f"   ⚠️ Retornando página original (pode não ter tamanho A4)")
            return page

    def _verify_a4_standardization(self, pdf_path: str) -> None:
        """
        Verifica se todas as páginas do PDF estão no formato A4 padrão.
        
        Args:
            pdf_path: Caminho do arquivo PDF para verificar
        """
        try:
            print(f"🔍 Verificando padronização A4 do arquivo final...")
            
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                verification_result = self._analyze_pages_dimensions(reader)
                self._report_verification_results(verification_result)
                    
        except Exception as e:
            self._handle_verification_error(e)
    
    def _analyze_pages_dimensions(self, reader: PyPDF2.PdfReader) -> Dict[str, Any]:
        """Analisa dimensões de todas as páginas."""
        total_pages = len(reader.pages)
        non_a4_pages = []
        
        for page_num, page in enumerate(reader.pages):
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            
            if not self._is_page_a4_compliant(width, height):
                non_a4_pages.append(self._create_page_info(page_num + 1, width, height))
                print(f"   ⚠️ Página {page_num + 1}: {width:.1f}x{height:.1f} pts (deveria ser {PDFConstants.A4_WIDTH}x{PDFConstants.A4_HEIGHT} pts)")
        
        return {'total_pages': total_pages, 'non_a4_pages': non_a4_pages}
    
    def _is_page_a4_compliant(self, width: float, height: float) -> bool:
        """Verifica se página está em conformidade com A4."""
        is_a4_width = abs(width - PDFConstants.A4_WIDTH) <= PDFConstants.SIZE_TOLERANCE
        is_a4_height = abs(height - PDFConstants.A4_HEIGHT) <= PDFConstants.SIZE_TOLERANCE
        return is_a4_width and is_a4_height
    
    def _create_page_info(self, page_num: int, width: float, height: float) -> Dict[str, Any]:
        """Cria informações de página não-A4."""
        return {
            'page': page_num,
            'width': width,
            'height': height,
            'expected_width': PDFConstants.A4_WIDTH,
            'expected_height': PDFConstants.A4_HEIGHT
        }
    
    def _report_verification_results(self, result: Dict[str, Any]) -> None:
        """Reporta resultados da verificação A4."""
        total_pages = result['total_pages']
        non_a4_pages = result['non_a4_pages']
        
        if non_a4_pages:
            print(f"   ❌ {len(non_a4_pages)} de {total_pages} páginas NÃO estão no formato A4 correto!")
            self._report_page_differences(non_a4_pages)
        else:
            print(f"   ✅ PERFEITO! Todas as {total_pages} páginas estão no formato A4 padrão ({PDFConstants.A4_WIDTH}x{PDFConstants.A4_HEIGHT} pts)")
    
    def _report_page_differences(self, non_a4_pages: List[Dict[str, Any]]) -> None:
        """Reporta diferenças específicas das páginas."""
        for page_info in non_a4_pages:
            diff_w = abs(page_info['width'] - page_info['expected_width'])
            diff_h = abs(page_info['height'] - page_info['expected_height'])
            print(f"      Página {page_info['page']}: diferença largura={diff_w:.1f}pts, altura={diff_h:.1f}pts")
    
    def _handle_verification_error(self, error: Exception) -> None:
        """Trata erros durante verificação."""
        print(f"   ⚠️ Erro na verificação A4: {error}")
        print(f"   ℹ️ Verificação manual pode ser necessária")

class PDFValidator:
    """Classe para validar arquivos PDF"""
    
    @staticmethod
    def is_valid_pdf(file_path: str) -> bool:
        """
        Verifica se um arquivo é um PDF válido
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            True se for PDF válido, False caso contrário
        """
        if not os.path.exists(file_path):
            return False
            
        if not file_path.lower().endswith(SUPPORTED_EXTENSIONS):
            return False
        
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                # Tentar acessar primeira página para validar
                if len(reader.pages) > 0:
                    return True
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_pdf_info(file_path: str) -> Optional[PDFInfo]:
        """
        Obtém informações de um PDF
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            PDFInfo se válido, None caso contrário
        """
        if not PDFValidator.is_valid_pdf(file_path):
            return None
        
        try:
            return PDFInfo(file_path)
        except Exception:
            return None

def format_file_size(size_bytes: int) -> str:
    """
    Formata tamanho em bytes para formato legível.
    
    Args:
        size_bytes: Tamanho em bytes
        
    Returns:
        String formatada (ex: "1.2 MB")
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    
    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    
    return f"{size:.1f} TB"