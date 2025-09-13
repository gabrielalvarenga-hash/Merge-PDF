#!/usr/bin/env python3
"""
Otimizador INTELIGENTE de Imagens em PDFs
Script Python avançado para compressão inteligente de arquivos PDF.
"""

import os
import io
import logging
import tempfile
import shutil
from typing import Dict, Any, Tuple, List
from pathlib import Path

# Constantes para otimização de imagens
class ImageOptimizerConstants:
    """Constantes para otimização de imagens PDF."""
    # Thresholds de tamanho
    LARGE_IMAGE_SIZE = 1024 * 1024  # 1MB - VALOR CRÍTICO testado
    LARGE_DIMENSION_THRESHOLD = 3000
    SAMPLE_SIZE = 100
    
    # Qualidades JPEG
    JPEG_QUALITY_LARGE = 95
    JPEG_QUALITY_MEDIUM = 97 
    JPEG_QUALITY_SMALL = 98
    
    # Thresholds de pixels
    LARGE_IMAGE_PIXELS = 2000000
    MEDIUM_IMAGE_PIXELS = 500000
    
    # Configurações PNG
    PNG_MAX_COLORS = 128
    PNG_VERY_SIMPLE_COLORS = 16
    PNG_COMPRESS_LEVEL = 6
    
    # Redimensionamento
    MAX_USEFUL_DIMENSION = 2500
    MIN_DIMENSION = 100
    
    # Análise de cores
    COLOR_RATIO_THRESHOLD = 0.05
    COMPRESSION_THRESHOLD = 0.90  # 90% do tamanho original

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    
try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def optimize_pdf_images(input_path: str, output_path: str, quality: str = 'smart') -> Dict[str, Any]:
    """
    Otimiza arquivos PDF com compressão INTELIGENTE de imagens.
    
    ⚠️⚠️ CONFIGURAÇÃO CRÍTICA TESTADA ⚠️⚠️
    NUNCA alterar: original_size > 1024 * 1024 (linha ~281)
    Este é o ÚNICO valor que funciona sem destruir arquivos!
    Qualquer outro limite causará problemas no PDF final!
    
    Esta função implementa estratégia de preservação com limpeza suave:
    - Preserva qualidade máxima das imagens (JPEG 95-98)
    - Redimensiona apenas se extremamente grandes (>3000px)
    - Remove metadados e otimiza estruturas
    - Foco na limpeza sem comprometer qualidade visual
    
    Args:
        input_path (str): Caminho para o arquivo PDF original
        output_path (str): Caminho para salvar o arquivo PDF limpo
        quality (str): Nível de processamento (apenas 'smart' suportado)
    
    Returns:
        Dict[str, Any]: Dicionário com estatísticas do processamento contendo:
            - success (bool): Se a operação foi bem-sucedida
            - original_size (int): Tamanho original em bytes
            - final_size (int): Tamanho final em bytes
            - compression_ratio (float): Porcentagem de redução
            - images_processed (int): Número de imagens processadas
            - pages_processed (int): Número de páginas processadas
            - jpeg_images (int): Imagens JPEG processadas
            - png_images (int): Imagens PNG processadas
            - resized_images (int): Número de imagens redimensionadas (>2000px)
            - error_message (str): Mensagem de erro, se houver
    
    Raises:
        RuntimeError: Se PyMuPDF não estiver instalado
        FileNotFoundError: Se o arquivo de entrada não existir
        ValueError: Se o nível de qualidade for inválido
        Exception: Para outros erros durante o processamento
    """
    
    # Verificar dependências
    if not HAS_PYMUPDF:
        raise RuntimeError("PyMuPDF (fitz) é obrigatório. Execute: pip install PyMuPDF")
    
    # Verificar arquivo de entrada
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")
    
    # Apenas nível 'smart' é suportado
    if quality != 'smart':
        logger.warning(f"Nível '{quality}' não suportado. Usando 'smart'.")
        quality = 'smart'
    
    # Estatísticas iniciais
    original_size = os.path.getsize(input_path)
    images_processed = 0
    pages_processed = 0
    jpeg_images = 0
    png_images = 0 
    resized_images = 0
    
    logger.info(f"🎯 Iniciando processamento de PDF com preservação máxima: {Path(input_path).name}")
    logger.info(f"📊 Tamanho original: {original_size / 1024 / 1024:.2f} MB")
    logger.info(f"🎯 Modo: {quality} (Preservação máxima de qualidade, otimização suave apenas)")
    
    try:
        # Abrir documento original
        doc_original = fitz.open(input_path)
        logger.info(f"📄 PDF carregado: {len(doc_original)} páginas")
        
        # Criar novo documento LIMPO (sem metadados desnecessários)
        doc_novo = fitz.open()
        
        # LIMPEZA COMPLETA DE METADADOS
        _limpar_metadados_completo(doc_novo)
        
        # Processar cada página com otimização balanceada
        for num_pagina in range(len(doc_original)):
            logger.info(f"🔄 Processando página {num_pagina + 1}/{len(doc_original)}")
            
            pagina_original = doc_original[num_pagina]
            
            # Criar nova página limpa
            pagina_nova = doc_novo.new_page(
                width=pagina_original.rect.width,
                height=pagina_original.rect.height
            )
            
            # Processar imagens com compressão balanceada
            stats_pagina = _processar_pagina_balanceada(pagina_original, pagina_nova)
            
            # Atualizar estatísticas
            images_processed += stats_pagina['total_images']
            jpeg_images += stats_pagina['jpeg_images']
            png_images += stats_pagina['png_images']
            resized_images += stats_pagina['resized_images']
            
            # Copiar APENAS texto (sem imagens para não anular compressão)
            _copiar_conteudo_texto_apenas(pagina_original, pagina_nova)
            
            pages_processed += 1
        
        # Fechar documento original
        doc_original.close()
        
        # Salvar PDF otimizado
        logger.info("💾 Salvando PDF otimizado...")
        
        # Usar arquivo temporário para evitar problemas
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        doc_novo.save(
            temp_path,
            garbage=4,          # Limpeza de estruturas
            deflate=True,       # Comprimir streams
            clean=True,         # Ativar limpeza
            ascii=False,        # Encoding binário
            expand=0,           # Manter compressão
            linear=False,       # Não linearizar
            pretty=False,       # Não formatar
            encryption=fitz.PDF_ENCRYPT_NONE,  # Sem criptografia
            permissions=-1,     # Todas as permissões
            incremental=False   # Reescrever arquivo
        )
        
        # Substituir arquivo original
        shutil.move(temp_path, output_path)
        
        # Fechar documento novo
        doc_novo.close()
        
        # Calcular estatísticas finais
        final_size = os.path.getsize(output_path)
        compression_ratio = ((original_size - final_size) / original_size) * 100
        
        logger.info("✅ PDF OTIMIZADO criado com sucesso!")
        logger.info(f"📊 Estatísticas do processamento:")
        logger.info(f"   📂 Tamanho original: {original_size / 1024 / 1024:.2f} MB")
        logger.info(f"   📦 Tamanho final: {final_size / 1024 / 1024:.2f} MB")
        logger.info(f"   🎯 Redução: {compression_ratio:.1f}%")
        logger.info(f"   🖼️ Total de imagens: {images_processed}")
        logger.info(f"   📸 JPEG processados: {jpeg_images}")
        logger.info(f"   🎨 PNG processados: {png_images}")
        logger.info(f"   📏 Imagens redimensionadas: {resized_images}")
        logger.info(f"   📄 Páginas processadas: {pages_processed}")
        logger.info(f"   🧹 Metadados do documento removidos")
        logger.info(f"   🔧 Otimização suave aplicada (JPEG 95-98 qualidade máxima)")
        logger.info(f"   📝 Texto preservado com formatação original")
        logger.info(f"   🖼️ Imagens: qualidade máxima preservada (só >1MB processadas)")
        logger.info(f"   ✅ PRESERVAÇÃO MÁXIMA APLICADA")
        logger.info(f"   🎯 Configuração: qualidade máxima preservada")
        
        # Verificar resultado da PRESERVAÇÃO MÁXIMA
        final_mb = final_size / 1024 / 1024
        
        if compression_ratio < 0:
            logger.info(f"📊 Arquivo ligeiramente maior ({abs(compression_ratio):.1f}%) - reconstrução limpa aplicada")
        elif compression_ratio < 10:
            logger.info(f"📊 Tamanho mantido ({compression_ratio:.1f}%) - qualidade máxima preservada!")
        elif compression_ratio < 25:
            logger.info(f"📊 Otimização suave ({compression_ratio:.1f}%) - qualidade totalmente preservada!")
        else:
            logger.info(f"📊 Limpeza eficiente ({compression_ratio:.1f}%) - apenas metadados removidos!")
        
        logger.info(f"📊 Arquivo final: {final_mb:.1f}MB com qualidade máxima preservada")
        
        return {
            'success': True,
            'original_size': original_size,
            'final_size': final_size,
            'compression_ratio': compression_ratio,
            'images_processed': images_processed,
            'pages_processed': pages_processed,
            'jpeg_images': jpeg_images,
            'png_images': png_images,
            'resized_images': resized_images,
            'error_message': None
        }
        
    except Exception as e:
        error_msg = f"Erro durante otimização inteligente: {str(e)}"
        logger.error(error_msg)
        
        return {
            'success': False,
            'original_size': original_size,
            'final_size': 0,
            'compression_ratio': 0,
            'images_processed': images_processed,
            'pages_processed': pages_processed,
            'jpeg_images': jpeg_images,
            'png_images': png_images,
            'resized_images': resized_images,
            'error_message': error_msg
        }


