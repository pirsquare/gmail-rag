# 📧 Gmail RAG - Semantic Search Your Inbox

A powerful RAG (Retrieval-Augmented Generation) application that enables semantic search and conversational AI interaction with your Gmail inbox using open-source Python libraries.

## 🌟 Features

- **Gmail Integration**: Seamlessly fetch and index emails from your Gmail account
- **Semantic Search**: Find relevant emails using natural language queries
- **Conversational AI**: Chat with your inbox using GPT models
- **🔒 Privacy-Focused**: Local embeddings - email content stays on your machine, only LLM interactions use APIs
- **Vector Database**: Efficient local storage using ChromaDB
- **Modern UI**: Clean Streamlit interface

## 🏗️ Architecture

- **sentence-transformers**: Local embeddings (all-MiniLM-L6-v2) - privacy-first, no external API calls
- **ChromaDB**: Local vector database for fast similarity search
- **OpenAI API**: GPT-4o-mini for answer generation only
- **Gmail API**: Secure email retrieval via OAuth 2.0
- **Streamlit**: Clean web interface for interaction
- **LangChain**: Minimal - only for Document schema and text splitting

### Privacy & Security

- **Local Embeddings**: Email content embedded locally using sentence-transformers (all-MiniLM-L6-v2)
- **Full Email Indexing**: Complete email bodies fetched and indexed for better search results
- **Minimal API Calls**: Only LLM queries + context sent to OpenAI, never email content
- **Local Storage**: Vector database and embeddings stored completely on your machine
- **OAuth 2.0**: Secure Gmail authentication with minimal scopes (read-only)

## 📋 Prerequisites

- Python 3.8+ (3.9-3.11 recommended)
- Gmail account
- OpenAI API key
- Google Cloud Console project (for Gmail API credentials)

### Why Python 3.8-3.11?
Some dependencies (torch, sentence-transformers) have compatibility issues with Python 3.13+. Use 3.9-3.11 for best compatibility.

## 🚀 Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/pirsquare/gmail-rag
cd gmail-rag
pip install -r requirements.txt
```

### 2. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Gmail API (APIs & Services → Library)
4. Create OAuth 2.0 credentials (APIs & Services → Credentials)
   - Application type: Desktop app
   - Download credentials as JSON
5. Rename to `credentials.json` and place in project root

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 4. Index Emails

```bash
python run_indexer.py --max-emails 100
```

First run will prompt Gmail authentication.

### 5. Start Application

```bash
streamlit run src/app.py
```

Visit `http://localhost:8501` and start chatting!

## 💡 Usage

## 💡 Usage Examples

### Example Questions

- "What are the key points from the last email about the project?"
- "Find all emails from John discussing the proposal"
- "What updates have I received about the marketing campaign this week?"
- "Show me emails with important decisions or action items"
- "Summarize the recent conversation with my team"

### How It Works

1. **Indexing Phase**: 
   - Fetches emails from Gmail (full content)
   - Cleans and chunks the text
   - Generates embeddings locally using sentence-transformers
   - Stores vectors in ChromaDB

2. **Query Phase**:
   - Converts your question to embeddings (local)
   - Finds similar emails in ChromaDB
   - Sends context + question to OpenAI
   - Returns answer with source citations

### CLI Options

```bash
# Index first 100 emails
python run_indexer.py --max-emails 100

# Index 500 emails
python run_indexer.py --max-emails 500

# Force re-index existing data
python run_indexer.py --force

# Combine options
python run_indexer.py --max-emails 1000 --force
```

## ⚙️ Configuration

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `MAX_EMAILS` | Maximum emails to fetch | 500 |
| `LLM_MODEL` | GPT model to use | gpt-4o-mini |
| `TEMPERATURE` | LLM temperature (0-1) | 0.7 |
| `CHROMA_PERSIST_DIRECTORY` | Vector DB location | ./chroma_db |

Advanced settings in [src/config.py](src/config.py):
- `CHUNK_SIZE`: Document chunk size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `TOP_K_RESULTS`: Number of documents to retrieve (default: 5)

## 🔒 Security & Privacy

- **Local Storage**: All email data and embeddings stored on your machine
- **Local Embeddings**: Sentence-transformers (no external API calls)
- **Minimal External Calls**: Only LLM interactions use OpenAI API
- **OAuth Security**: Gmail authentication via secure OAuth 2.0
- **Credentials**: Never commit `.env`, `credentials.json`, or `token.json`

### Data Flow

```
Gmail → Local Storage → Local Embeddings → ChromaDB (Local)
                                              ↓
                                    Local Similarity Search
                                              ↓
                             Retrieved Context → OpenAI LLM → Response
```

For complete privacy details, see [PRIVACY.md](PRIVACY.md).

## 🐛 Troubleshooting

### "credentials.json not found"
Download OAuth credentials from Google Cloud Console and place in project root.

### "OPENAI_API_KEY is required"
Set your OpenAI API key in the `.env` file.

### "No emails fetched"
- Verify Gmail API is enabled in Google Cloud Console
- Check OAuth authentication succeeded
- Ensure internet connection is active

### "Vector database empty"
Run indexing first: `python run_indexer.py` or use the web interface.

## 🚧 Future Enhancements

- [ ] Local LLM support (Ollama, LLaMA, Mistral)
- [ ] Multiple email account support
- [ ] Date range and sender filtering
- [ ] Export search results
- [ ] GPU acceleration for embeddings
- [ ] Email summarization
- [ ] Automatic re-indexing scheduler

## 📝 License

See [LICENSE](LICENSE) file for details.

---

Built with ❤️ using open-source Python libraries


