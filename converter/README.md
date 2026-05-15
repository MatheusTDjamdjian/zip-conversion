# converter

[![Licença: MIT](https://img.shields.io/badge/licença-MIT-success.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Testes](https://img.shields.io/badge/testes-54%20passando-brightgreen.svg)](#testes)
[![Cobertura](https://img.shields.io/badge/cobertura-85%25-brightgreen.svg)](#testes)

Ferramenta leve e portátil para conversão de arquivos — **imagens**, **documentos** e **PDFs** — com duas interfaces: uma **CLI** robusta para automação e uma **interface web local** com design moderno para uso casual. Tudo roda **na sua máquina**, sem subir nada para a nuvem.

```
┌────────────────────────────────────────────────────┐
│  CLI       python -m converter foto.png foto.webp  │
│  Web       python -m converter.web                 │
│  Lote      python -m converter --batch in/ out/ \  │
│                                  --to webp         │
└────────────────────────────────────────────────────┘
```

---

## Sumário

- [Recursos](#recursos)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Uso da CLI](#uso-da-cli)
- [Interface web local](#interface-web-local)
- [Formatos suportados](#formatos-suportados)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Testes](#testes)
- [Como contribuir](#como-contribuir)
- [Justificativa das dependências](#justificativa-das-dependências)
- [Limitações conhecidas](#limitações-conhecidas)
- [Licença](#licença)

---

## Recursos

- **Imagens**: PNG ↔ JPG/JPEG ↔ WEBP ↔ BMP ↔ GIF ↔ TIFF (via Pillow).
- **Documentos**: DOCX → PDF, TXT → PDF e PDF → imagens (uma por página).
- **Dois modos** na CLI: arquivo único ou pasta inteira (`--batch`), com opção recursiva.
- **Interface web local**: drag-and-drop, glassmorphism, dark/light automático.
- **Opções práticas**: qualidade (`--quality`), redimensionamento (`--resize`), modo silencioso (`--quiet`), verboso (`--verbose`), proteção contra sobrescrita (`--no-overwrite`).
- **Detecção automática** do formato pela extensão.
- **Mensagens em português** — claras e acionáveis (dizem o que fazer, não só o que falhou).
- **Multiplataforma**: Linux, macOS e Windows sem alterações.
- **Arquitetura plugável**: novos formatos são uma classe que herda de `BaseConverter`, sem mexer no núcleo.
- **Zero servidor externo**: não precisa de Docker, Poppler, Ghostscript, LibreOffice nem banco de dados.

## Pré-requisitos

- **Python 3.10** ou superior.
- **pip** disponível no ambiente (no Windows, costuma ser invocado como `python -m pip`).

## Instalação

Clone o repositório e instale as dependências em um ambiente virtual isolado.

### Linux / macOS

```bash
git clone <url-do-repositorio>
cd converter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows (PowerShell)

```powershell
git clone <url-do-repositorio>
Set-Location converter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Verifique a instalação:

```bash
python -m converter --help
```

---

## Uso da CLI

A ferramenta detecta o formato de origem e destino pela **extensão** dos arquivos. Basta passar entrada e saída.

### 1. Conversão simples

```bash
python -m converter foto.png foto.webp
```

### 2. Ajustar qualidade de JPEG/WEBP

```bash
python -m converter --quality 90 foto.jpg foto.webp
```

Qualidade é um inteiro de 1 a 100 (padrão: 85). Vale apenas para formatos com compressão lossy (JPEG/WEBP).

### 3. Redimensionar imagens

```bash
python -m converter --resize 1920x1080 foto.png foto_hd.png
```

Aplica-se também à renderização de PDF → imagem.

### 4. Conversão em lote

Converte todos os arquivos suportados de uma pasta para um formato-alvo:

```bash
python -m converter --batch ./entrada ./saida --to webp
```

Pastas mistas são tratadas com graça: arquivos não suportados são **pulados com aviso**, os demais são convertidos. Uma barra de progresso é mostrada quando o terminal é interativo.

### 5. Lote recursivo

```bash
python -m converter --batch ./pdfs ./imagens --to png --recursive
```

### 6. Documentos

```bash
python -m converter relatorio.docx relatorio.pdf
python -m converter anotacoes.txt anotacoes.pdf
python -m converter relatorio.pdf paginas.png
```

Para PDFs com múltiplas páginas, cada página vira um arquivo com sufixo `_pagina_NNN.png` no mesmo diretório de saída.

### 7. Verbosidade

```bash
python -m converter foto.png foto.webp --verbose   # logs DEBUG detalhados
python -m converter foto.png foto.webp --quiet     # apenas avisos/erros
```

### 8. Listar formatos suportados

```bash
python -m converter --list-formats
```

### 9. Não sobrescrever arquivos existentes

```bash
python -m converter foto.png foto.webp --no-overwrite
```

### Códigos de saída

| Código | Significado                                                |
|--------|------------------------------------------------------------|
| `0`    | Sucesso                                                    |
| `1`    | Erro de conversão (formato, arquivo, permissão)            |
| `2`    | Lote concluído, mas com falhas em alguns arquivos          |
| `3`    | Lote sem nada convertido (todos os arquivos eram inválidos)|

Úteis para scripts e CI.

---

## Interface web local

Se preferir não usar o terminal — ou quiser uma experiência mais visual — suba o servidor web embutido:

```bash
python -m converter.web
```

O navegador abre automaticamente em `http://localhost:5000`. Lá você:

1. **Arrasta** um arquivo (ou clica para selecionar).
2. **Escolhe** o formato de destino.
3. **(Opcional)** ajusta qualidade e redimensionamento em "Opções avançadas".
4. Clica em **Converter e baixar** — o resultado vem direto.

Conversões que geram múltiplos arquivos (ex.: PDF com várias páginas → PNG) são empacotadas automaticamente em um `.zip`.

### Design

A interface usa um visual moderno com:

- Tema escuro com aurora animada (gradientes mesh em movimento) e grain sutil.
- Card glassmorphic com `backdrop-filter` e borda em gradiente.
- Tipografia Inter + JetBrains Mono.
- Drag-and-drop com preview de nome e tamanho do arquivo.
- Estado de loading no botão durante a conversão.
- Suporte automático a tema claro via `prefers-color-scheme`.
- Acessibilidade: respeita `prefers-reduced-motion`.

### Opções do servidor

```bash
python -m converter.web --port 8080            # porta alternativa
python -m converter.web --no-browser           # não abre o navegador
python -m converter.web --host 0.0.0.0         # expor na rede local (cuidado)
python -m converter.web --max-upload-mb 256    # limite de upload
```

> ⚠️ **Aviso de segurança**: o servidor web é projetado para **uso local/pessoal**. Ele não tem autenticação, rate-limit, varredura de arquivos maliciosos nem isolamento adequado para internet pública. **Não exponha** a porta em redes não confiáveis.

---

## Formatos suportados

| Origem      | Destinos possíveis                                        |
|-------------|-----------------------------------------------------------|
| **PNG**     | JPG, JPEG, WEBP, BMP, GIF, TIFF                           |
| **JPG/JPEG**| PNG, WEBP, BMP, GIF, TIFF                                 |
| **WEBP**    | PNG, JPG, JPEG, BMP, GIF, TIFF                            |
| **BMP**     | PNG, JPG, JPEG, WEBP, GIF, TIFF                           |
| **GIF**     | PNG, JPG, JPEG, WEBP, BMP, TIFF (primeiro frame apenas)   |
| **TIFF/TIF**| PNG, JPG, JPEG, WEBP, BMP, GIF                            |
| **PDF**     | PNG, JPG, JPEG, WEBP, BMP, TIFF (uma imagem por página)   |
| **TXT**     | PDF                                                       |
| **DOCX**    | PDF                                                       |

---

## Estrutura do projeto

```
converter/
├── converter/                  # Pacote principal
│   ├── __init__.py             # Metadados (versão, autor, licença)
│   ├── __main__.py             # Entry point: python -m converter
│   ├── cli.py                  # Parser argparse e roteamento da CLI
│   ├── core.py                 # ConversionEngine + registro de conversores
│   ├── exceptions.py           # Exceções customizadas em português
│   ├── utils.py                # Logging, validação, barra de progresso
│   ├── converters/             # Implementações por formato
│   │   ├── __init__.py
│   │   ├── base.py             # BaseConverter + ConversionOptions
│   │   ├── image.py            # Imagens (Pillow)
│   │   ├── pdf.py              # PDF → imagens (pypdf + Pillow)
│   │   └── document.py         # DOCX/TXT → PDF (escritor PDF próprio)
│   └── web/                    # Interface web
│       ├── __init__.py
│       ├── __main__.py         # Entry point: python -m converter.web
│       ├── app.py              # Aplicação Flask
│       └── templates/
│           └── index.html      # UI moderna com drag-and-drop
├── tests/                      # Suíte de testes pytest
│   ├── conftest.py             # Fixtures (arquivos gerados em runtime)
│   ├── test_image.py
│   ├── test_pdf.py
│   ├── test_cli.py
│   ├── test_web.py
│   └── fixtures/
├── requirements.txt            # Dependências runtime
├── pyproject.toml              # Metadados + config de Black/Ruff/pytest
├── README.md                   # Este arquivo
├── LICENSE                     # MIT
└── .gitignore
```

---

## Testes

A suíte cobre conversão de imagens, PDFs, documentos, CLI e a interface web.

```bash
# Rodar todos os testes
python -m pytest

# Com relatório de cobertura
python -m pytest --cov=converter --cov-report=term-missing

# Apenas um módulo
python -m pytest tests/test_image.py -v
```

**Status atual**: 54 testes, 85% de cobertura (incluindo branches).

Os arquivos de fixture (PNGs, DOCX, etc.) são gerados em runtime, mantendo o repositório enxuto.

---

## Como contribuir

### 1. Rodar testes e linters antes de subir

```bash
python -m pytest                  # Testes
python -m ruff check .            # Linter
python -m black --check .         # Formatação
```

Para auto-corrigir formatação e import sort:

```bash
python -m ruff check . --fix
python -m black .
```

### 2. Padrão de commits

Recomendado [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

- `feat: adiciona suporte a HEIC`
- `fix: corrige tratamento de PDF protegido por senha`
- `docs: amplia exemplos de uso no README`
- `test: cobre cenário de pasta vazia no modo batch`
- `refactor: extrai writer de PDF para módulo próprio`

### 3. Adicionar um novo formato

Esse é o caminho mais comum — a arquitetura foi pensada para isso ser **rápido**:

1. Crie `converter/converters/<formato>.py` com uma classe que herde de `BaseConverter`.
2. Declare `source_formats` e `target_formats` (frozenset de extensões em minúsculas, sem ponto).
3. Implemente `convert(input_path, output_path, options)`.
4. Registre a classe em `build_default_engine()` em `converter/core.py`.
5. Crie testes em `tests/test_<formato>.py`.

Exemplo mínimo:

```python
from .base import BaseConverter, ConversionOptions
from pathlib import Path

class MeuConversor(BaseConverter):
    source_formats = frozenset({"foo"})
    target_formats = frozenset({"bar"})

    def convert(self, input_path: Path, output_path: Path,
                options: ConversionOptions) -> Path:
        # ... sua lógica aqui ...
        return output_path
```

### 4. Convenções de código

- **Type hints** em tudo que for público.
- **Docstrings** Google/NumPy em módulos e funções públicas.
- **Sem `except:` genérico** — use exceções específicas e levante `ConversionError` com mensagem em português quando falhar.
- **`pathlib.Path`** em vez de strings para caminhos.
- **`logging`** em vez de `print` para mensagens de status (exceto saída final para o usuário na CLI).
- **Linha de 100 caracteres** (configurado no `pyproject.toml`).

---

## Justificativa das dependências

Mantemos a lista de dependências o mais curta possível. Cada uma tem uma razão:

| Dependência     | Por quê                                                                                              |
|-----------------|------------------------------------------------------------------------------------------------------|
| **Pillow**      | Decodificadores/encodificadores maduros para todos os formatos de imagem. Reimplementar seria caro.  |
| **pypdf**       | Leitura de PDF em Python puro, sem depender de Poppler/Ghostscript. Mantém a ferramenta portátil.    |
| **python-docx** | Parser do `.docx` (que é um ZIP de XML). Reimplementar daria muito trabalho e seria frágil.          |
| **Flask**       | Micro-framework usado apenas pela interface web opcional. Pequeno, sem servidor externo, com Jinja2. |

**Tudo o mais é biblioteca padrão** — `argparse`, `logging`, `pathlib`, `zipfile`, `tempfile`, `zlib`. A geração de PDF (TXT/DOCX → PDF) é feita à mão com `zlib`, sem ReportLab nem WeasyPrint. A barra de progresso é manual também, sem `tqdm`.

---

## Limitações conhecidas

Ser honesto sobre o que **não** funciona é tão importante quanto listar o que funciona.

- **DOCX → PDF**: extrai apenas o texto dos parágrafos, em fonte Helvetica de tamanho fixo. Formatação rica (estilos, tabelas complexas, imagens, cabeçalhos/rodapés) é **descartada**. Para preservar fidelidade visual, pós-processe com LibreOffice headless (`soffice --convert-to pdf`).
- **PDF → imagens**: como não dependemos de Poppler/Ghostscript, a renderização é simplificada — mostra o texto extraído da página com um cabeçalho identificador. **Não reproduz** layout original, vetores ou imagens incorporadas.
- **GIF animado**: salva apenas o primeiro frame. Animações não são preservadas.
- **Formatos não suportados**: HEIC, RAW de câmeras, vídeo, áudio, ODT, RTF, PSD, AI, SVG.
- **Sem paralelismo**: a conversão em lote é sequencial. Para milhares de arquivos, paralelize externamente (`GNU parallel`, `xargs -P`).
- **Interface web**: sem autenticação, sem rate-limit, sem isolamento entre uploads. Foi pensada para uso local/pessoal — **não exponha** na internet pública.
- **Senhas em PDFs**: PDFs criptografados não são suportados. Remova a proteção antes (`qpdf --decrypt`).

---

## Licença

Distribuído sob a [MIT License](LICENSE). Sinta-se livre para usar, modificar e distribuir.

---

<sub>Feito em Python com foco em **baixa fricção** — instala em 30 segundos, roda em qualquer sistema, sem surpresas.</sub>
