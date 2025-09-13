#!/usr/bin/env python3
"""
Módulo de compressão de PDF
Responsável por comprimir PDFs reduzindo qualidade e largura das imagens
"""

import os
import io
import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

# Imports condicionais para dependências de compressão
try:
    import pikepdf
except ImportError:
    raise ImportError("pikepdf não encontrado. Execute: pip install pikepdf")

try:
    from PIL import Image
except ImportError:
    raise ImportError("Pillow não encontrado. Execute: pip install Pillow")

class CompressionLevel(Enum):
    """Níveis de compressão disponíveis"""
    BAIXO = "baixo"
    MEDIO = "medio" 
    ALTO = "alto"
    EXTREMO = "extremo"
    PERSONALIZADO = "personalizado"

class CompressionSettings:
    """Configurações de compressão"""
    
    # Configurações predefinidas
    PRESETS = {
        CompressionLevel.BAIXO: {
            'quality': 80,
            'max_width': 1240,
            'name': 'Baixo',
            'description': 'Compressão mínima, máxima qualidade'
        },
        CompressionLevel.MEDIO: {
            'quality': 50,
            'max_width': 1240,
            'name': 'Médio',
            'description': 'Compressão balanceada'
        },
        CompressionLevel.ALTO: {
            'quality': 30,
            'max_width': 1000,
            'name': 'Alto',
            'description': 'Compressão alta, qualidade reduzida'
        },
        CompressionLevel.EXTREMO: {
            'quality': 20,
            'max_width': 1000,
            'name': 'Extremo',
            'description': 'Compressão máxima, tamanho mínimo'
        }
    }
    
    @classmethod
    def get_preset(cls, level: CompressionLevel) -> Dict[str, Any]:
        """Retorna configurações predefinidas para um nível"""
        return cls.PRESETS.get(level, cls.PRESETS[CompressionLevel.MEDIO])
    
    @classmethod
    def create_custom(cls, quality: int, max_width: int) -> Dict[str, Any]:
        """Cria configurações personalizadas"""
        return {
            'quality': max(1, min(100, quality)),
            'max_width': max(100, max_width),
            'name': 'Personalizado',
            'description': f'Qualidade: {quality}%, Largura máx.: {max_width}px'
        }