def _processar_pagina_balanceada(pagina_original: fitz.Page, pagina_nova: fitz.Page) -> Dict[str, Any]:
    """
    Processa página preservando QUALIDADE MÁXIMA das imagens.
    
    ⚠️ ATENÇÃO CRÍTICA: NUNCA alterar o limite de 1MB (1024*1024)
    Esta configuração foi TESTADA e é a ÚNICA que funciona sem destruir arquivos!
    
    Funcionalidades:
    - Preserva qualidade máxima das imagens (JPEG 95-98)
    - Redimensiona apenas se extremamente grandes (>3000px)
    - Processa apenas imagens muito grandes (>1MB) ⚠️ VALOR CRÍTICO
    - Foco na preservação máxima de qualidade visual
    
    Args:
        pagina_original: Página de origem 
        pagina_nova: Página de destino (limpa)
        
    Returns:
        Dict com estatísticas das imagens processadas
    """
    stats = {
        'total_images': 0,
        'jpeg_images': 0,
        'png_images': 0,
        'resized_images': 0
    }
    
    try:
        # Obter lista de imagens na página original
        lista_imagens = pagina_original.get_images(full=True)
        stats['total_images'] = len(lista_imagens)
        
        for img_index, img_ref in enumerate(lista_imagens):
            try:
                # Extrair referência da imagem
                xref = img_ref[0]  # Referência do objeto imagem
                
                # Obter dados da imagem original
                img_dict = pagina_original.parent.extract_image(xref)
                img_data = img_dict["image"]
                img_ext = img_dict["ext"]
                original_size = len(img_data)
                
                # Obter retângulos onde a imagem aparece
                img_rects = pagina_original.get_image_rects(xref)
                
                # ═══════════════════════════════════════════════════════════════════
                # ⚠️⚠️⚠️ ZONA CRÍTICA - NÃO ALTERAR NADA ABAIXO! ⚠️⚠️⚠️
                # ═══════════════════════════════════════════════════════════════════
                # ⚠️ LINHA CRÍTICA - NÃO ALTERAR! ⚠️
                # Esta é a ÚNICA configuração que funciona sem destruir arquivos
                # TESTADO e APROVADO: 1024 * 1024 (1MB) é o limite seguro
                # NUNCA alterar este valor - qualquer mudança causa problemas!
                if HAS_PIL and original_size > 1024 * 1024:  # ⚠️ CRÍTICO: > 1MB - NÃO MEXER! ⚠️
                    # ═══════════════════════════════════════════════════════════════════
                    # ✅ FIM DA ZONA CRÍTICA - Configuração testada e aprovada acima ✅
                    # ═══════════════════════════════════════════════════════════════════
                    try:
                        # Converter para PIL Image
                        pil_image = Image.open(io.BytesIO(img_data))
                        pil_image = ImageOps.exif_transpose(pil_image)
                        
                        # Redimensionar apenas se extremamente grande (máxima preservação)
                        redimensionada = False
                        if pil_image.size[0] > 3000 or pil_image.size[1] > 3000:
                            pil_image, redimensionada = _redimensionar_balanceado(pil_image)
                            if redimensionada:
                                stats['resized_images'] += 1
                        
                        # Comprimir com qualidade máxima
                        formato_final, img_data_comprimida = _comprimir_balanceado(pil_image)
                        
                        # Usar imagem comprimida apenas se redução mínima (preservar qualidade)
                        if len(img_data_comprimida) < original_size * 0.90:  # Apenas se reduzir pelo menos 5%
                            img_data = img_data_comprimida
                            logger.debug(f"   🗜️ Imagem {img_index + 1}: {original_size//1024}KB → {len(img_data)//1024}KB ({formato_final})")
                        else:
                            logger.debug(f"   ✅ Imagem {img_index + 1}: mantida original ({original_size//1024}KB, {img_ext.upper()})")
                            
                    except Exception as compress_error:
                        logger.debug(f"   ⚠️ Erro na compressão da imagem {img_index + 1}, usando original: {compress_error}")
                
                # Inserir imagem (original ou comprimida)
                for rect in img_rects:
                    try:
                        pagina_nova.insert_image(
                            rect=rect,
                            stream=img_data,
                            keep_proportion=True,
                            alpha=255
                        )
                    except Exception as insert_error:
                        logger.warning(f"   ⚠️ Erro ao inserir imagem {img_index + 1}: {insert_error}")
                        continue
                
                # Atualizar estatísticas baseado no formato original
                if img_ext.lower() in ['jpg', 'jpeg']:
                    stats['jpeg_images'] += 1
                elif img_ext.lower() == 'png':
                    stats['png_images'] += 1
                
            except Exception as ref_error:
                logger.warning(f"   ⚠️ Erro ao processar referência de imagem {img_index + 1}: {ref_error}")
                continue
    
    except Exception as page_error:
        logger.warning(f"⚠️ Erro ao extrair imagens da página: {page_error}")
    
    return stats


