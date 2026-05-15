# converter

[![Licença: MIT](https://img.shields.io/badge/licença-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

Ferramenta CLI leve e portátil para conversão de arquivos — imagens, documentos
e PDFs — com mínimas dependências externas e zero configuração. Funciona em
Linux, macOS e Windows, sem Docker, sem servidores, sem banco de dados.

## Recursos

- Conversão de imagens entre PNG, JPG/JPEG, WEBP, BMP, GIF e TIFF.
- Conversão de documentos: DOCX → PDF, TXT → PDF e PDF → imagens (uma por página).
- Modo arquivo único e modo de conversão em lote (pasta inteira), com opção
  recursiva.
- Opções práticas: qualidade (`--quality`), redimensionamento (`--resize`),
  modo silencioso (`--quiet`) e verboso (`--verbose`).
- Detecção automática do formato pela extensão.
- Mensagens de erro em português, claras e acionáveis.
- Barra de progresso simples no modo lote, sem dependências extras.
- Arquitetura plugável: novos formatos viram uma classe que herda de
  `BaseConverter`, sem alterar o núcleo.
- **Interface web local opcional** (`python -m converter.web`) com formulário
  de upload no navegador — não precisa abrir o terminal.

## Pré-requisitos

- Python **3.10** ou superior.
- `pip` disponível no ambiente.

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
cd converter
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Verifique a instalação:

```bash
python -m converter --help
```

## Uso

A ferramenta detecta o formato de origem e destino pela **extensão** dos
arquivos. Basta passar o arquivo de entrada e o arquivo de saída desejado.

### 1. Conversão simples (arquivo único)

```bash
python -m converter foto.png foto.webp
```

### 2. Ajustar qualidade de JPEG/WEBP

```bash
python -m converter --quality 90 foto.jpg foto.webp
```

A qualidade é um inteiro de 1 a 100 (padrão: 85). Vale apenas para formatos
com compressão lossy (JPEG e WEBP).

### 3. Redimensionar imagens

```bash
python -m converter --resize 1920x1080 foto.png foto_hd.png
```

O formato é `LARGURAxALTURA`. Aplica-se a imagens (e também à renderização de
PDF → imagem).

### 4. Conversão em lote

Converte todos os arquivos suportados de uma pasta para um formato-alvo:

```bash
python -m converter --batch ./entrada ./saida --to webp
```

Pastas mistas são tratadas com graça: arquivos não suportados são pulados com
aviso, e os demais são convertidos.

### 5. Lote recursivo

Inclui subpastas:

```bash
python -m converter --batch ./pdfs ./imagens --to png --recursive
```

### 6. Documentos

```bash
python -m converter relatorio.docx relatorio.pdf
python -m converter anotacoes.txt anotacoes.pdf
python -m converter relatorio.pdf paginas.png
```

Para PDFs com múltiplas páginas, cada página vira um arquivo com sufixo
`_pagina_NNN.png` no mesmo diretório.

### 7. Modos de verbosidade

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

## Interface web local

Se preferir não usar o terminal, suba o servidor web embutido:

```bash
python -m converter.web
```

O comando abre o navegador automaticamente em `http://localhost:5000`. Lá
você escolhe o arquivo, o formato de destino e (opcionalmente) qualidade e
redimensionamento. O resultado é baixado direto — nada é enviado para a
internet, tudo roda na sua máquina.

Opções úteis:

```bash
python -m converter.web --port 8080            # porta alternativa
python -m converter.web --no-browser           # não abrir o navegador
python -m converter.web --host 0.0.0.0         # expor na rede local (cuidado)
python -m converter.web --max-upload-mb 256    # aumentar limite de upload
```

> **Atenção:** o servidor é apenas para uso local/pessoal. Não exponha a
> porta na internet pública — ele não tem autenticação, rate-limit, varredura
> de arquivos maliciosos nem isolamento adequado para esse cenário.

Conversões que geram múltiplos arquivos (ex.: PDF de várias páginas para
PNG) são empacotadas automaticamente em um `.zip`.

## Formatos suportados

| Origem | Destinos possíveis                                      |
|--------|---------------------------------------------------------|
| PNG    | JPG, JPEG, WEBP, BMP, GIF, TIFF                         |
| JPG/JPEG | PNG, WEBP, BMP, GIF, TIFF                             |
| WEBP   | PNG, JPG, JPEG, BMP, GIF, TIFF                          |
| BMP    | PNG, JPG, JPEG, WEBP, GIF, TIFF                         |
| GIF    | PNG, JPG, JPEG, WEBP, BMP, TIFF                         |
| TIFF/TIF | PNG, JPG, JPEG, WEBP, BMP, GIF                        |
| PDF    | PNG, JPG, JPEG, WEBP, BMP, TIFF (uma imagem por página) |
| TXT    | PDF                                                     |
| DOCX   | PDF                                                     |

## Estrutura do projeto

```
converter/
├── converter/
│   ├── __init__.py           # metadados do pacote
│   ├── __main__.py           # ponto de entrada para `python -m converter`
│   ├── cli.py                # parser argparse e roteamento da CLI
│   ├── core.py               # orquestrador e registro de conversores
│   ├── exceptions.py         # exceções customizadas em português
│   ├── utils.py              # logging, validação, barra de progresso
│   ├── converters/
│   │   ├── __init__.py
│   │   ├── base.py           # protocolo BaseConverter + ConversionOptions
│   │   ├── image.py          # imagens (Pillow)
│   │   ├── pdf.py            # PDF → imagens (pypdf + Pillow)
│   │   └── document.py       # DOCX/TXT → PDF (escritor PDF próprio)
│   └── web/
│       ├── __init__.py
│       ├── __main__.py       # entry point: python -m converter.web
│       ├── app.py            # aplicação Flask (formulário + endpoint)
│       └── templates/
│           └── index.html
├── tests/
│   ├── conftest.py           # fixtures (geram arquivos pequenos em runtime)
│   ├── test_image.py
│   ├── test_pdf.py
│   ├── test_cli.py
│   └── test_web.py
├── requirements.txt
├── pyproject.toml            # metadados + configuração de Black/Ruff/pytest
├── README.md
├── LICENSE
└── .gitignore
```

## Como contribuir

1. **Rodar os testes**

   ```bash
   python -m pytest --cov=converter --cov-report=term-missing
   ```

2. **Formatar e checar o código**

   ```bash
   python -m black .
   python -m ruff check .
   ```

3. **Padrão de commits sugerido**: [Conventional Commits](https://www.conventionalcommits.org/pt-br/).
   Exemplos:

   - `feat: adiciona suporte a HEIC`
   - `fix: corrige tratamento de PDF protegido por senha`
   - `docs: amplia exemplos de uso no README`
   - `test: cobre cenário de pasta vazia no modo batch`

4. **Adicionar um novo formato** é simples:

   - Crie uma classe em `converter/converters/<seu_formato>.py` que herde de
     `BaseConverter`, declare `source_formats` e `target_formats` e implemente
     `convert(...)`.
   - Registre-a em `build_default_engine()` em `converter/core.py`.
   - Escreva testes em `tests/test_<seu_formato>.py`.

## Justificativa das dependências

- **Pillow** — abertura, manipulação e salvamento de praticamente todos os
  formatos de imagem suportados. Sem ela, teríamos de reimplementar
  codificadores e decodificadores complexos.
- **pypdf** — leitura de PDFs em Python puro, sem dependência de Poppler ou
  Ghostscript. Mantém a ferramenta portátil em Windows/macOS/Linux sem
  ferramentas nativas extras.
- **python-docx** — leitura de arquivos `.docx`, que internamente são ZIP de
  XML. Reimplementar o parser seria caro e frágil.
- **Flask** — micro-framework usado apenas pela interface web opcional. É
  pequeno e roda sem servidor externo. Se você só usa a CLI, ele fica
  ocioso (mas continua instalado).

A geração de PDF (TXT/DOCX → PDF) é feita pela biblioteca padrão (`zlib`), sem
ReportLab ou WeasyPrint, para evitar dependências pesadas. A barra de
progresso também é implementada à mão, sem `tqdm`.

## Limitações conhecidas

- **DOCX → PDF**: extrai apenas o texto dos parágrafos, em fonte Helvetica de
  tamanho fixo. Formatação rica (estilos, tabelas complexas, imagens, cabeçalhos
  e rodapés) é descartada. Para preservar fidelidade visual, recomenda-se
  pós-processar com LibreOffice em modo headless.
- **PDF → imagens**: como não dependemos de Poppler/Ghostscript, a renderização
  é uma versão simplificada que mostra o texto extraído da página com um
  cabeçalho identificador. Não reproduz layout, vetores ou imagens originais.
- **GIF animado**: salva apenas o primeiro frame; a ferramenta não preserva
  animações.
- **Não suporta**: HEIC, RAW de câmeras, vídeo, áudio, ODT, RTF e formatos
  proprietários como PSD/AI.
- **Sem paralelismo**: a conversão em lote é sequencial. Para milhares de
  arquivos, considere paralelizar em camada superior.
- **Interface web**: foi pensada para uso local. Não tem login, rate-limit
  nem isolamento entre usuários — não exponha na internet pública.

## Licença

[MIT](LICENSE) — sinta-se livre para usar, modificar e distribuir.
