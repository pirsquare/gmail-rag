# Privacy & Security Documentation

## 🔒 Privacy-First Design

Gmail RAG is built with privacy as a core principle. Your email content never leaves your machine unnecessarily.

## Data Processing Flow

### Local Processing (No External API Calls)
1. **Email Fetching**: Downloaded directly from your Gmail account via OAuth
2. **Email Processing**: Text cleaning and parsing (100% local)
3. **Chunking**: Documents split into manageable pieces (100% local)
4. **Embedding**: Converted to vector representations using Sentence-Transformers (100% local)
5. **Vector Storage**: Stored in ChromaDB on your local machine

### Minimal External Communication
- **LLM Queries**: Only conversation and retrieved context sent to OpenAI (configurable)
- **Gmail API**: Uses secure OAuth 2.0 (Google-managed authentication)

## Technology Choices for Privacy

### Local Embeddings
- **Model**: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Runtime**: sentence-transformers library
- **Data Flow**: Email text → embeddings → stored locally
- **Benefit**: Email content never sent to embedding APIs

### Alternative: OpenAI Embeddings (Previous Approach)
- Would send email text to OpenAI's servers
- Not used in this version due to privacy concerns

### Vector Database
- **ChromaDB**: Fully local, no external API calls
- **Storage**: `./chroma_db/` directory (can be encrypted)

## Security Best Practices

### 1. Credential Management
```
❌ NEVER commit:
- .env file with API keys
- credentials.json (Gmail OAuth credentials)
- token.json (Gmail access tokens)

✅ DO:
- Add to .gitignore (already done)
- Keep in secure location
- Rotate API keys regularly
```

### 2. Gmail OAuth Flow
- Uses secure OAuth 2.0 (industry standard)
- Credentials stored in `token.json` locally
- Minimal permissions: `gmail.readonly` only
- Can revoke access at any time in Google Account settings

### 3. Environment Variables
- Load from `.env` file (never hardcoded)
- Use `python-dotenv` for safe loading
- Consider using OS secret managers for production

## Optional Privacy Enhancements

### Use Local LLM Instead of OpenAI
To completely eliminate external API calls:

```bash
# Install Ollama: https://ollama.ai
ollama pull mistral  # or llama2, neural-chat, etc.

# Modify config.py to use local LLM
from langchain.llms import Ollama
llm = Ollama(model="mistral")
```

### Encrypt Vector Database
```bash
# Use file-level encryption
# Option 1: LUKS (Linux)
# Option 2: BitLocker (Windows)
# Option 3: FileVault (macOS)
```

### Network Isolation
- Run on airgapped machine (no internet)
- Use local LLM only
- Store credentials securely

## What Data Leaves Your Machine?

### ✅ Only When Using OpenAI LLM:
1. Retrieved email snippets (context window)
2. Your question/prompt
3. Conversation history

### ❌ Never Sent:
1. Full email body (only chunks during retrieval)
2. Email metadata (sender, date, subject)
3. Vector embeddings
4. Account credentials

### LLM Data Retention
- OpenAI retains API data per their [data retention policy](https://openai.com/policies/api-data-usage-policies)
- Consider disabling for sensitive emails
- Use local LLM alternative for zero external calls

## Auditing & Monitoring

### Check What's Local
```bash
# View vector database
ls -la chroma_db/

# Verify no data sent to unknown hosts
# Use network monitoring tools: Wireshark, Little Snitch, etc.
```

### Gmail OAuth Permissions
1. Go to Google Account: https://myaccount.google.com
2. Navigate to "Security" → "Your devices"
3. Check "Gmail RAG" app permissions
4. Revoke anytime

## Threat Model

### Assumptions
- Your local machine is reasonably secure
- Network is generally trustworthy (or using VPN)
- OpenAI API has reasonable security practices

### Protection Against
- ✅ Email scraping from inbox directly
- ✅ Mass surveillance of email embeddings
- ✅ Unauthorized email access
- ✅ Data leaks from vector database

### Not Protected Against
- ❌ Compromised local machine
- ❌ Spyware/malware on your system
- ❌ Physical access to hard drive
- ❌ Gmail account compromise

## Compliance

### GDPR
- ✅ User data stays local
- ✅ Easy to delete (remove chroma_db/)
- ⚠️  OpenAI API calls may need Data Processing Agreement

### HIPAA
- ✅ Can be compliant with local LLM
- ❌ OpenAI API may require Business Associate Agreement

### SOC 2
- ✅ Local storage verified
- ⚠️  Depends on LLM provider

## Recommendations

### For Maximum Privacy:
1. Use local LLM (Ollama, LLaMA)
2. Run on dedicated machine
3. Use file encryption
4. Monitor network traffic
5. Regular security updates

### For Standard Use:
1. Keep `.env` secure
2. Review Gmail OAuth permissions
3. Monitor OpenAI API usage
4. Keep dependencies updated
5. Use strong passwords

## Contact & Reporting

If you find security issues:
1. Do NOT open public issues
2. Email maintainers privately
3. Include detailed reproduction steps
4. Allow reasonable time for patch

---

**Last Updated**: January 2026
**Version**: 1.0.0
