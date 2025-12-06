---
inclusion: always
---

# Project Structure

```
.
├── data/              # Default location for index.json storage
├── src/               # Source code
│   └── whatsapp_pdf_bot.py  # Main application entry point
└── requirements.txt   # Python dependencies
```

## Code Organization

### Main Module: `src/whatsapp_pdf_bot.py`

Single-file application with clear functional separation:

- **PDF Processing**: `extract_pdf_text()` - Extract text from PDF pages
- **Indexing**: `build_index()` - Scan folder and create searchable index
- **Search**: `search_index()` - Query index and rank results
- **Utilities**: `build_snippet()`, `load_index()`, `get_default_paths()`
- **CLI**: `main()` - Argument parsing and command routing

## Conventions

- Type hints used for function signatures
- Docstrings for public functions
- Path handling via `pathlib.Path`
- Error handling with try/except and informative messages
- Logging-style print statements with prefixes: `[INFO]`, `[WARN]`, `[ERROR]`, `[DONE]`
- Constants defined at module level (e.g., `INDEX_VERSION`)

## Data Storage

- Index stored as JSON in `./data/index.json` by default
- Index structure includes version, timestamp, root folder, and document list
- Each document entry contains: filename, path, modified date, size, preview, and searchable content