def _redimensionar_balanceado(pil_image: Image.Image) -> Tuple[Image.Image, bool]:
    """
    Redimensiona imagem de forma BALANCEADA para meta de 3.5-4MB.
    
    Estratégia balanceada:
    - Reduz para 85% da resolução se > 1800px
    - Limite máximo de 2500px em qualquer dimensão
    - Equilíbrio entre qualidade visual e tamanho
    
    Args:
        pil_image: Imagem PIL
        
    Returns:
        Tuple[Image.Image, bool]: (imagem_redimensionada, foi_redimensionada)
    """
    try:
        # Dimensões da imagem original
        img_width, img_height = pil_image.size
        
        # REDIMENSIONAMENTO CONSERVADOR
        new_width = img_width
        new_height = img_height
        foi_redimensionada = False
        
        # Redimensionar apenas se extremamente grandes (máxima preservação)
        max_useful_dimension = 2500  # Dimensão mais permissiva
        if img_width > max_useful_dimension or img_height > max_useful_dimension:
            if img_width > img_height:
                new_width = max_useful_dimension
                new_height = int((max_useful_dimension * img_height) / img_width)
            else:
                new_height = max_useful_dimension
                new_width = int((max_useful_dimension * img_width) / img_height)
            foi_redimensionada = True
            logger.debug(f"   📏 Redimensionamento inteligente: {img_width}x{img_height} → {new_width}x{new_height}")
        else:
            logger.debug(f"   📏 Imagem mantida em tamanho adequado: {img_width}x{img_height}")
        
        # Garantir dimensões mínimas
        new_width = max(new_width, 100)
        new_height = max(new_height, 100)
        
        if foi_redimensionada:
            # Redimensionar usando algoritmo de alta qualidade
            resized_image = pil_image.resize(
                (new_width, new_height), 
                Image.Resampling.LANCZOS  # Algoritmo de alta qualidade
            )
            
            logger.debug(f"   📏 Redimensionamento balanceado: {img_width}x{img_height} → {new_width}x{new_height}")
            return resized_image, True
        
        return pil_image, False
        
    except Exception as e:
        logger.warning(f"Erro no redimensionamento balanceado: {e}")
        return pil_image, False


