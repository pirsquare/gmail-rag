# 📧 Gmail RAG - LlamaIndex-Powered Inbox Agent

A powerful RAG application with **LlamaIndex agent framework** that enables intelligent email management through natural language. Search emails, triage urgent messages, summarize threads, and draft replies using either OpenAI or local LLMs (Ollama).

## 🌟 Features

- **LlamaIndex Agent Framework**: Intelligent tool routing with ReAct agent
- **4 Specialized Tools**:
  - 🔍 **search_emails**: Semantic search with full citations
  - 🧵 **get_thread**: Retrieve complete email threads
  - 📥 **triage_recent**: Find emails needing replies (ranked by urgency)
  - ✍️ **draft_reply**: Generate reply drafts (never auto-sends)
- **Flexible LLM Backend**: 
  - ☁️ OpenAI (gpt-4o-mini) - cloud-based
  - 🖥️ Ollama (llama3.2, mistral, etc.) - 100% local
- **🔒 Privacy-Focused**: Local embeddings - emails stay on your machine
- **Thread-Aware**: Intelligent grouping by Gmail thread IDs
- **Citation-First**: Every response includes subject, sender, date, message_id, thread_id

## 🏗️ Architecture

### LlamaIndex Agent Stack

```
Streamlit UI (app.py)
    ↓
GmailAgent (LlamaIndex ReActAgent)
    ├─ System Prompt (strict citation policy)
    ├─ Tool Router (automatic tool selection)
    └─ 4 Tools:
        ├─ EmailSearchTool → RAGEngine.semantic_search()
        ├─ ThreadTool → ChromaDB (thread_id filter)
        ├─ TriageTool → Keyword analysis + urgency scoring
        └─ DraftTool → LLM generation (draft-only)
    ↓
RAGEngine (vector search + LLM calls)
    ↓
ChromaDB (local vectors) + sentence-transformers
```

### Core Components

- **LlamaIndex**: Agent framework with ReAct reasoning, tool calling
- **sentence-transformers**: Local embeddings (all-MiniLM-L6-v2) - 384 dims, ~80MB
- **ChromaDB**: Local vector database with metadata filtering
- **OpenAI / Ollama**: LLM for agent reasoning and draft generation
- **Gmail API**: OAuth 2.0 read-only access
- **Streamlit**: Interactive chat interface

### Privacy & Security

- **Local Embeddings**: Email content embedded locally using sentence-transformers (all-MiniLM-L6-v2)
- **Full Email Indexing**: Complete email bodies (HTML→text) fetched and indexed
- **Minimal API Calls**: Only agent queries + context sent to LLM (OpenAI or local Ollama)
- **Local Storage**: Vector database stored in `./chroma_db/`
- **OAuth 2.0**: Gmail read-only scope
- **Draft Only**: Agent NEVER auto-sends emails - always generates drafts for review

### LLM Options

**Option 1: OpenAI (Cloud)**
- Model: `gpt-4o-mini` (fast, cost-effective)
- Requires: `OPENAI_API_KEY` in `.env`
- Pros: Best reasoning, no local setup
- Cons: API costs, data leaves machine

**Option 2: Ollama (100% Local)**
- Models: `llama3.2`, `mistral`, `phi3`, etc.
- Requires: Ollama running locally
- Pros: Free, private, no API limits
- Cons: Slower, needs GPU for speed, may have lower quality reasoning

Set in `.env`:
```bash
LLM_PROVIDER=ollama  # or 'openai'
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

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
```

Edit `.env` with your settings:

**For OpenAI (cloud):**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

**For Ollama (local):**
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

