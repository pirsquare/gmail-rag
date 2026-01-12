# Quick Start Guide

## Running the Application

### Method 1: Direct Streamlit (Recommended)
```bash
streamlit run src/app.py
```

### Method 2: Using wrapper script
```bash
python run_app.py
```

## Indexing Emails

### Method 1: Direct Python module
```bash
python -m src.index_emails --max-emails 100
```

### Method 2: Using wrapper script
```bash
python run_indexer.py --max-emails 100
```

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Index 500 emails
python run_indexer.py --max-emails 500

# Force re-index
python run_indexer.py --force

# Run the web app
streamlit run src/app.py
```

## Project Structure

```
gmail-rag/
├── src/                    # All application code
│   ├── app.py             # Streamlit interface
│   ├── index_emails.py    # CLI indexer
│   ├── gmail_client.py    # Gmail API
│   ├── email_processor.py # Email processing
│   ├── rag_engine.py      # RAG pipeline
│   └── config.py          # Configuration
├── run_app.py             # App launcher
├── run_indexer.py         # Indexer launcher
└── requirements.txt       # Dependencies
```