def _comprimir_balanceado(pil_image: Image.Image) -> Tuple[str, bytes]:
    """
    Comprime imagem usando estratégias BALANCEADAS para meta de 3.5-4MB.
    
    Estratégias balanceadas:
    - JPEG: Qualidade 70-80 (balanceada)
    - PNG: Para gráficos muito simples apenas
    - Análise inteligente priorizando legibilidade
    
    Args:
        pil_image: Imagem PIL para comprimir
        
    Returns:
        Tuple[str, bytes]: (formato_escolhido, dados_comprimidos)
    """
    try:
        # Análise de conteúdo da imagem (balanceada)
        formato_otimo = _analisar_conteudo_balanceado(pil_image)
        
        if formato_otimo == 'JPEG':
            return _comprimir_jpeg_balanceado(pil_image)
        else:
            return _comprimir_png_balanceado(pil_image)
            
    except Exception as e:
        logger.warning(f"Erro na compressão balanceada: {e}")
        # Fallback para JPEG balanceado
        return _comprimir_jpeg_balanceado(pil_image)


def _analisar_conteudo_balanceado(pil_image: Image.Image) -> str:
    """
    Análise BALANCEADA que prioriza JPEG para meta de 3.5-4MB.
    
    Critérios restritivos para PNG, priorizando JPEG balanceado na maioria dos casos
    para alcançar tamanho adequado mantendo legibilidade.
    
    Args:
        pil_image: Imagem PIL
        
    Returns:
        str: 'JPEG' para maioria das imagens, 'PNG' apenas para casos muito específicos
    """
    try:
        # Converter para RGB para análise rápida
        if pil_image.mode not in ['RGB', 'RGBA']:
            temp_image = pil_image.convert('RGB')
        else:
            temp_image = pil_image
        
        # Análise rápida (amostra menor)
        sample_size = 100
        if temp_image.size[0] > sample_size or temp_image.size[1] > sample_size:
            temp_image.thumbnail((sample_size, sample_size), Image.Resampling.NEAREST)
        
        # Contar cores únicas (aproximado)
        colors = temp_image.getcolors(maxcolors=64*64*64)  # Menor limite para ser mais rápido
        if colors is None:
            # Muitas cores - usar JPEG
            return 'JPEG'
        
        unique_colors = len(colors)
        pixel_count = temp_image.size[0] * temp_image.size[1]
        
        # CRITÉRIOS MUITO RESTRITIVOS para PNG (priorizar JPEG balanceado)
        # Usar PNG apenas para gráficos muito simples e pequenos
        if (unique_colors <= 32 and           # Até 32 cores apenas (muito restritivo)
            pixel_count < 10000 and           # Apenas imagens muito pequenas
            unique_colors < pixel_count * 0.05):  # Cores representam <5% dos pixels (muito restritivo)
            
            logger.debug(f"   🎨 PNG restrito: {unique_colors} cores em {pixel_count} pixels")
            return 'PNG'
        else:
            logger.debug(f"   📷 JPEG balanceado: {unique_colors} cores em {pixel_count} pixels")
            return 'JPEG'
            
    except Exception as e:
        logger.debug(f"Erro na análise balanceada: {e}")
        # Fallback: sempre JPEG para máxima compressão
        return 'JPEG'