Note: For Ollama, install from [ollama.ai](https://ollama.ai) and run:
```bash
ollama pull llama3.2  # or mistral, phi3, etc.
ollama serve
```

### 4. Index Emails

```bash
python src/index_emails.py --max-emails 500
```

First run will prompt Gmail authentication. This creates:
- Vector database in `./chroma_db/`
- Analytics database at `data/gmail_stats.db`

### 5. Start Application

**Chat Interface (LlamaIndex Agent):**
```bash
streamlit run src/app.py
```

**Analytics Dashboard:**
```bash
streamlit run src/dashboard.py
```

Visit `http://localhost:8501` and start chatting!

## 💡 Usage

### Agent Tools Reference

The agent automatically selects the right tool based on your query:

| Tool | Trigger Phrases | Example |
|------|----------------|---------|
| **search_emails** | "find", "search", "show me" | "Find emails from Sarah about budget" |
| **get_thread** | "thread", "conversation", "show thread" | "Show me thread abc123" |
| **triage_recent** | "need replies", "urgent", "action items" | "What needs replies from last week?" |
| **draft_reply** | "draft", "reply", "respond" | "Draft a friendly reply to thread xyz" |

### Example Queries

**Search**
- "What did John say about the Q4 project?"
- "Find emails from Sarah about the budget"
- "Show me invoices from last month"

**Triage**
- "What emails from the last 3 days need replies?"
- "Show me urgent emails waiting for my response"
- "Which messages are waiting for action?"

**Thread**
- "Show me the full thread abc123"
- "Get the conversation history with Sarah"

**Draft Reply**
- "Draft a professional reply to thread xyz789"
- "Help me respond to John's question (friendly tone)"
- "Create a concise reply to the budget request"

### How Agent Works

1. **Indexing Phase** (one-time setup):
   - Fetches emails from Gmail (full content, HTML→text)
   - Cleans and chunks text (1000 chars, 200 overlap)
   - Generates 384-dim embeddings **locally** (sentence-transformers)
   - Stores vectors + metadata (thread_id, message_id) in ChromaDB

2. **Agent Query Phase**:
   - User enters natural language query in Streamlit
   - **LlamaIndex ReAct Agent** reasons about which tool(s) to use
   - Agent calls appropriate tools (search_emails, get_thread, etc.)
   - For triage/draft: uses keyword analysis or LLM generation
   - Returns response with **mandatory citations** (subject, sender, date, message_id, thread_id)
   - Streamlit displays response + citations + optional triage table

### Tool Selection Examples

| User Query | Tool(s) Called | Why |
|------------|---------------|-----|
| "Find emails about budget" | `search_emails` | Semantic search needed |
| "Show thread abc123" | `get_thread` | Explicit thread_id provided |
| "What needs replies?" | `triage_recent` | Action-oriented query |
| "Draft reply to xyz" | `get_thread` + `draft_reply` | Need context + generation |
| "Urgent emails from last week" | `triage_recent(days=7)` | Time + urgency |

### Switching LLM Providers

**In Streamlit UI (Live):**
1. Open sidebar in Streamlit
2. Find "🤖 LLM Provider" section
3. Select OpenAI or Ollama
4. Agent automatically recreates with new provider

**In .env (Persistent):**
```bash
# For OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key

# For Ollama
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

### LLM Comparison

| Feature | OpenAI | Ollama |
|---------|--------|--------|
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Speed** | Fast | Slow (without GPU) |
| **Privacy** | Cloud | 100% Local |
| **Cost** | ~$0.15/1M tokens | Free |
| **Setup** | API key only | Install + download model |

### Citation Format

Agent always includes full citations:
```
📧 Subject: Budget Review Q4
From: sarah@company.com
Date: 2026-01-10
Message ID: <abc123@gmail.com>
Thread ID: thread_xyz789
```

### CLI Options

```bash
# Index first 100 emails
python src/index_emails.py --max-emails 100

# Index 500 emails
python src/index_emails.py --max-emails 500

# Force re-index existing data
python src/index_emails.py --force

# Combine options
python src/index_emails.py --max-emails 1000 --force
```

## 📊 Analytics Dashboard

The dashboard provides visual insights into your Gmail inbox patterns using local SQLite data.

### Running the Dashboard

```bash
streamlit run src/dashboard.py
```

### Features

**Sidebar Filters:**
- 📅 Date range picker
- 🏷️ Label filter (INBOX, SENT, STARRED, etc.)
- 🌐 Domain filter (filter by sender domain)
- 📧 Unread-only toggle
- 🔍 Keyword search

**KPI Cards:**
- Total emails in filtered view
- Unread count
- Unique senders
- Top domain
- Average emails per day

**Charts:**
- 📈 **Emails Over Time**: Line chart showing daily email volume
- 👥 **Top Senders**: Bar chart of most frequent senders
- 🌐 **Top Domains**: Bar chart of most active domains
- 🏷️ **Label Distribution**: Bar and pie charts showing label breakdown
- 🕐 **Hour of Day Heatmap**: When do you receive most emails?

**AI Insights (Optional):**
- 🤖 Click "Generate Inbox Insights" button
- Uses your configured LLM (OpenAI or Ollama) to analyze:
  - Inbox patterns and trends
  - Top 20 recent threads
  - Actionable recommendations
- **Note**: Does NOT send full email bodies to LLM, only aggregated stats + thread metadata

**Thread Drill-Down:**
- View 50 most recent threads
- Click to expand and see last 10 messages
- Shows subject, sender, date, snippet
- Indicators for unread (🔵) and starred (⭐) emails

### Data Refresh

Dashboard data updates automatically when you re-run indexing:

```bash
python src/index_emails.py --force
```

This will:
1. Re-fetch emails from Gmail
2. Update ChromaDB vector database
3. **Update SQLite analytics database** (`data/gmail_stats.db`)

The dashboard queries SQLite directly, so no need to restart after indexing.

### Privacy Note

- All analytics data stored locally in `data/gmail_stats.db`
- No external API calls except optional LLM insights
- SQLite database contains metadata only (no full email bodies)
- Metadata stored: date, sender, subject, snippet, labels, thread_id

## ⚙️ Configuration

Edit `.env` to customize:

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openai/ollama) | openai |
| `OPENAI_API_KEY` | Your OpenAI API key | Required for OpenAI |
| `OLLAMA_MODEL` | Ollama model name | llama3.2 |
| `OLLAMA_BASE_URL` | Ollama server URL | http://localhost:11434 |
| `MAX_EMAILS` | Maximum emails to fetch | 500 |
| `LLM_MODEL` | OpenAI model to use | gpt-4o-mini |
| `TEMPERATURE` | LLM temperature (0-1) | 0.7 |
| `CHROMA_PERSIST_DIRECTORY` | Vector DB location | ./chroma_db |

Advanced settings in [src/config.py](src/config.py):
- `CHUNK_SIZE`: Document chunk size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `EMBEDDING_MODEL`: Sentence transformer model (default: all-MiniLM-L6-v2)
- `EMBEDDING_DEVICE`: CPU or GPU (default: cpu)

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

- [x] Local LLM support (Ollama)
- [x] Analytics dashboard with visual insights
- [ ] Multiple email account support
- [ ] Advanced date range and sender filtering in chat
- [ ] Export search results to CSV
- [ ] GPU acceleration for embeddings
- [ ] Email summarization by date range
- [ ] Automatic re-indexing scheduler
- [ ] Email attachment analysis

## 📝 License

See [LICENSE](LICENSE) file for details.

---

Built with ❤️ using open-source Python libraries


