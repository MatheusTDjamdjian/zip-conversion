# Zip Conversion

Projeto completo: site + backend para conversão de arquivos (imagens, vídeos, documentos) e download em um único arquivo `.zip`.

## Requisitos
- Node.js 18+ (testado com Node 18/20)
- ffmpeg (on PATH)
- libreoffice (for document conversion) — on PATH
- Sistema operacional: Linux / macOS / Windows (com ffmpeg & libreoffice instalados)

## Instalação

1. Clone ou copie o repositório.
2. Instale dependências do backend:

```bash
cd zip-conversion/backend
npm install