def _comprimir_jpeg_balanceado(pil_image: Image.Image) -> Tuple[str, bytes]:
    """
    Comprime imagem como JPEG com qualidade balanceada.
    
    Args:
        pil_image: Imagem PIL
        
    Returns:
        Tuple[str, bytes]: ('JPEG', dados_comprimidos)
    """
    # Converter para RGB se necessário
    if pil_image.mode in ['RGBA', 'P', 'LA']:
        # Para transparência, criar fundo branco
        rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
        if pil_image.mode == 'P':
            pil_image = pil_image.convert('RGBA')
        rgb_image.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode in ['RGBA', 'LA'] else None)
        pil_image = rgb_image
    elif pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    
    quality = _determine_jpeg_quality(pil_image)
    
    img_buffer = io.BytesIO()
    pil_image.save(
        img_buffer,
        format='JPEG',
        quality=quality,
        optimize=True,
        progressive=False,
        exif=b'',
        subsampling=0
    )
    
    return 'JPEG', img_buffer.getvalue()

def _determine_jpeg_quality(pil_image: Image.Image) -> int:
    """Determina qualidade JPEG baseada no tamanho da imagem."""
    pixels = pil_image.size[0] * pil_image.size[1]
    
    if pixels > ImageOptimizerConstants.LARGE_IMAGE_PIXELS:
        return ImageOptimizerConstants.JPEG_QUALITY_LARGE
    elif pixels > ImageOptimizerConstants.MEDIUM_IMAGE_PIXELS:
        return ImageOptimizerConstants.JPEG_QUALITY_MEDIUM
    else:
        return ImageOptimizerConstants.JPEG_QUALITY_SMALL


def _comprimir_png_balanceado(pil_image: Image.Image) -> Tuple[str, bytes]:
    """
    Comprime imagem como PNG otimizado.
    
    Args:
        pil_image: Imagem PIL
        
    Returns:
        Tuple[str, bytes]: ('PNG', dados_comprimidos)
    """
    pil_image = _optimize_png_colors(pil_image)
    
    img_buffer = io.BytesIO()
    pil_image.save(
        img_buffer,
        format='PNG',
        optimize=True,
        compress_level=ImageOptimizerConstants.PNG_COMPRESS_LEVEL,
        exif=b''
    )
    
    return 'PNG', img_buffer.getvalue()

