#  WhatsApp PDF Knowledge Bot

> **"I hate searching old WhatsApp PDFs, so I built this."**

A smart, offline, Python-based knowledge bot that turns your messy WhatsApp & Downloads PDFs into a **searchable, analyzable, and organized knowledge base**.

Built as part of **AI for Bharat – Week 2: Lazy Automation** | Powered by **Python + Kiro**

---

##  What This Project Does

This tool:

 **Indexes all PDFs** from your WhatsApp / Downloads folder  
 **Extracts text** from PDFs automatically  
 **Searches instantly** using keywords  
 **Auto-tags subjects** (ML, Neural Networks, DBMS, DSA, etc.)  
 **Interactive chat-style mode** for quick searches  
 **Detects duplicate PDFs** based on content  
 **Shows analytics & insights** about your study material  
 **Exports search results** to CSV / TXT  
 **Works completely offline**  
 **Menu system** (no command memorization needed)  
 **Colored terminal output** for better readability  

---

##  Why This Exists (The Problem)

Engineering students receive hundreds of PDFs via:
- WhatsApp
- Telegram  
- Google Drive
- Email

After a few months:
- File names are forgotten
- PDFs are duplicated
- Notes are scattered
- Searching manually is painful

So instead of opening 30 PDFs during exams… I built a **local knowledge bot** 

---

##  Project Structure

```
whatsapp-pdf-knowledge-bot/
├── .kiro/                    # Kiro metadata
├── src/
│   └── whatsapp_pdf_bot.py   # Main application
├── data/
│   └── index.json            # Auto-generated search index
├── exports/                  # Exported CSV/TXT files (auto-created)
├── README.md
├── requirements.txt
└── LICENSE
```

---

##  Features Explained

###  1. Smart PDF Indexing

Scans your WhatsApp / Downloads folder and extracts:
- File name
- Full path
- Modified date
- File size
- Page text (first 3 pages by default)
- Subject category
- Content hash (for duplicate detection)

```bash
python src/whatsapp_pdf_bot.py index --folder "C:\Users\YourName\Downloads"
```

---

###  2. Smart Subject Auto-Tagging

Each PDF is automatically classified into:
- **Machine Learning**
- **Neural Networks**
- **DBMS**
- **Data Structures & Algorithms**
- **Probability & Statistics**
- **Unknown**

Classification is based on keyword matching in the PDF content.

---

###  3. Instant Keyword Search

```bash
python src/whatsapp_pdf_bot.py search "neural networks"
```

Shows:
- File name
- Full path
- Subject
- Modified date
- File size
- Highlighted snippet

**Advanced search with filters:**

```bash
# Search with date range
python src/whatsapp_pdf_bot.py search "machine learning" --since 2024-01-01 --until 2024-12-31

# Search by file size
python src/whatsapp_pdf_bot.py search "dbms" --min-size-kb 100 --max-size-kb 5000

# Limit results
python src/whatsapp_pdf_bot.py search "probability" --top-k 10
```

---

###  4. Interactive Search Mode (Chat Style)

```bash
python src/whatsapp_pdf_bot.py interactive
```

Then type:
```
>> neural networks
>> unit 3 probability
>> dbms normalization
>> exit
```

---

###  5. Duplicate PDF Detector

```bash
python src/whatsapp_pdf_bot.py dups
```

Finds same/similar PDFs saved multiple times with different names using content hash comparison.

---

###  6. Export Search Results (CSV / TXT)

```bash
# Export to CSV
python src/whatsapp_pdf_bot.py search "machine learning" --export exports/ml_results.csv

# Export to TXT
python src/whatsapp_pdf_bot.py search "probability" --export exports/probability.txt
```

---

###  7. Analytics & Insights Mode

```bash
python src/whatsapp_pdf_bot.py stats
```

Shows:
- Total PDFs
- Total size
- Average file size
- Oldest and newest files
- Top 5 folders by document count
- Subject distribution
- Top 10 frequent words across all documents

---

###  8. Simple Menu Mode (No Commands Needed)

Just run:
```bash
python src/whatsapp_pdf_bot.py
```

You'll see:
```
1) Index PDFs
2) Search PDFs
3) Interactive Search
4) Show Stats
5) Find Duplicates
6) Exit
```

Perfect for non-technical users too 

---

##  Installation

### 1. Clone the Repo

```bash
git clone https://github.com/nishnarudkar/WhatsApp-PDF-Knowledge-Bot.git
cd Whatsapp-PDF-Knowledge-bot
```

### 2. Create and Activate Virtual Environment (Recommended)

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
PyPDF2>=3.0.0
colorama>=0.4.6
```

---

##  How to Use

###  Index Your PDFs (Once)

```bash
python src/whatsapp_pdf_bot.py index --folder "C:\Users\YourName\Downloads"
```

###  Search

```bash
python src/whatsapp_pdf_bot.py search "neural networks"
```

###  Show Stats

```bash
python src/whatsapp_pdf_bot.py stats
```

###  Detect Duplicates

```bash
python src/whatsapp_pdf_bot.py dups
```

###  Interactive Mode

```bash
python src/whatsapp_pdf_bot.py interactive
```

###  Menu Mode (Easiest)

```bash
python src/whatsapp_pdf_bot.py
```

---

##  Built with Kiro

Kiro helped in:
- Designing the CLI architecture
- PDF extraction logic
- Error handling
- Feature expansion
- Documentation
- Debugging during development

This project was built as part of **AI for Bharat – Lazy Automation Week**.

---

##  Future Enhancements

- [ ] Semantic search using embeddings
- [ ] Web-based UI (Flask / FastAPI)
- [ ] Live WhatsApp folder watcher
- [ ] Support for .docx and .pptx
- [ ] Cloud sync (S3 / Drive)

---

##  GitHub Repo

 https://github.com/nishnarudkar/WhatsApp-PDF-Knowledge-Bot

---

##  Final Note

This project is not just a script — it's a **real productivity tool** that turns unstructured PDF chaos into a searchable personal knowledge system.

If you're a student drowning in notes… **This bot is your academic life-saver.** 🚀

---

##  License

MIT License - feel free to use and modify!

---

**Made with ❤️ by [Nishant Narudkar]**
