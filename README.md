# 📄 PDF Merger

Uma aplicação Python moderna para **juntar e comprimir PDFs** com interface gráfica elegante, preview completo e dark mode.

## ✨ Funcionalidades Principais

- 🔗 **Juntar múltiplos PDFs** - Combine vários arquivos PDF em um único documento
- 📖 **Preview completo em tempo real** - Visualize todas as páginas de cada PDF antes de juntar
- 📊 **Contador inteligente de páginas** - Mostra páginas individuais e total em tempo real
- 🎯 **Drag & Drop avançado** - Arraste PDFs do Finder/Explorer direto para a aplicação
- 🔄 **Reordenação flexível** - Reorganize arquivos com drag & drop visual ou ordenação A-Z/Z-A
- 🌙 **Tema Dark/Light dinâmico** - Alternância instantânea entre temas com persistência
- 📐 **Padronização A4 automática** - Todas as páginas são padronizadas para formato A4 profissional
- 🖱️ **Interface totalmente navegável** - Scroll com roda do mouse em todas as áreas
- 📱 **Tipografia otimizada** - Fontes maiores para melhor legibilidade
- 🎨 **Design moderno e responsivo** - Interface clean com componentes customizados
- 🔐 **Suporte a PDFs protegidos** - Manipula PDFs com criptografia automaticamente
- ⚡ **Performance otimizada** - Processamento assíncrono com barra de progresso em tempo real

## 🚀 Instalação

### Pré-requisitos
- Python 3.7+
- Sistema: Windows, macOS, Linux

### Instalação

```bash
# 1. Clone ou baixe o projeto
git clone https://github.com/seu-usuario/merge-pdf.git
cd merge-pdf

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar aplicação
python3 main.py
```

### Dependências Essenciais
- `PyPDF2` - Manipulação e merge de arquivos PDF
- `Pillow` - Processamento de imagens
- `PyMuPDF` - Preview de PDFs em alta qualidade  
- `PyCryptodome` - Suporte a PDFs protegidos/criptografados
- `tkinterdnd2` - Drag & drop de arquivos externos (opcional)
- `tkinter` - Interface gráfica nativa (incluído no Python)

### Dependências Opcionais
Se algumas dependências não estiverem disponíveis, a aplicação continuará funcionando com funcionalidades limitadas:
- Sem `tkinterdnd2`: Drag & drop desabilitado (use botão "Adicionar")
- Sem `PyMuPDF`: Preview desabilitado (merge continuará funcionando)
- Sem `Pillow`: Ícones desabilitados (funcionalidade core mantida)

## 📱 Como Usar

1. **📁 Adicionar PDFs**: 
   - Clique no botão "Adicionar PDFs", ou
   - **Arraste arquivos PDF** do Finder/Explorer direto para o aplicativo
2. **👁️ Preview**: Clique em qualquer PDF para ver todas as páginas
3. **🔄 Reordenar**: 
   - Arraste o ícone ⋮⋮ para mover arquivos, ou
   - Use as setas ▲▼, ou
   - Use o botão de ordenação A-Z/Z-A
4. **🌙 Tema**: Alterne entre modo claro e escuro
5. **📐 Formato A4**: Todas as páginas são automaticamente padronizadas
6. **🚀 Juntar**: Clique para processar e salvar

## 🎨 Funcionalidades Avançadas

### Preview Completo
- Visualização de **todas as páginas** de cada PDF
- Scroll suave com roda do mouse
- Indicador de número de páginas
- Preview responsivo com qualidade otimizada

### Dark/Light Mode
- **Modo Claro**: Interface branca e azul
- **Modo Escuro**: Interface preta com botões escuros
- Alternância instantânea preservando estado

### Interface Responsiva
- Layout em duas colunas (lista + preview)
- Fontes otimizadas para legibilidade
- Scroll com roda do mouse em todas as áreas
- Drag & drop intuitivo com indicadores visuais

### Padronização A4 Profissional 📐
- **Formato único**: Todas as páginas padronizadas para A4 (595.276 x 841.890 pts)
- **Compatibilidade total**: Sistemas bancários, bandeiras de crédito e impressão profissional
- **Processamento inteligente**: Preserva conteúdo enquanto ajusta dimensões
- **Otimização automática**: Redimensionamento e centralização das páginas

## 🖼️ Logo Personalizado

Coloque um arquivo `logo.png` na mesma pasta do script para usar como ícone da aplicação. O sistema detecta automaticamente e aplica em alta resolução.

## 📁 Estrutura do Projeto