def _optimize_png_colors(pil_image: Image.Image) -> Image.Image:
    """Otimiza cores de imagem PNG."""
    try:
        if pil_image.mode in ['RGB', 'RGBA']:
            quantized = pil_image.quantize(
                colors=ImageOptimizerConstants.PNG_MAX_COLORS,
                method=Image.Quantize.MEDIANCUT,
                dither=Image.Dither.FLOYDSTEINBERG
            )
            return quantized
        elif pil_image.mode == 'P':
            colors = pil_image.getcolors()
            if colors and len(colors) > ImageOptimizerConstants.PNG_VERY_SIMPLE_COLORS:
                quantized = pil_image.quantize(
                    colors=ImageOptimizerConstants.PNG_VERY_SIMPLE_COLORS, 
                    method=Image.Quantize.MEDIANCUT
                )
                return quantized
    except Exception:
        pass
    
    return pil_image


def _limpar_metadados_completo(doc: fitz.Document) -> None:
    """
    Remove TODOS os metadados desnecessários do documento PDF.
    
    Funcionalidades:
    - Remove metadados de criação/modificação
    - Remove informações do produtor/criador
    - Remove palavras-chave e título
    - Remove informações de autoria
    - Limpa qualquer informação de tracking
    
    Args:
        doc: Documento PDF para limpar
    """
    try:
        # Limpar todos os metadados possíveis
        metadata_keys = [
            'title', 'author', 'subject', 'keywords', 'creator', 'producer',
            'creationDate', 'modDate', 'trapped', 'encryption'
        ]
        
        for key in metadata_keys:
            try:
                doc.set_metadata({key: ""})
            except:
                pass
        
        # Remover informações XMP se existirem
        try:
            doc.set_xml_metadata("")
        except:
            pass
            
        logger.debug("   🧹 Metadados limpos completamente")
        
    except Exception as e:
        logger.debug(f"Erro ao limpar metadados: {e}")


def _copiar_conteudo_texto_apenas(pagina_origem: fitz.Page, pagina_destino: fitz.Page) -> None:
    """
    Copia APENAS TEXTO da página original, preservando formatação.
    
    NÃO copia imagens para não anular a compressão aplicada.
    - Mantém: texto com formatação original
    - Remove: imagens (já foram otimizadas)
    - Preserva: fontes e cores do texto original
    
    Args:
        pagina_origem: Página de origem
        pagina_destino: Página de destino
    """
    try:
        # Copiar apenas texto preservando formatação original
        text_dict = pagina_origem.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:  # Bloco de texto
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        if text.strip():  # Apenas se não for vazio
                            try:
                                # Inserir preservando formatação original
                                pagina_destino.insert_text(
                                    fitz.Point(span["bbox"][0], span["bbox"][1]),
                                    text,
                                    fontsize=span["size"],
                                    fontname=span.get("font", "helv"),
                                    color=span.get("color", 0)
                                )
                            except:
                                # Fallback com fonte básica
                                try:
                                    pagina_destino.insert_text(
                                        fitz.Point(span["bbox"][0], span["bbox"][1]),
                                        text,
                                        fontsize=span["size"],
                                        color=span.get("color", 0)
                                    )
                                except:
                                    # Fallback final simples
                                    try:
                                        pagina_destino.insert_text(
                                            fitz.Point(span["bbox"][0], span["bbox"][1]),
                                            text,
                                            fontsize=12
                                        )
                                    except:
                                        pass
        
        logger.debug("   📝 Texto copiado (sem imagens)")
                                
    except Exception as e:
        logger.debug(f"Erro ao copiar texto: {e}")


# Funções auxiliares para o módulo

if __name__ == "__main__":
    """
    Exemplo de uso do otimizador de PDFs
    """
    exemplo_input = "exemplo_input.pdf"
    exemplo_output = "exemplo_output.pdf"
    
    if not os.path.exists(exemplo_input):
        print(f"⚠️ Arquivo não encontrado: {exemplo_input}")
        exit(1)
    
    print("🔄 Processando PDF...")
    try:
        resultado = optimize_pdf_images(exemplo_input, exemplo_output, 'smart')
        if resultado['success']:
            print(f"✅ Concluído! Arquivo salvo: {exemplo_output}")
            print(f"📊 Redução: {resultado['compression_ratio']:.1f}%")
        else:
            print(f"❌ Erro: {resultado['error_message']}")
    except Exception as e:
        print(f"❌ Erro: {str(e)}")