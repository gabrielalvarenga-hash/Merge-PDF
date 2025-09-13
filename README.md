# 📄 PDF Merger

Um aplicativo Python moderno para **juntar e comprimir PDFs** com interface gráfica elegante, preview completo e dark mode.

## ✨ Funcionalidades

- 🔗 **Juntar múltiplos PDFs** em um único arquivo
- 📖 **Preview completo** - visualize todas as páginas de cada PDF
- 📊 **Contador de páginas** individual e total
- 🎯 **Drag & Drop de arquivos** - arraste PDFs do Finder/Explorer direto para o app
- 🔄 **Reordenar arquivos** com drag & drop visual ou ordenação A-Z/Z-A
- 🌙 **Dark/Light Mode** com cores otimizadas
- 🗜️ **Compressão inteligente** - reduza PDFs significativamente mantendo qualidade visual
- ⭐ **4 níveis de compressão**: Baixa, Média, Alta, Smart (compressão inteligente com qualidade preservada)
- 🖱️ **Scroll com roda do mouse** em toda a interface
- 📱 **Fontes maiores** para melhor legibilidade
- 🎨 **Interface moderna** responsiva

## 🚀 Instalação

### Pré-requisitos
- Python 3.7+
- Sistema: Windows, macOS, Linux

### Instalação
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicativo
python3 pdf_merger_app.py
```

### Dependências
- `PyPDF2` - Manipulação de PDFs
- `Pillow` - Processamento de imagens
- `PyMuPDF` - Preview de PDFs
- `pikepdf` - Compressão avançada de PDFs
- `tkinter` - Interface gráfica (incluído no Python)

## 📱 Como Usar

1. **📁 Adicionar PDFs**: 
   - Clique no botão "Adicionar PDFs", ou
   - **Arraste arquivos PDF** do Finder/Explorer direto para o aplicativo
2. **👁️ Preview**: Clique em qualquer PDF para ver todas as páginas
3. **🔄 Reordenar**: 
   - Arraste o ícone ⋮⋮ para mover arquivos, ou
   - Use o botão de ordenação A-Z/Z-A
4. **🌙 Tema**: Alterne entre modo claro e escuro
5. **⚙️ Compressão**: Escolha nível desejado
6. **🚀 Juntar**: Clique para processar e salvar

## 🎨 Funcionalidades Avançadas

### Preview Completo
- Visualização de **todas as páginas** de cada PDF
- Scroll suave com roda do mouse
- Indicador de número de páginas

### Dark/Light Mode
- **Modo Claro**: Interface branca e azul
- **Modo Escuro**: Interface preta com botões escuros
- Alternância instantânea preservando estado

### Interface Responsiva
- Layout em duas colunas (lista + preview)
- Fontes otimizadas para legibilidade
- Scroll com roda do mouse em todas as áreas
- Drag & drop intuitivo

### Compressão Inteligente ⭐
- **Redução significativa**: Transforme PDFs de 50MB em ~13MB (73% de redução) mantendo qualidade
- **4 níveis disponíveis**:
  - 🔹 **Baixa**: ~10-20% redução, qualidade alta
  - 🔹 **Média**: ~25-40% redução, qualidade boa  
  - 🔹 **Alta**: ~40-60% redução, qualidade média
  - ⭐ **Smart**: ~70-80% redução, **qualidade das imagens preservada**
- **Tecnologias avançadas Smart**:
  - Preservação inteligente de qualidade de imagens
  - Otimização de streams de conteúdo sem perda visual
  - Remoção de metadados desnecessários
  - Compressão focada em estrutura, não em conteúdo visual
- **Ideal para**: Todos os tipos de documento - combina excelente compressão com qualidade preservada

## 🖼️ Logo Personalizado

Coloque um arquivo `logo.png` na mesma pasta do script para usar como ícone da aplicação. O sistema detecta automaticamente e aplica em alta resolução.

## 📋 Arquivos do Projeto

- `pdf_merger_app.py` - Aplicativo principal
- `requirements.txt` - Dependências
- `logo.png` - Ícone personalizado (opcional)
- `README.md` - Este arquivo

## 🛠️ Desenvolvimento

O aplicativo foi desenvolvido com:
- **Python 3** + tkinter para interface nativa
- **PyPDF2** para manipulação de PDFs
- **PyMuPDF** para preview de alta qualidade
- **Pillow** para processamento de imagens
- **Design moderno** com dark mode

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua feature branch
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

---

**Desenvolvido com ❤️ em Python** • *Interface moderna e intuitiva*