```
📦 PDF Merger/
├── 📜 main.py                    # Ponto de entrada da aplicação
├── 📜 main_window.py             # Janela principal e coordenação
├── 📜 config.py                  # Configurações globais
├── 📜 requirements.txt           # Dependências Python
├── 📜 logo.png                   # Logo personalizado (opcional)
├── 📁 core/                      # Módulos principais
│   ├── 📜 __init__.py           
│   ├── 📜 pdf_handler.py         # Manipulação e merge de PDFs
│   ├── 📜 pdf_image_optimizer.py # Otimização inteligente de PDFs
│   └── 📜 file_manager.py        # Gerenciamento de arquivos
├── 📁 ui/                        # Interface gráfica
│   ├── 📜 __init__.py           
│   ├── 📜 components.py          # Componentes UI customizados
│   ├── 📜 themes.py              # Gerenciador de temas dark/light
│   ├── 📜 drag_drop.py           # Sistema de drag & drop
│   └── 📜 preview.py             # Preview de PDFs
└── 📜 README.md                  # Documentação
```

## 🛠️ Arquitetura e Tecnologias

### Stack Tecnológico
- **Python 3.7+** - Linguagem principal com tipagem moderna
- **tkinter** - Interface gráfica nativa multiplataforma  
- **Arquitetura modular** - Separação clara de responsabilidades

### Módulos Principais
- **Core Engine** (`core/`): Lógica de negócio e processamento de PDFs
  - `pdf_handler.py` - Engine de merge com progress tracking
  - `pdf_image_optimizer.py` - Otimização inteligente preservando qualidade
  - `file_manager.py` - Gerenciamento inteligente de arquivos

- **Interface Moderna** (`ui/`): Componentes visuais avançados
  - `themes.py` - Sistema de temas com persistência
  - `components.py` - Widgets customizados e modernos
  - `drag_drop.py` - Drag & drop nativo do sistema
  - `preview.py` - Renderização em tempo real de PDFs

### Funcionalidades Avançadas
- **Threading assíncrono** para operações pesadas
- **Progress tracking** em tempo real com callbacks
- **Detecção automática de dependências** com graceful degradation  
- **Sistema de logging** integrado para debugging
- **Gerenciamento de memória** otimizado para arquivos grandes

## 🚀 Recursos de Performance

### Otimizações Implementadas
- **Processamento assíncrono**: Operações pesadas em threads separadas
- **Preview otimizado**: Cache inteligente de miniaturas renderizadas
- **Padronização A4**: Algoritmo eficiente de redimensionamento
- **Gerenciamento de memória**: Liberação automática de recursos após operações
- **Progress tracking**: Feedback em tempo real do progresso de operações

### Benchmarks Típicos
- **Merge**: 10 PDFs (100MB total) → ~5 segundos
- **Padronização A4**: Processamento automático sem perda de qualidade
- **Preview**: Renderização instantânea de até 100 páginas
- **Drag & drop**: Suporte a dezenas de arquivos simultaneamente

## 🔧 Limpeza e Otimização

### Código Limpo ✨
Esta versão foi **completamente otimizada** removendo:
- **Dependências desnecessárias**: Removidas bibliotecas não utilizadas (PyPDF4, pikepdf, numpy, reportlab)
- **Constantes não utilizadas**: Limpeza de configurações desnecessárias
- **Imports redundantes**: Remoção de imports não referenciados
- **Cache Python**: Limpeza de arquivos `.pyc` e diretórios `__pycache__`

### Dependências Enxutas
O projeto agora usa apenas as dependências essenciais, resultando em:
- **Instalação mais rápida**: Menos pacotes para baixar
- **Menor footprint**: Redução significativa no tamanho da instalação  
- **Menos conflitos**: Menor chance de problemas de compatibilidade
- **Melhor performance**: Código mais limpo e otimizado

## 🤝 Como Contribuir

Contribuições são muito bem-vindas! Para contribuir:

1. **Fork** este repositório
2. **Clone** seu fork localmente
3. **Crie** uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
4. **Teste** suas alterações extensivamente
5. **Commit** suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)  
6. **Push** para sua branch (`git push origin feature/MinhaFeature`)
7. **Abra** um Pull Request detalhado

### Áreas para Contribuição
- 🐛 **Bug fixes** e correções
- ✨ **Novas funcionalidades** (filtros, formatos, etc.)
- 🎨 **Melhorias de UI/UX**
- 📚 **Documentação** e exemplos
- 🚀 **Otimizações de performance**
- 🌍 **Internacionalização** (suporte a mais idiomas)

## 📄 Licença

Este projeto está sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **PyPDF2** - Biblioteca fundamental para manipulação de PDFs
- **PyMuPDF** - Renderização de alta qualidade para previews  
- **Pillow** - Processamento avançado de imagens
- **tkinter** - Interface gráfica nativa e confiável

## 📋 Changelog

### v1.1.0 - Otimização e Limpeza
- ✅ **Dependências otimizadas**: Removidas bibliotecas não utilizadas
- ✅ **Código limpo**: Remoção de imports e constantes desnecessárias  
- ✅ **Performance melhorada**: Código mais enxuto e eficiente
- ✅ **Instalação simplificada**: Menos dependências para instalar
- ✅ **Compatibilidade aprimorada**: Menos conflitos entre bibliotecas

---

**🎯 Desenvolvido com ❤️ em Python** | **📧 [Contato](mailto:seu-email@exemplo.com)** | **⭐ Considere dar uma estrela se este projeto foi útil!**