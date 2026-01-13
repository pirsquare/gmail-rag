"""Gmail Analytics Dashboard - Streamlit UI for inbox insights."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from db_manager import GmailDatabase
from config import Config

# Try to import agent for LLM insights
try:
    from agent.controller import create_agent
    from rag_engine import RAGEngine
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False


# Page config
st.set_page_config(
    page_title="Gmail Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Gmail Analytics Dashboard")


# Initialize database
@st.cache_resource
def get_database():
    """Get database connection."""
    db_path = "data/gmail_stats.db"
    if not Path(db_path).exists():
        st.error(f"❌ Database not found at {db_path}")
        st.info("Run indexing first: `python src/index_emails.py`")
        st.stop()
    return GmailDatabase(db_path)


db = get_database()


# Sidebar filters
st.sidebar.header("🔍 Filters")

# Date range
all_emails = pd.read_sql_query(
    "SELECT MIN(date_timestamp) as min_date, MAX(date_timestamp) as max_date FROM emails",
    db.conn
)
min_ts = int(all_emails['min_date'].iloc[0]) if all_emails['min_date'].iloc[0] else 0
max_ts = int(all_emails['max_date'].iloc[0]) if all_emails['max_date'].iloc[0] else int(datetime.now().timestamp())

min_date = datetime.fromtimestamp(min_ts).date()
max_date = datetime.fromtimestamp(max_ts).date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Label filter
label_filter = st.sidebar.selectbox(
    "Label",
    options=["All", "INBOX", "SENT", "STARRED", "UNREAD", "IMPORTANT"],
    index=0
)

# Domain filter
all_domains = db.get_all_domains()
domain_filter = st.sidebar.selectbox(
    "From Domain",
    options=["All"] + all_domains,
    index=0
)

# Unread toggle
unread_only = st.sidebar.checkbox("Unread Only", value=False)

# Search keyword
search_keyword = st.sidebar.text_input("Search Keyword", "")

# Build filters dict
filters = {}
if len(date_range) == 2:
    filters['date_from'] = datetime.combine(date_range[0], datetime.min.time()).timestamp()
    filters['date_to'] = datetime.combine(date_range[1], datetime.max.time()).timestamp()
elif len(date_range) == 1:
    filters['date_from'] = datetime.combine(date_range[0], datetime.min.time()).timestamp()
    filters['date_to'] = datetime.combine(date_range[0], datetime.max.time()).timestamp()

if label_filter != "All":
    filters['label'] = label_filter

if domain_filter != "All":
    filters['from_domain'] = domain_filter

if unread_only:
    filters['unread_only'] = True

if search_keyword:
    filters['search'] = search_keyword

# Main content
st.sidebar.markdown("---")
st.sidebar.caption(f"📁 Database: `{db.db_path}`")


# KPI Cards
st.header("📈 Key Metrics")
stats = db.get_stats(filters)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Emails", f"{stats['total']:,}")

with col2:
    st.metric("Unread", f"{stats['unread']:,}")

with col3:
    st.metric("Unique Senders", f"{stats['unique_senders']:,}")

with col4:
    st.metric("Top Domain", stats['top_domain'])

with col5:
    st.metric("Avg/Day", f"{stats['emails_per_day']:.1f}")

st.markdown("---")


# Charts Section
st.header("📊 Analytics")

# Emails by day
emails_by_day = db.get_emails_by_day(filters)
if emails_by_day:
    df_by_day = pd.DataFrame(emails_by_day)
    df_by_day['day'] = pd.to_datetime(df_by_day['day'])
    
    fig_timeline = px.line(
        df_by_day,
        x='day',
        y='count',
        title='Emails Over Time',
        labels={'day': 'Date', 'count': 'Email Count'},
        markers=True
    )
    fig_timeline.update_layout(height=400)
    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("No emails found for the selected filters.")

# Two columns for bar charts
col_left, col_right = st.columns(2)

with col_left:
    # Top senders
    top_senders = db.get_top_senders(limit=10, filters=filters)
    if top_senders:
        df_senders = pd.DataFrame(top_senders)
        fig_senders = px.bar(
            df_senders,
            x='count',
            y='sender',
            orientation='h',
            title='Top 10 Senders',
            labels={'sender': 'Sender', 'count': 'Emails'}
        )
        fig_senders.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_senders, use_container_width=True)
    else:
        st.info("No sender data available.")

with col_right:
    # Top domains
    top_domains = db.get_top_domains(limit=10, filters=filters)
    if top_domains:
        df_domains = pd.DataFrame(top_domains)
        fig_domains = px.bar(
            df_domains,
            x='count',
            y='domain',
            orientation='h',
            title='Top 10 Domains',
            labels={'domain': 'Domain', 'count': 'Emails'}
        )
        fig_domains.update_layout(height=400, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_domains, use_container_width=True)
    else:
        st.info("No domain data available.")

# Label breakdown
label_breakdown = db.get_label_breakdown(filters)
if label_breakdown:
    df_labels = pd.DataFrame(label_breakdown)
    
    col_label1, col_label2 = st.columns(2)
    
    with col_label1:
        fig_labels_bar = px.bar(
            df_labels,
            x='label',
            y='count',
            title='Label Distribution (Bar)',
            labels={'label': 'Label', 'count': 'Emails'}
        )
        fig_labels_bar.update_layout(height=350)
        st.plotly_chart(fig_labels_bar, use_container_width=True)
    
    with col_label2:
        fig_labels_pie = px.pie(
            df_labels,
            names='label',
            values='count',
            title='Label Distribution (Pie)'
        )
        fig_labels_pie.update_layout(height=350)
        st.plotly_chart(fig_labels_pie, use_container_width=True)

# Hour of day heatmap
hour_dist = db.get_hour_distribution(filters)
if hour_dist:
    df_hours = pd.DataFrame(hour_dist)
    
    # Create heatmap data (1 row)
    hour_counts = {h: 0 for h in range(24)}
    for item in hour_dist:
        hour_counts[item['hour']] = item['count']
    
    heatmap_data = [[hour_counts[h] for h in range(24)]]
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=[f"{h:02d}:00" for h in range(24)],
        y=['Emails'],
        colorscale='Blues',
        showscale=True
    ))
    fig_heatmap.update_layout(
        title='Email Distribution by Hour of Day',
        xaxis_title='Hour',
        height=200
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.markdown("---")


# LLM Insights Section
if AGENT_AVAILABLE:
    st.header("🤖 AI Insights")
    
    if st.button("Generate Inbox Insights", type="primary"):
        with st.spinner("Analyzing your inbox patterns..."):
            try:
                # Get RAG engine
                rag_engine = RAGEngine()
                
                # Check LLM provider from config
                llm_provider = Config.LLM_PROVIDER
                
                # Create agent
                agent = create_agent(rag_engine, llm_provider)
                
                # Get top 20 threads
                top_threads = db.get_recent_threads(limit=20, filters=filters)
                
                # Build summary stats
                thread_summary = f"""Based on the filtered inbox data:
                
