---
inclusion: always
---

# Product Overview

WhatsApp PDF Knowledge Bot is a local PDF search tool that indexes and searches PDF documents. It extracts text content from PDFs (first few pages), stores metadata in a JSON index, and provides simple keyword-based search functionality.

## Core Features

- Index PDF files recursively from a specified folder
- Extract text from first N pages of each PDF (default: 3 pages, max 4000 chars)
- Store searchable index with metadata (filename, path, modified date, size)
- Search indexed PDFs using keyword matching with ranked results
- Display search results with snippets highlighting query terms

## Default Behavior

- Default scan location: ~/Downloads or current directory
- Index storage: ./data/index.json
- Text extraction limited to keep index size manageable
