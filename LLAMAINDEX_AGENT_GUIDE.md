# LlamaIndex Agent Implementation Guide

## Overview

This Gmail RAG application uses **LlamaIndex** as its agent framework to provide intelligent email management through natural language.

## Architecture

### Agent Stack

```
User Query (Streamlit)
    ↓
GmailAgent (agent/controller.py)
    ├─ LlamaIndex ReActAgent
    ├─ System Prompt (citation policy)
    └─ Tool Router
        ↓
    4 Tools (agent/tools.py)
        ├─ EmailSearchTool → semantic_search()
        ├─ ThreadTool → thread filtering
        ├─ TriageTool → keyword analysis
        └─ DraftTool → LLM generation
    ↓
RAGEngine (rag_engine.py)
    ├─ sentence-transformers (local embeddings)
    └─ ChromaDB (vector storage)
    ↓
OpenAI / Ollama (LLM)
```

## LLM Provider Setup

### Option 1: OpenAI (Recommended for best quality)

**.env configuration:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-key-here
LLM_MODEL=gpt-4o-mini
TEMPERATURE=0.7
```

**Pros:**
- Best reasoning quality
- Fast response times
- No local setup required
- Reliable tool calling

**Cons:**
- API costs (~$0.15 per 1M tokens for gpt-4o-mini)
- Queries leave your machine
- Requires internet connection

**Setup:**
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`: `OPENAI_API_KEY=sk-...`
3. That's it!

### Option 2: Ollama (100% Local & Private)

**.env configuration:**
```bash
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
TEMPERATURE=0.7
```

**Pros:**
- 100% local - maximum privacy
- No API costs
- No rate limits
- Works offline

**Cons:**
- Requires local installation
- Slower (especially without GPU)
- Lower reasoning quality than GPT-4
- Needs disk space (models are 4-8GB each)

**Setup:**

1. **Install Ollama:**
   - Windows/Mac/Linux: Download from https://ollama.ai
   - Or via package manager: `brew install ollama` (Mac)

2. **Pull a model:**
   ```bash
   # Recommended models:
   ollama pull llama3.2        # Best balance (4.7GB)
   ollama pull mistral         # Fast, compact (4.1GB)
   ollama pull phi3            # Smallest (2.3GB)
   ollama pull llama3.1:70b    # Best quality (needs powerful GPU)
   ```

3. **Start Ollama server:**
   ```bash
   ollama serve
   ```
   
   Should see: `Ollama is running on http://localhost:11434`

4. **Test it works:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

5. **Update .env:**
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   ```

6. **Run your app:**
   ```bash
   streamlit run src/app.py
   ```

### Switching Between Providers

You can switch LLM providers in the Streamlit UI:
1. Open sidebar
2. Find "🤖 LLM Provider" section
3. Select "openai" or "ollama"
4. Agent automatically recreates with new provider

## Tool Descriptions

### 1. EmailSearchTool

**Purpose:** Semantic search across emails

**Function:** `search_emails(query: str, sender_filter: Optional[str] = None, k: int = 5)`

**How it works:**
1. Performs vector similarity search via RAGEngine
2. Optionally filters by sender email
3. Returns top-k results with full citations

**Example:**
```python
# User: "Find emails from Sarah about budget"
# Agent calls:
search_emails(
    query="budget",
    sender_filter="sarah",
    k=5
)
# Returns: List of 5 emails with subject, sender, date, message_id, thread_id
```

**Citations:** Always includes message_id and thread_id

### 2. ThreadTool

**Purpose:** Retrieve full email thread by ID

**Function:** `get_thread(thread_id: str)`

**How it works:**
1. Searches vectorstore for all docs with matching thread_id
2. Sorts by date (chronological)
3. Returns complete thread with full content

**Example:**
```python
# User: "Show me thread abc123"
# Agent calls:
get_thread(thread_id="abc123")
# Returns: All emails in thread, sorted chronologically
```

**Use cases:**
- "Show me the full conversation"
- "What's the thread history?"
- "Get thread ID xyz"

### 3. TriageTool

**Purpose:** Find emails needing replies

**Function:** `triage_recent(days: int = 1, sender_filter: Optional[str] = None)`

**How it works:**
1. Searches emails from last N days
2. Scans for keywords: "please confirm", "action required", "urgent", etc.
3. Calculates urgency score (# of keywords matched)
4. Ranks by urgency (descending)

**Keywords detected:**
- please confirm
- let me know
- waiting for
- can you / could you / would you
- action required
- need your
- awaiting
- please reply / respond
- get back to me
- follow up
- asap
- urgent
- time-sensitive

**Example:**
```python
# User: "What emails from last 3 days need replies?"
# Agent calls:
triage_recent(days=3)
# Returns: Ranked list with urgency_score and keywords_found
```

**Output format:**
```python
{
    'needs_reply': [
        {
            'subject': '...',
            'sender': '...',
            'urgency_score': 3,  # Number of keywords matched
            'keywords_found': ['please confirm', 'urgent', 'asap'],
            'message_id': '...',
            'thread_id': '...'
        }
    ],
    'count': 5
}
```

### 4. DraftTool

**Purpose:** Generate reply drafts (NEVER auto-sends)

**Function:** `draft_reply(thread_id: str, tone: str = 'professional')`

**How it works:**
1. Retrieves thread content
2. Extracts latest email
3. Builds context (subject, sender, content)
4. Generates draft using LLM with tone instructions
5. Returns draft with **DRAFT ONLY** warning

**Supported tones:**
- `concise`: Brief, to-the-point (2-3 sentences)
- `friendly`: Warm, conversational
- `formal`: Professional, structured
- `professional`: Balanced (default)

**Example:**
```python
# User: "Draft a friendly reply to thread xyz"
# Agent calls:
draft_reply(thread_id="xyz", tone="friendly")
# Returns: Draft text + warning
```

**Safety:**
- Always includes warning: "DRAFT ONLY - Review before sending. Never auto-send."
- Agent cannot send emails (Gmail API is read-only)
- User must copy draft and send manually

## System Prompt

The agent uses a strict system prompt enforcing:

1. **Tool Usage:** Always use tools, never hallucinate data
2. **Citations:** Include message_id and thread_id for every email
3. **Format:** Use structured citation format (subject, sender, date, IDs)
4. **Honesty:** Say "I don't know" if data unavailable
5. **Safety:** Never claim to send emails, only draft

Full prompt in `agent/controller.py`

## Agent Behavior

### ReAct Reasoning Loop

LlamaIndex uses ReAct (Reasoning + Acting) pattern:

```
1. Thought: User wants to find emails about budget
2. Action: search_emails(query="budget", k=5)
3. Observation: Found 5 emails [results]
4. Thought: I have the emails, now format with citations
5. Response: [Formatted answer with citations]
```

### Multi-Tool Calls

Agent can chain multiple tools:

```
User: "Draft a reply to the budget email from Sarah"

