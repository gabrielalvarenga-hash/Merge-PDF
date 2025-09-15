# PDF Merger

Aplicação Python para merge e compressão de arquivos PDF com interface gráfica tkinter.

## Funcionalidades

- **Merge de PDFs**: Combinação de múltiplos arquivos PDF em ordem configurável
- **Compressão inteligente**: 5 níveis predefinidos + configuração personalizada
- **Preservação de conteúdo**: Texto e elementos vetoriais mantidos durante compressão
- **Padronização A4**: Normalização automática de páginas para formato A4
- **Preview de documentos**: Visualização de páginas antes do processamento
- **Interface drag & drop**: Suporte nativo para arrastar arquivos
- **Temas visuais**: Modo claro e escuro
- **Processamento assíncrono**: Operações em background com feedback de progresso

## Instalação

### Requisitos
- Python 3.7+
- Sistema operacional: Windows, macOS, Linux

### Dependências
```bash
pip install -r requirements.txt
```

### Execução
```bash
python3 main.py
```

## Dependências Técnicas

### Bibliotecas principais
- `pikepdf`: Engine de compressão e manipulação de PDFs
- `PyPDF2`: Merge e manipulação básica de documentos PDF
- `Pillow`: Processamento e otimização de imagens
- `PyMuPDF`: Renderização de previews
- `PyCryptodome`: Suporte a documentos criptografados

### Bibliotecas opcionais
- `tkinterdnd2`: Sistema drag & drop (fallback disponível)

## Configuração de Compressão

| Nível | Qualidade JPEG | Largura Máxima | Compressão Estimada |
|-------|----------------|----------------|-------------------|
| Baixo | 80% | 1240px | ~15% |
| Médio | 50% | 1240px | ~35% |
| Alto | 30% | 1000px | ~55% |
| Extremo | 20% | 1000px | ~70% |
| Personalizado | 1-100% | 100-2000px | Variável |

## Arquitetura

```
├── main.py                 # Entry point
├── main_window.py          # Interface principal
├── config.py              # Configurações globais
├── core/
│   ├── pdf_handler.py     # Merge e manipulação
│   ├── pdf_compressor.py  # Engine de compressão
│   └── file_manager.py    # Gerenciamento de arquivos
└── ui/
    ├── components.py      # Componentes de interface
    ├── themes.py         # Sistema de temas
    ├── drag_drop.py      # Funcionalidade drag & drop
    └── preview.py        # Renderização de previews
```

## Algoritmo de Compressão

1. **Análise de documento**: Identificação de imagens, texto e metadados
2. **Preservação de texto**: Manutenção de fontes e elementos textuais
3. **Otimização de imagens**: 
   - Redimensionamento para largura máxima configurada
   - Conversão para JPEG com qualidade especificada
   - Otimização de palette de cores
4. **Limpeza de metadados**: Remoção de dados desnecessários
5. **Reconstrução**: Montagem do documento otimizado

## Performance

- **Threading**: Operações de I/O em threads separadas
- **Lazy loading**: Carregamento sob demanda de previews
- **Gerenciamento de memória**: Liberação automática de recursos
- **Cache**: Sistema de cache para previews renderizados

## Tratamento de Erros

- Validação de arquivos de entrada
- Recuperação automática de falhas de dependências
- Logging estruturado para debugging
- Fallbacks para funcionalidades opcionais

## API Interna

### PDFCompressor
```python
compressor = PDFCompressor()
result = compressor.compress_pdf(
    input_path="input.pdf",
    output_path="output.pdf",
    level=CompressionLevel.MEDIO
)
```

### PDFMerger
```python
merger = PDFMerger()
result = merger.merge_pdfs(
    file_paths=["file1.pdf", "file2.pdf"],
    output_path="merged.pdf"
)
```

## Limitações Técnicas

- Suporte limitado para PDFs com proteção DRM avançada
- Compressão otimizada para imagens rasterizadas (não afeta vetores)
- Interface baseada em tkinter (limitações de styling nativo)

## Licença

MIT License

## Dependências Detalhadas

**pikepdf**: Biblioteca principal para compressão PDF. Responsável pela otimização de imagens e metadados preservando integridade do texto.

**PyPDF2**: Manipulação e merge de documentos PDF.

**PyMuPDF**: Renderização de alta qualidade para sistema de preview.

**Pillow**: Processamento de imagens para redimensionamento e otimização.

**tkinter**: Interface gráfica nativa Python.