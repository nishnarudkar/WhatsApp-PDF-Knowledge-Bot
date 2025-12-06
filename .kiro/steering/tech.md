---
inclusion: always
---

# Technology Stack

## Language & Runtime

- Python 3.x
- Standard library modules: argparse, json, pathlib, datetime

## Dependencies

- PyPDF2 (>=3.0.0) - PDF text extraction

## Project Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

## Common Commands

Index PDFs in a folder:
```bash
python src/whatsapp_pdf_bot.py index --folder /path/to/pdfs
```

Search indexed PDFs:
```bash
python src/whatsapp_pdf_bot.py search "your query here"
```

Custom index location:
```bash
python src/whatsapp_pdf_bot.py index --folder /path/to/pdfs --index-path ./custom/index.json
python src/whatsapp_pdf_bot.py search "query" --index-path ./custom/index.json
```

Adjust pages to index:
```bash
python src/whatsapp_pdf_bot.py index --folder /path/to/pdfs --max-pages 5
```

## Build System

No build system required - pure Python script execution.
