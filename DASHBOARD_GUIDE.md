# Gmail Analytics Dashboard - Quick Reference

## 🚀 Running the Dashboard

```bash
streamlit run src/dashboard.py
```

Opens at: `http://localhost:8501`

## 📊 Dashboard Components

### Filters (Sidebar)
- **Date Range**: Filter emails by date
- **Label**: INBOX, SENT, STARRED, UNREAD, IMPORTANT
- **From Domain**: Filter by sender domain
- **Unread Only**: Show only unread emails
- **Search**: Keyword search in subject/snippet/sender

### KPI Cards (Top Row)
1. Total Emails (filtered count)
2. Unread Count
3. Unique Senders
4. Top Domain
5. Average Emails/Day

### Charts
1. **Emails Over Time**: Line chart showing daily volume
2. **Top 10 Senders**: Horizontal bar chart
3. **Top 10 Domains**: Horizontal bar chart
4. **Label Distribution**: Bar and pie charts
5. **Hour of Day Heatmap**: Email volume by hour

### AI Insights (Optional)
- Click "Generate Inbox Insights" button
- Analyzes top 20 recent threads + aggregate stats
- Uses configured LLM (OpenAI or Ollama)
- Does NOT send full email bodies to LLM

### Thread Drill-Down
- Table view of 50 most recent threads
- Click to expand messages
- Shows last 10 messages per thread
- Indicators: 🔵 unread, ⭐ starred

## 🔄 Refreshing Data

Dashboard reads from `data/gmail_stats.db`. To refresh:

```bash
python src/index_emails.py --force
```

This updates:
1. ChromaDB vector database
2. SQLite analytics database

No need to restart dashboard - just refresh browser page.

## 📁 Data Storage

**Database Location**: `data/gmail_stats.db`

**Schema**:
- `message_id` (primary key)
- `thread_id`
- `date`, `date_timestamp`
- `from_email`, `from_domain`
- `to_emails` (JSON array)
- `subject`, `snippet`
- `label_ids` (JSON array)
- `is_unread`, `is_starred`, `has_attachments`, `is_from_me`
- `indexed_at`

**Privacy**:
- All data local (no cloud sync)
- Metadata only (no full email bodies)
- SQLite file excluded from git (in `.gitignore`)

## 🎯 Use Cases

### Monitor Inbox Health
- Check unread backlog
- Identify top senders consuming time
- Spot email volume trends

### Time Management
- See when you receive most emails (hour heatmap)
- Find emails per day rate
- Identify busy periods

### Domain Analysis
- Which domains send most emails?
- Filter by work vs personal domains
- Track vendor/partner communication patterns

### Thread Investigation
- Drill down into specific conversations
- Track unread/starred threads
- Quick access to recent activity

### AI-Powered Insights
- Get automated inbox analysis
- Find patterns you might miss
- Receive actionable recommendations

## 🔧 Troubleshooting

### "Database not found"
**Solution**: Run indexing first
```bash
python src/index_emails.py
```

### "No data for selected filters"
**Solution**: Adjust date range or clear filters

### AI Insights not working
**Solution**: 
1. Check LLM_PROVIDER in `.env`
2. For OpenAI: verify OPENAI_API_KEY
3. For Ollama: ensure `ollama serve` is running

### Charts not rendering
**Solution**: Install plotly
```bash
pip install plotly>=5.18.0
```

### Empty thread drill-down
**Solution**: Select a different thread from dropdown

## ⚡ Performance Tips

1. **Filter Before Analyzing**: Use date range to limit dataset
2. **Large Inboxes**: Start with recent 3-6 months
3. **Fast Queries**: SQLite indexes on date, domain, thread_id
4. **AI Insights**: Uses top 20 threads only (fast)

## 🔐 Privacy & Security

- ✅ All data local (SQLite file on your machine)
- ✅ No external API calls (except optional LLM insights)
- ✅ Metadata only (no full email content in database)
- ✅ Database excluded from git
- ✅ Same Gmail OAuth as chat interface (read-only)
- ✅ AI insights use aggregated stats, not raw emails

## 📊 Sample Queries Dashboard Answers

- "How many emails do I get per day on average?"
- "Who emails me the most?"
- "What time of day am I busiest?"
- "How many unread emails do I have?"
- "Which domains send me the most mail?"
- "What are my most recent active threads?"
- "Show me starred emails from last week"
- "Which emails are labeled IMPORTANT?"

All answered visually with charts and filters!
