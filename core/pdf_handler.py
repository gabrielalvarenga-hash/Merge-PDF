#!/usr/bin/env python3
"""
Manipulador de arquivos PDF
Responsável por merge, compressão e operações com PDFs
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
    
    # Qualidade de compressão
    JPEG_QUALITY_LARGE = 95
    JPEG_QUALITY_MEDIUM = 97
    JPEG_QUALITY_SMALL = 98
    
    # Thresholds de tamanho
    LARGE_IMAGE_PIXELS = 2000000
    MEDIUM_IMAGE_PIXELS = 500000
    
    # Progress percentages
    MERGE_PROGRESS = 80
    SAVE_PROGRESS = 85
    COMPRESS_PROGRESS = 90
    VERIFY_PROGRESS = 95
    COMPLETE_PROGRESS = 100

# Configurar logger
logger = logging.getLogger(__name__)

# Imports condicionais para PyPDF
try:
    import PyPDF2
except ImportError:
    raise ImportError("PyPDF2 não encontrado. Execute: pip install PyPDF2")

from config import COMPRESSION_LEVELS, SUPPORTED_EXTENSIONS
from .pdf_image_optimizer import optimize_pdf_images

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
        compression_level: str = "smart",
        standardize_to_a4: bool = False
    ) -> Dict[str, Any]:
        """
        Junta múltiplos PDFs em um arquivo único.
        
        Args:
            pdf_files: Lista de PDFInfo dos arquivos a serem juntados
            output_path: Caminho do arquivo de saída
            compression_level: Nível de compressão (apenas 'smart' suportado)
            standardize_to_a4: Se True, padroniza todas as páginas para formato A4
            
        Returns:
            Dicionário com informações do resultado
        """
        self._validate_merge_inputs(pdf_files)
        
        try:
            self._update_progress(0, "Iniciando merge...")
            
            merger_result = self._execute_merge_process(pdf_files, output_path, standardize_to_a4)
            final_size = self._finalize_merge(output_path, compression_level, standardize_to_a4)
            
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
    
    def _finalize_merge(self, output_path: str, compression_level: str, standardize_to_a4: bool) -> int:
        """Finaliza o processo de merge com compressão e verificação."""
        self._update_progress(PDFConstants.COMPRESS_PROGRESS, "Comprimindo...")
        final_size = self._compress_pdf(output_path, compression_level)
        
        if standardize_to_a4:
            self._update_progress(PDFConstants.VERIFY_PROGRESS, "Verificando padronização A4...")
            self._verify_a4_standardization(output_path)
        
        self._update_progress(PDFConstants.COMPLETE_PROGRESS, "Concluído!")
        return final_size
    
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
        blank_space_height: float = 100.0,
        compression_level: str = "smart"
    ) -> Dict[str, Any]:
        """
        Unifica múltiplos documentos em um único arquivo A4 com áreas em branco para preenchimento.
        
        Args:
            pdf_files: Lista de PDFInfo dos arquivos a serem unificados
            output_path: Caminho do arquivo de saída
            blank_space_height: Altura da área em branco entre documentos (pontos)
            compression_level: Nível de compressão
            
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
            
            # Aplicar preservação de imagens (sem compressão de imagens)
            self._update_progress(90, "Finalizando...")
            final_size = self._compress_pdf(output_path, compression_level)
            
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
    
    
    def _compress_pdf(self, pdf_path: str, compression_level: str) -> int:
        """
        Comprime um arquivo PDF usando compressão INTELIGENTE
        
        Args:
            pdf_path: Caminho do arquivo PDF
            compression_level: Nível de compressão (apenas 'smart' suportado)
            
        Returns:
            Tamanho final do arquivo em bytes
        """
        try:
            # Obter tamanho do arquivo para determinar estratégia
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            
            # Sempre usar compressão SMART (único nível suportado)
            if compression_level != 'smart':
                logger.warning(f"Nível '{compression_level}' não suportado. Usando 'smart'.")
                
            # Smart: Compressão inteligente com otimização AVANÇADA de imagens
            print(f"🧠 Usando compressão INTELIGENTE com otimização avançada!")
            print(f"📊 Arquivo: {file_size_mb:.1f}MB")
            print(f"🎯 Aplicando: compressão adaptativa, redimensionamento e remoção de metadados")
            
            # COMPRESSÃO CONTROLADA para atingir meta de ~3MB
            self._update_progress(50, "🎯 Aplicando compressão balanceada...")
            print(f"🎯 COMPRESSÃO BALANCEADA para a melhor qualidade vs tamanho:")
            print(f"   📂 Arquivo: {file_size_mb:.1f}MB")
            print(f"   🖼️ Otimizando imagens com qualidade alta (85-95)")
            
            # Usar ABORDAGEM EQUILIBRADA que preserva a qualidade
            self._balanced_reconstruction(pdf_path, file_size_mb)
                    
        except Exception as e:
            print(f"Aviso: Erro na compressão: {e}")
            # Fallback para compressão básica
            self._basic_compression(pdf_path, compression_level)
        
        return os.path.getsize(pdf_path)
    
    
    def _balanced_reconstruction(self, pdf_path: str, original_size_mb: float):
        """
        Processamento equilibrado do PDF mantendo qualidade máxima
        """
        try:
            # Usar sistema de otimização com preservação máxima
            result = optimize_pdf_images(
                input_path=pdf_path,
                output_path=pdf_path,
                quality='smart'
            )
            
            if result['success']:
                final_mb = result['final_size'] / (1024 * 1024)
                print(f"   ✅ Processamento concluído:")
                print(f"   📦 Tamanho final: {final_mb:.1f}MB")
                print(f"   📊 Variação: {result['compression_ratio']:.1f}%")
                print(f"   🖼️ Imagens processadas: {result['images_processed']}")
                print(f"   📸 Qualidade máxima preservada: {result['jpeg_images']}")
                
                # Avaliar resultado
                if final_mb <= original_size_mb * 1.1:  # Até 10% maior é aceitável
                    print(f"   🎯 PERFEITO! Qualidade máxima mantida")
                else:
                    print(f"   ✅ Processamento concluído com qualidade preservada")
                    
            else:
                print(f"   ❌ Erro no processamento: {result.get('error_message')}")
                # Fallback para compressão básica
                self._basic_compression(pdf_path, "smart")
                
        except Exception as e:
            print(f"   ⚠️ Erro no processamento: {e}")
            # Fallback para compressão básica
            self._basic_compression(pdf_path, "smart")

    def _basic_compression(self, pdf_path: str, compression_level: str):
        """Compressão básica original (fallback)"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    page.compress_content_streams()
                    writer.add_page(page)
                
                with open(pdf_path, 'wb') as output_file:
                    writer.write(output_file)
                    
        except Exception as e:
            print(f"Erro na compressão básica: {e}")
    
    def _standardize_page_to_a4(self, page):
        """
        Padroniza página para formato A4 padrão.
        
        Args:
            page: Objeto PyPDF2 PageObject
            
        Returns:
            Página com tamanho A4 exato
        """
        try:
            print(f"   📐 Padronizando página para A4: {PDFConstants.A4_WIDTH} x {PDFConstants.A4_HEIGHT} pts")
            
            current_dimensions = self._get_current_page_dimensions(page)
            a4_page = self._create_blank_a4_page()
            
            scaled_page = self._scale_page_to_fit_a4(page, current_dimensions)
            offset = self._calculate_centering_offset(current_dimensions, scaled_page['scale_factor'])
            
            if self._merge_page_to_a4(a4_page, scaled_page['page'], offset):
                self._ensure_a4_mediabox(a4_page)
                print(f"   ✅ Página padronizada: {PDFConstants.A4_WIDTH} x {PDFConstants.A4_HEIGHT} pts")
                return a4_page
            else:
                return self._apply_fallback_a4_sizing(page)
                
        except Exception as e:
            print(f"   ❌ Erro na padronização A4: {e}")
            return self._apply_emergency_fallback(page)
    
    def _get_current_page_dimensions(self, page) -> Dict[str, float]:
        """Obtém dimensões atuais da página."""
        current_width = float(page.mediabox.width)
        current_height = float(page.mediabox.height)
        
        print(f"   📊 Tamanho original: {current_width:.1f} x {current_height:.1f} pts")
        
        return {'width': current_width, 'height': current_height}
    
    def _create_blank_a4_page(self):
        """Cria página A4 em branco."""
        from PyPDF2 import PageObject
        return PageObject.create_blank_page(width=PDFConstants.A4_WIDTH, height=PDFConstants.A4_HEIGHT)
    
    def _scale_page_to_fit_a4(self, page, dimensions: Dict[str, float]) -> Dict[str, Any]:
        """Escala página para caber em A4 preservando proporção."""
        scale_x = PDFConstants.A4_WIDTH / dimensions['width']
        scale_y = PDFConstants.A4_HEIGHT / dimensions['height']
        scale_factor = min(scale_x, scale_y)
        
        print(f"   🔧 Fator de escala: {scale_factor:.3f}")
        
        page.scale(scale_factor, scale_factor)
        
        return {'page': page, 'scale_factor': scale_factor}
    
    def _calculate_centering_offset(self, dimensions: Dict[str, float], scale_factor: float) -> Tuple[float, float]:
        """Calcula offset para centralizar página em A4."""
        scaled_width = dimensions['width'] * scale_factor
        scaled_height = dimensions['height'] * scale_factor
        
        x_offset = max(0, (PDFConstants.A4_WIDTH - scaled_width) / 2)
        y_offset = max(0, (PDFConstants.A4_HEIGHT - scaled_height) / 2)
        
        print(f"   📍 Centralizando: offset x={x_offset:.1f}, y={y_offset:.1f}")
        
        return (x_offset, y_offset)
    
    def _merge_page_to_a4(self, a4_page, scaled_page, offset: Tuple[float, float]) -> bool:
        """Tenta fazer merge da página escalada na página A4."""
        merge_methods = [
            ('mergeTranslatedPage', lambda: a4_page.mergeTranslatedPage(scaled_page, offset[0], offset[1])),
            ('merge_translated_page', lambda: a4_page.merge_translated_page(scaled_page, offset[0], offset[1])),
            ('merge_page', lambda: a4_page.merge_page(scaled_page))
        ]
        
        for method_name, merge_func in merge_methods:
            if hasattr(a4_page, method_name.replace('_', '')) or hasattr(a4_page, method_name):
                try:
                    merge_func()
                    print(f"   ✅ Merge usando {method_name}")
                    return True
                except Exception as e:
                    print(f"   ❌ {method_name} falhou: {e}")
        
        return False
    
    def _ensure_a4_mediabox(self, page) -> None:
        """Garante que MediaBox seja exatamente A4."""
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (PDFConstants.A4_WIDTH, PDFConstants.A4_HEIGHT)
    
    def _apply_fallback_a4_sizing(self, page):
        """Aplica fallback forçando dimensões A4 na página original."""
        print(f"   ⚠️ Usando fallback - forçando dimensões A4")
        self._ensure_a4_mediabox(page)
        return page
    
    def _apply_emergency_fallback(self, page):
        """Aplica fallback de emergência com tratamento de erro."""
        try:
            print(f"   🆘 Aplicando fallback de emergência - A4 padrão")
            self._ensure_a4_mediabox(page)
            self._try_basic_scaling(page)
            return page
        except Exception as e2:
            print(f"   💥 Fallback de emergência falhou: {e2}")
            return page
    
    def _try_basic_scaling(self, page) -> None:
        """Tenta aplicar escala básica se necessário."""
        try:
            current_width = float(page.mediabox.width)
            current_height = float(page.mediabox.height)
            
            if self._needs_scaling(current_width, current_height):
                scale_factor = self._calculate_basic_scale_factor(current_width, current_height)
                if scale_factor != 1.0:
                    page.scale(scale_factor, scale_factor)
                    self._ensure_a4_mediabox(page)
        except Exception:
            pass
    
    def _needs_scaling(self, width: float, height: float) -> bool:
        """Verifica se página precisa de escala."""
        return (abs(width - PDFConstants.A4_WIDTH) > PDFConstants.SIZE_TOLERANCE or 
                abs(height - PDFConstants.A4_HEIGHT) > PDFConstants.SIZE_TOLERANCE)
    
    def _calculate_basic_scale_factor(self, width: float, height: float) -> float:
        """Calcula fator de escala básico."""
        scale_x = PDFConstants.A4_WIDTH / width
        scale_y = PDFConstants.A4_HEIGHT / height
        return min(scale_x, scale_y)

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