**Statistics:**
- Total emails: {stats['total']:,}
- Unread: {stats['unread']:,}
- Unique senders: {stats['unique_senders']:,}
- Top domain: {stats['top_domain']}
- Average emails per day: {stats['emails_per_day']:.1f}

**Top 20 Recent Threads:**
"""
                for i, thread in enumerate(top_threads[:20], 1):
                    thread_date = datetime.fromtimestamp(thread['last_date']).strftime('%Y-%m-%d')
                    thread_summary += f"\n{i}. [{thread_date}] {thread['subject']} ({thread['message_count']} messages)"
                
                # Ask agent to summarize
                prompt = f"""Analyze this inbox data and provide insights:

{thread_summary}

Please provide:
1. Key patterns you notice (e.g., most active senders, busy times)
2. Any notable trends or observations
3. Actionable recommendations (e.g., which threads may need attention)

Keep it concise and actionable."""
                
                result = agent.run(prompt, chat_history=[])
                
                st.markdown("### 💡 Insights")
                st.markdown(result['response'])
                
                if result.get('citations'):
                    with st.expander("📎 Referenced Emails"):
                        for cite in result['citations']:
                            st.caption(f"- {cite['message_id']}")
            
            except Exception as e:
                st.error(f"Error generating insights: {e}")
                st.info("Make sure you have indexed emails and configured LLM settings.")
else:
    st.info("💡 Install agent dependencies to enable AI-powered insights: `pip install llama-index`")

st.markdown("---")


# Thread Drill-Down
st.header("📨 Recent Threads")

recent_threads = db.get_recent_threads(limit=50, filters=filters)

if recent_threads:
    # Display as table
    df_threads = pd.DataFrame(recent_threads)
    df_threads['last_date'] = pd.to_datetime(df_threads['last_date'], unit='s')
    df_threads['last_date'] = df_threads['last_date'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Rename columns for display
    df_display = df_threads[['last_date', 'subject', 'message_count', 'thread_id']].copy()
    df_display.columns = ['Last Activity', 'Subject', 'Messages', 'Thread ID']
    
    st.dataframe(df_display, use_container_width=True, height=400)
    
    # Thread detail view
    st.subheader("Thread Details")
    
    selected_thread = st.selectbox(
        "Select a thread to view messages:",
        options=df_threads['thread_id'].tolist(),
        format_func=lambda x: df_threads[df_threads['thread_id'] == x]['subject'].iloc[0]
    )
    
    if selected_thread:
        messages = db.get_thread_messages(selected_thread, limit=10)
        
        if messages:
            st.caption(f"Showing last {len(messages)} messages in thread")
            
            for msg in messages:
                with st.expander(
                    f"{'🔵 ' if msg['is_unread'] else ''}{'⭐ ' if msg['is_starred'] else ''}"
                    f"{msg['from']} - {msg['date'][:10]}"
                ):
                    st.markdown(f"**Subject:** {msg['subject']}")
                    st.markdown(f"**From:** {msg['from']}")
                    st.markdown(f"**Date:** {msg['date']}")
                    st.markdown(f"**Snippet:** {msg['snippet']}")
                    st.caption(f"Message ID: `{msg['message_id']}`")
        else:
            st.info("No messages found in this thread.")
else:
    st.info("No threads found for the selected filters.")


# Footer
st.markdown("---")
st.caption("📊 Gmail Analytics Dashboard | Data refreshes when you re-run indexing")
