# 📧 Gmail RAG - Semantic Search Your Inbox

A powerful RAG (Retrieval-Augmented Generation) application that enables semantic search and conversational AI interaction with your Gmail inbox using open-source Python libraries.

## 🌟 Features

- **Gmail Integration**: Seamlessly fetch and index emails from your Gmail account
- **Semantic Search**: Find relevant emails using natural language queries
- **Conversational AI**: Chat with your inbox using GPT models
- **Vector Database**: Efficient storage and retrieval using ChromaDB
- **Modern UI**: Clean Streamlit interface for easy interaction
- **Privacy-Focused**: All data stored locally on your machine

## 🏗️ Architecture

- **LangChain**: Orchestration and RAG pipeline
- **ChromaDB**: Vector database for embeddings
- **OpenAI Embeddings**: High-quality text embeddings
- **Gmail API**: Email retrieval
- **Streamlit**: Interactive web interface

## 📋 Prerequisites

- Python 3.8 or higher
- Gmail account
- OpenAI API key
- Google Cloud Console project (for Gmail API)

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd gmail-rag
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials JSON file
5. Rename the downloaded file to `credentials.json` and place it in the project root

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_actual_api_key_here
```

### 5. Index Your Emails

You can index emails using either the CLI script or the web interface:

**Option A: Using CLI**
```bash
python run_indexer.py --max-emails 100
```

**Option B: Using Web Interface**
```bash
streamlit run src/app.py
# Then click "Fetch & Index Emails" in the sidebar
```

The first time you run this, you'll be prompted to authenticate with your Gmail account.

### 6. Start Chatting

```bash
streamlit run src/app.py
```

Navigate to `http://localhost:8501` in your browser and start asking questions about your emails!

## 💡 Usage Examples

### Example Questions

- "What meetings do I have scheduled this week?"
- "Find emails from John about the project proposal"
- "What are the latest updates on the marketing campaign?"
- "Show me emails with attachments from last month"
- "What did Sarah say about the budget?"

### CLI Indexing Options

```bash
# Index maximum 500 emails
python run_indexer.py --max-emails 500

# Force re-indexing (replaces existing database)
python run_indexer.py --force

# Combine options
python run_indexer.py --max-emails 1000 --force
```

## 📁 Project Structure

```
gmail-rag/
├── src/                    # Main application package
│   ├── __init__.py        # Package initializer
│   ├── app.py             # Streamlit web interface
│   ├── index_emails.py    # CLI indexing script
│   ├── gmail_client.py    # Gmail API integration
│   ├── email_processor.py # Email processing and chunking
│   ├── rag_engine.py      # RAG pipeline and vector store
│   └── config.py          # Configuration management
├── run_app.py             # App entry point (alternative)
├── run_indexer.py         # Indexer entry point (alternative)
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## ⚙️ Configuration

Edit [.env](.env) to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `MAX_EMAILS` | Maximum emails to fetch | 500 |
| `LLM_MODEL` | GPT mosrc/config.py](src/| gpt-3.5-turbo |
| `TEMPERATURE` | LLM temperature (0-1) | 0.7 |
| `CHROMA_PERSIST_DIRECTORY` | Vector DB location | ./chroma_db |

Advanced settings in [config.py](config.py):
- `CHUNK_SIZE`: Document chunk size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `TOP_K_RESULTS`: Number of documents to retrieve (default: 5)

## 🔒 Security & Privacy

- **Local Storage**: All email data and embeddings are stored locally
- **API Keys**: Never commit `.env` file or credentials
- **OAuth**: Gmail authentication uses secure OAuth 2.0
- **Credentials**: `credentials.json` and `token.json` are gitignored

## 🐛 Troubleshooting

### "credentials.json not found"
Download OAuth credentials from Google Cloud Console and place in project root.

### "OPENAI_API_KEY is required"
Set your OpenAI API key in the `.env` file.

### "No emails fetched"
- Check your Gmail API is enabled
- Verify OAuth authenticatiorun_indexer
- Check internet connection

### "Vector database empty"
Run indexing first: `python index_emails.py` or use the web interface.

## 🚧 Future Enhancements

- [ ] Support for multiple email accounts
- [ ] Email filtering by date range, sender, labels
- [ ] Export search results
- [ ] Local LLM support (Ollama, LLaMA)
- [ ] Advanced metadata filtering
- [ ] Email summarization
- [ ] Automatic re-indexing on schedule

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For issues and questions, please open a GitHub issue.

---

Built with ❤️ using open-source Python libraries