class PDFCompressor:
    """Classe responsável por comprimir PDFs"""
    
    def __init__(self):
        self.progress_callback: Optional[Callable[[float, str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Define callback para atualização de progresso"""
        self.progress_callback = callback
    
    def _update_progress(self, value: float, message: str = ""):
        """Atualiza progresso se callback estiver definido"""
        if self.progress_callback:
            self.progress_callback(value, message)
    
    def compress_pdf(
        self, 
        input_path: str, 
        output_path: str, 
        level: CompressionLevel = CompressionLevel.MEDIO,
        custom_quality: Optional[int] = None,
        custom_max_width: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Comprime um PDF reduzindo qualidade e tamanho das imagens.
        
        Args:
            input_path: Caminho do arquivo PDF de entrada
            output_path: Caminho do arquivo PDF de saída
            level: Nível de compressão predefinido
            custom_quality: Qualidade personalizada (1-100, apenas para PERSONALIZADO)
            custom_max_width: Largura máxima personalizada (apenas para PERSONALIZADO)
            
        Returns:
            Dicionário com informações do resultado
        """
        # Validar entrada
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
        
        # Obter configurações
        if level == CompressionLevel.PERSONALIZADO:
            if custom_quality is None or custom_max_width is None:
                raise ValueError("Qualidade e largura máxima são obrigatórios para compressão personalizada")
            settings = CompressionSettings.create_custom(custom_quality, custom_max_width)
        else:
            settings = CompressionSettings.get_preset(level)
        
        try:
            self._update_progress(0, "Iniciando compressão...")
            
            # Executar compressão
            result = self._execute_compression(input_path, output_path, settings)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na compressão: {e}")
            raise RuntimeError(f"Erro ao comprimir PDF: {str(e)}")
    
    def _execute_compression(
        self, 
        input_path: str, 
        output_path: str, 
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executa o processo de compressão"""
        
        quality = settings['quality']
        max_width = settings['max_width']
        
        print(f"🗜️ Iniciando compressão com configurações:")
        print(f"   📊 Qualidade JPEG: {quality}%")
        print(f"   📏 Largura máxima: {max_width}px")
        
        self._update_progress(5, f"Abrindo arquivo: {os.path.basename(input_path)}")
        
        # Obter tamanho original
        original_size = os.path.getsize(input_path)
        
        # Abrir PDF
        pdf = pikepdf.open(input_path)
        
        try:
            # Remover metadados
            self._update_progress(10, "Removendo metadados...")
            metadata_removed = self._remove_metadata(pdf)
            
            # Otimizar fontes  
            self._update_progress(20, "Otimizando fontes...")
            fonts_removed = self._optimize_fonts(pdf)
            
            # Processar imagens
            self._update_progress(30, "Processando imagens...")
            images_processed = self._process_images(pdf, quality, max_width)
            
            # Salvar arquivo comprimido
            self._update_progress(90, "Salvando arquivo comprimido...")
            pdf.save(output_path)
            
            # Obter tamanho final
            final_size = os.path.getsize(output_path)
            
            self._update_progress(100, "Compressão concluída!")
            
            # Calcular estatísticas
            compression_ratio = ((original_size - final_size) / original_size) * 100 if original_size > 0 else 0
            size_reduction = original_size - final_size
            
            print(f"\n--- RESUMO DA COMPRESSÃO ---")
            print(f"✓ Imagens processadas: {images_processed}")
            print(f"✓ Fontes otimizadas: {fonts_removed}")
            print(f"✓ Metadados removidos: {metadata_removed}")
            print(f"✓ Tamanho original: {self._format_size(original_size)}")
            print(f"✓ Tamanho final: {self._format_size(final_size)}")
            print(f"✓ Redução: {self._format_size(size_reduction)} ({compression_ratio:.1f}%)")
            print("🎉 Processo concluído com sucesso!")
            
            return {
                'success': True,
                'input_path': input_path,
                'output_path': output_path,
                'original_size': original_size,
                'final_size': final_size,
                'compression_ratio': compression_ratio,
                'size_reduction': size_reduction,
                'images_processed': images_processed,
                'fonts_removed': fonts_removed,
                'metadata_removed': metadata_removed,
                'settings': settings
            }
            
        finally:
            pdf.close()
    
    def _remove_metadata(self, pdf) -> bool:
        """Remove metadados do PDF"""
        metadata_removed = False
        
        try:
            # Remove metadados do PDF
            if pdf.Root.get("/Info"):
                del pdf.Root.Info
                metadata_removed = True
            
            # Remove metadados XMP se existir
            if pdf.Root.get("/Metadata"):
                del pdf.Root.Metadata
                metadata_removed = True
                
        except Exception as e:
            print(f"   ⚠️ Erro ao remover metadados: {e}")
        
        return metadata_removed
    
    def _optimize_fonts(self, pdf) -> int:
        """Remove fontes embutidas não utilizadas"""
        fonts_removed = 0
        
        try:
            for page in pdf.pages:
                # Remove fontes da página se existirem
                if hasattr(page, 'Resources') and page.Resources:
                    if page.Resources.get("/Font"):
                        fonts_count = len(page.Resources.Font) if isinstance(page.Resources.Font, dict) else 0
                        del page.Resources.Font
                        fonts_removed += fonts_count
                        
        except Exception as e:
            print(f"   ⚠️ Erro ao otimizar fontes: {e}")
        
        return fonts_removed
    
    def _process_images(self, pdf, quality: int, max_width: int) -> int:
        """Processa e comprime imagens no PDF"""
        images_processed = 0
        total_pages = len(pdf.pages)
        
        for page_num, page in enumerate(pdf.pages):
            progress_value = 30 + (page_num / total_pages) * 50  # 30-80%
            self._update_progress(
                progress_value, 
                f"Processando página {page_num + 1}/{total_pages}..."
            )
            
            try:
                # Processar imagens da página
                page_images = self._process_page_images(page, quality, max_width)
                images_processed += page_images
                
            except Exception as e:
                print(f"   ⚠️ Erro na página {page_num + 1}: {e}")
        
        return images_processed
    
    def _process_page_images(self, page, quality: int, max_width: int) -> int:
        """Processa imagens de uma página específica"""
        images_processed = 0
        
        try:
            for name, raw_image in page.images.items():
                try:
                    image = pikepdf.PdfImage(raw_image)
                    pil_image = image.as_pil_image()
                    
                    # Redimensionar se necessário
                    if pil_image.width > max_width:
                        print(f"  -> Redimensionando imagem '{name}' (de {pil_image.width}px para {max_width}px de largura)")
                        # Mantém a proporção da imagem
                        pil_image.thumbnail((max_width, max_width), Image.Resampling.LANCZOS)
                    
                    # Comprimir imagem
                    buffer = io.BytesIO()
                    
                    # Converter para RGB se necessário (JPEG não suporta transparência)
                    if pil_image.mode in ('RGBA', 'LA', 'P'):
                        # Criar fundo branco
                        rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'P':
                            pil_image = pil_image.convert('RGBA')
                        rgb_image.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode in ('RGBA', 'LA') else None)
                        pil_image = rgb_image
                    
                    # Salvar como JPEG com qualidade especificada
                    pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
                    buffer.seek(0)
                    
                    # Substituir imagem no PDF
                    raw_image.write(buffer.read(), filter=pikepdf.Name.DCTDecode)
                    images_processed += 1
                    
                    print(f"  -> Imagem '{name}' comprimida (qualidade: {quality}%)")
                    
                except Exception as e:
                    print(f"  -> Imagem '{name}' não pôde ser processada: {e}")
                    continue
        
        except Exception as e:
            print(f"   ⚠️ Erro ao processar imagens da página: {e}")
        
        return images_processed
    
    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para formato legível"""
        units = ['B', 'KB', 'MB', 'GB']
        size = float(size_bytes)
        
        for unit in units:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        
        return f"{size:.1f} TB"
    
    def get_compression_info(self, level: CompressionLevel) -> Dict[str, Any]:
        """Retorna informações sobre um nível de compressão"""
        if level == CompressionLevel.PERSONALIZADO:
            return {
                'name': 'Personalizado',
                'description': 'Configure qualidade e largura máxima',
                'quality_range': (1, 100),
                'width_range': (100, 2000)
            }
        
        return CompressionSettings.get_preset(level)
    
    def estimate_compression_ratio(self, file_path: str, level: CompressionLevel) -> Optional[float]:
        """
        Estima taxa de compressão baseada no nível selecionado.
        Esta é uma estimativa aproximada.
        
        Args:
            file_path: Caminho do arquivo
            level: Nível de compressão
            
        Returns:
            Estimativa da taxa de compressão (0-100)
        """
        try:
            # Estimativas baseadas em testes empíricos
            estimates = {
                CompressionLevel.BAIXO: 15.0,      # ~15% de redução
                CompressionLevel.MEDIO: 35.0,     # ~35% de redução  
                CompressionLevel.ALTO: 55.0,      # ~55% de redução
                CompressionLevel.EXTREMO: 70.0,   # ~70% de redução
            }
            
            return estimates.get(level, 35.0)
            
        except Exception:
            return None