1. search_emails(query="budget", sender_filter="Sarah")
   → Get thread_id
2. get_thread(thread_id="xyz")
   → Get full context
3. draft_reply(thread_id="xyz", tone="professional")
   → Generate draft
```

## Performance Tuning

### For Ollama (Local)

**GPU Acceleration:**
```bash
# Check GPU available:
ollama list

# Use GPU model (if available):
ollama pull llama3.2:70b-instruct-q4_0
```

**Model Selection:**
- **Fast & Small:** `phi3` (2.3GB) - Good for quick responses
- **Balanced:** `llama3.2` (4.7GB) - Recommended
- **Best Quality:** `llama3.1:70b` (40GB) - Needs powerful GPU

**Timeout Settings:**
In `agent/controller.py`:
```python
Ollama(
    model=Config.OLLAMA_MODEL,
    request_timeout=120.0  # Increase for slower GPUs
)
```

### For OpenAI

**Cost Optimization:**
- Use `gpt-4o-mini` (cheapest, fast)
- Set `max_tokens` lower in config
- Use shorter system prompts

**Quality vs Speed:**
- `gpt-4o-mini`: Fast, cheap, good quality
- `gpt-4o`: Best quality, slower, more expensive
- `gpt-3.5-turbo`: Fastest, cheapest, lower quality

## Troubleshooting

### Ollama Issues

**"Connection refused":**
```bash
# Start Ollama server:
ollama serve
```

**"Model not found":**
```bash
# Pull the model first:
ollama pull llama3.2
```

**Slow responses:**
- Use smaller model: `phi3`
- Check GPU usage: `nvidia-smi` (Linux)
- Increase timeout in controller.py

### OpenAI Issues

**"Invalid API key":**
- Check `.env` has correct key
- Verify key at https://platform.openai.com/api-keys

**"Rate limit exceeded":**
- Wait a few seconds
- Upgrade to paid tier
- Use Ollama instead

### Agent Issues

**No tool calls:**
- Check LLM supports function calling
- Try more explicit query: "Use search_emails to find..."

**Hallucinated citations:**
- System prompt should prevent this
- If persists, try different LLM model

**Wrong tool selection:**
- LlamaIndex router learns from descriptions
- Improve tool descriptions in `agent/tools.py`

## Advanced Usage

### Custom Tools

Add new tools in `agent/tools.py`:

```python
class CustomTool:
    def __init__(self, rag_engine):
        self.rag = rag_engine
    
    def my_function(self, param: str) -> dict:
        # Your logic here
        return {'result': 'data'}
    
    def as_tool(self):
        return FunctionTool.from_defaults(
            fn=self.my_function,
            name="custom_tool",
            description="What this tool does..."
        )
```

Register in `agent/controller.py`:
```python
tools = [
    self.email_search_tool.as_tool(),
    # ... existing tools
    CustomTool(rag_engine).as_tool()  # Add here
]
```

### Custom System Prompt

Edit `SYSTEM_PROMPT` in `agent/controller.py`:
```python
SYSTEM_PROMPT = """Your custom instructions here..."""
```

### Logging

Enable LlamaIndex verbose mode:
```python
self.agent = ReActAgent.from_tools(
    tools=tools,
    llm=self.llm,
    verbose=True  # Shows reasoning steps
)
```

View in terminal when running Streamlit.

## Comparison: LlamaIndex vs Previous Implementation

| Aspect | Previous (Rule-based) | New (LlamaIndex) |
|--------|----------------------|------------------|
| Routing | Manual if/else | LLM-based reasoning |
| Flexibility | Fixed workflows | Dynamic tool selection |
| Extensibility | Hard to add features | Easy: add tools |
| Transparency | Very clear | Requires logging |
| Quality | Predictable | Depends on LLM |
| Local Support | N/A | ✅ Ollama |

## Best Practices

1. **Start with OpenAI** for testing (best quality)
2. **Switch to Ollama** once stable (privacy + free)
3. **Monitor tool calls** via verbose mode
4. **Test edge cases** (ambiguous queries)
5. **Keep system prompt strict** to avoid hallucinations
6. **Always verify citations** in production use
7. **Use GPU** for Ollama if available

## Resources

- LlamaIndex Docs: https://docs.llamaindex.ai
- Ollama Models: https://ollama.ai/library
- OpenAI Pricing: https://openai.com/api/pricing
- ReAct Paper: https://arxiv.org/abs/2210.03629
