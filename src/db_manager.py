"""SQLite database manager for Gmail metadata."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class GmailDatabase:
    """Manager for Gmail metadata SQLite database."""
    
    def __init__(self, db_path: str = "data/gmail_stats.db"):
        """Initialize database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()
    
    def _create_schema(self):
        """Create database schema if not exists."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                message_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                date TEXT NOT NULL,
                date_timestamp INTEGER NOT NULL,
                from_email TEXT NOT NULL,
                from_domain TEXT NOT NULL,
                to_emails TEXT,
                subject TEXT,
                snippet TEXT,
                label_ids TEXT,
                is_unread INTEGER DEFAULT 0,
                is_starred INTEGER DEFAULT 0,
                has_attachments INTEGER DEFAULT 0,
                is_from_me INTEGER DEFAULT 0,
                indexed_at TEXT NOT NULL
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_date ON emails(date_timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_thread ON emails(thread_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_domain ON emails(from_domain)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_unread ON emails(is_unread)
        """)
        
        self.conn.commit()
    
    def _parse_email_address(self, email_str: str) -> tuple[str, str]:
        """Extract email and domain from 'Name <email@domain.com>' format."""
        # Match email in angle brackets or standalone
        match = re.search(r'<([^>]+)>|([^\s]+@[^\s]+)', email_str)
        if match:
            email = match.group(1) or match.group(2)
            email = email.strip().lower()
            domain = email.split('@')[-1] if '@' in email else 'unknown'
            return email, domain
        return email_str.lower(), 'unknown'
    
    def _parse_date(self, date_str: str) -> tuple[str, int]:
        """Parse date string to ISO format and timestamp."""
        from email.utils import parsedate_to_datetime
        try:
            dt = parsedate_to_datetime(date_str)
            # Convert to UTC if not already
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
            utc_dt = dt.astimezone(tz=None)
            return utc_dt.isoformat(), int(utc_dt.timestamp())
        except Exception:
            # Fallback to current time
            now = datetime.utcnow()
            return now.isoformat(), int(now.timestamp())
    
    def export_emails(self, emails: List[Dict[str, Any]], my_email: Optional[str] = None):
        """Export email metadata to SQLite."""
        cursor = self.conn.cursor()
        indexed_at = datetime.utcnow().isoformat()
        
        # Auto-detect my email if not provided
        if not my_email:
            # Try to get from first email marked as SENT
            for email in emails:
                labels = email.get('labelIds', [])
                if 'SENT' in labels:
                    from_email, _ = self._parse_email_address(email.get('sender', ''))
                    my_email = from_email
                    break
        
        inserted = 0
        updated = 0
        
        for email in emails:
            # Parse sender
            from_email, from_domain = self._parse_email_address(email.get('sender', ''))
            
            # Parse recipients
            to_str = email.get('to', '')
            to_emails = []
            if to_str:
                # Simple split, can be improved
                for addr in to_str.split(','):
                    to_email, _ = self._parse_email_address(addr.strip())
                    to_emails.append(to_email)
            
            # Parse date
            date_iso, date_ts = self._parse_date(email.get('date', ''))
            
            # Get labels
            label_ids = email.get('labelIds', [])
            if not label_ids:
                # Fallback: check if in 'labels' field (Gmail API format)
                label_ids = email.get('labels', [])
            
            # Check flags
            is_unread = 1 if 'UNREAD' in label_ids else 0
            is_starred = 1 if 'STARRED' in label_ids else 0
            has_attachments = 1 if email.get('hasAttachments', False) else 0
            is_from_me = 1 if (my_email and from_email == my_email) else 0
            
            # Check if exists
            cursor.execute("SELECT message_id FROM emails WHERE message_id = ?", 
                          (email.get('message_id', email.get('id')),))
            exists = cursor.fetchone()
            
            if exists:
                # Update
                cursor.execute("""
                    UPDATE emails SET
                        thread_id = ?, date = ?, date_timestamp = ?,
                        from_email = ?, from_domain = ?, to_emails = ?,
                        subject = ?, snippet = ?, label_ids = ?,
                        is_unread = ?, is_starred = ?, has_attachments = ?,
                        is_from_me = ?, indexed_at = ?
                    WHERE message_id = ?
                """, (
                    email.get('thread_id', email.get('threadId', '')),
                    date_iso, date_ts,
                    from_email, from_domain, json.dumps(to_emails),
                    email.get('subject', 'No Subject'),
                    email.get('snippet', ''),
                    json.dumps(label_ids),
                    is_unread, is_starred, has_attachments, is_from_me,
                    indexed_at,
                    email.get('message_id', email.get('id'))
                ))
                updated += 1
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO emails (
                        message_id, thread_id, date, date_timestamp,
                        from_email, from_domain, to_emails, subject, snippet,
                        label_ids, is_unread, is_starred, has_attachments,
                        is_from_me, indexed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    email.get('message_id', email.get('id')),
                    email.get('thread_id', email.get('threadId', '')),
                    date_iso, date_ts,
                    from_email, from_domain, json.dumps(to_emails),
                    email.get('subject', 'No Subject'),
                    email.get('snippet', ''),
                    json.dumps(label_ids),
                    is_unread, is_starred, has_attachments, is_from_me,
                    indexed_at
                ))
                inserted += 1
        
        self.conn.commit()
        print(f"✓ Exported to SQLite: {inserted} new, {updated} updated")
        return inserted, updated
    
    def get_stats(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get aggregate statistics with optional filters."""
        where_clauses = []
        params = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append("date_timestamp >= ?")
                params.append(int(filters['date_from']))
            if 'date_to' in filters:
                where_clauses.append("date_timestamp <= ?")
                params.append(int(filters['date_to']))
            if 'label' in filters and filters['label']:
                where_clauses.append("label_ids LIKE ?")
                params.append(f'%"{filters["label"]}"%')
            if 'from_domain' in filters and filters['from_domain']:
                where_clauses.append("from_domain = ?")
                params.append(filters['from_domain'])
            if 'unread_only' in filters and filters['unread_only']:
                where_clauses.append("is_unread = 1")
            if 'search' in filters and filters['search']:
                where_clauses.append("(subject LIKE ? OR snippet LIKE ? OR from_email LIKE ?)")
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term, search_term])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = self.conn.cursor()
        
        # Total count
        cursor.execute(f"SELECT COUNT(*) FROM emails WHERE {where_sql}", params)
        total = cursor.fetchone()[0]
        
        # Unread count
        unread_clause = " AND ".join(where_clauses + ["is_unread = 1"]) if where_clauses else "is_unread = 1"
        cursor.execute(f"SELECT COUNT(*) FROM emails WHERE {unread_clause}", params)
        unread = cursor.fetchone()[0]
        
        # Unique senders
        cursor.execute(f"SELECT COUNT(DISTINCT from_email) FROM emails WHERE {where_sql}", params)
        unique_senders = cursor.fetchone()[0]
        
        # Top domain
        cursor.execute(f"""
            SELECT from_domain, COUNT(*) as cnt 
            FROM emails 
            WHERE {where_sql}
            GROUP BY from_domain 
            ORDER BY cnt DESC 
            LIMIT 1
        """, params)
        top_domain_row = cursor.fetchone()
        top_domain = top_domain_row[0] if top_domain_row else 'N/A'
        
        # Emails per day (median approximation via avg)
        cursor.execute(f"""
            SELECT 
                COUNT(*) * 1.0 / (
                    (MAX(date_timestamp) - MIN(date_timestamp)) / 86400.0 + 1
                ) as emails_per_day
            FROM emails 
            WHERE {where_sql}
        """, params)
        row = cursor.fetchone()
        emails_per_day = round(row[0], 1) if row and row[0] else 0
        
        return {
            'total': total,
            'unread': unread,
            'unique_senders': unique_senders,
            'top_domain': top_domain,
            'emails_per_day': emails_per_day
        }
    
    def get_emails_by_day(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get email counts grouped by day."""
        where_clauses = []
        params = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append("date_timestamp >= ?")
                params.append(int(filters['date_from']))
            if 'date_to' in filters:
                where_clauses.append("date_timestamp <= ?")
                params.append(int(filters['date_to']))
            if 'label' in filters and filters['label']:
                where_clauses.append("label_ids LIKE ?")
                params.append(f'%"{filters["label"]}"%')
            if 'from_domain' in filters and filters['from_domain']:
                where_clauses.append("from_domain = ?")
                params.append(filters['from_domain'])
            if 'unread_only' in filters and filters['unread_only']:
                where_clauses.append("is_unread = 1")
            if 'search' in filters and filters['search']:
                where_clauses.append("(subject LIKE ? OR snippet LIKE ? OR from_email LIKE ?)")
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term, search_term])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT 
                DATE(date) as day,
                COUNT(*) as count
            FROM emails
            WHERE {where_sql}
            GROUP BY DATE(date)
            ORDER BY day
        """, params)
        
        return [{'day': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    def get_top_senders(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get top email senders."""
        where_clauses = []
        params = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append("date_timestamp >= ?")
                params.append(int(filters['date_from']))
            if 'date_to' in filters:
                where_clauses.append("date_timestamp <= ?")
                params.append(int(filters['date_to']))
            if 'label' in filters and filters['label']:
                where_clauses.append("label_ids LIKE ?")
                params.append(f'%"{filters["label"]}"%')
            if 'unread_only' in filters and filters['unread_only']:
                where_clauses.append("is_unread = 1")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT from_email, COUNT(*) as count
            FROM emails
            WHERE {where_sql} AND is_from_me = 0
            GROUP BY from_email
            ORDER BY count DESC
            LIMIT ?
        """, params + [limit])
        
        return [{'sender': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    def get_top_domains(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get top email domains."""
        where_clauses = []
        params = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append("date_timestamp >= ?")
                params.append(int(filters['date_from']))
            if 'date_to' in filters:
                where_clauses.append("date_timestamp <= ?")
                params.append(int(filters['date_to']))
            if 'label' in filters and filters['label']:
                where_clauses.append("label_ids LIKE ?")
                params.append(f'%"{filters["label"]}"%')
            if 'unread_only' in filters and filters['unread_only']:
                where_clauses.append("is_unread = 1")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT from_domain, COUNT(*) as count
            FROM emails
            WHERE {where_sql} AND is_from_me = 0
            GROUP BY from_domain
            ORDER BY count DESC
            LIMIT ?
        """, params + [limit])
        
        return [{'domain': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    def get_label_breakdown(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get email counts by label."""
        where_clauses = []
        params = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append("date_timestamp >= ?")
                params.append(int(filters['date_from']))
            if 'date_to' in filters:
                where_clauses.append("date_timestamp <= ?")
                params.append(int(filters['date_to']))
            if 'from_domain' in filters and filters['from_domain']:
                where_clauses.append("from_domain = ?")
                params.append(filters['from_domain'])
            if 'unread_only' in filters and filters['unread_only']:
                where_clauses.append("is_unread = 1")
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT label_ids FROM emails WHERE {where_sql}
        """, params)
        
        # Count labels
        label_counts = {}
        for row in cursor.fetchall():
            labels = json.loads(row[0]) if row[0] else []
            for label in labels:
                label_counts[label] = label_counts.get(label, 0) + 1
        
        # Sort by count
        result = [{'label': k, 'count': v} for k, v in label_counts.items()]
        result.sort(key=lambda x: x['count'], reverse=True)
        return result[:10]  # Top 10 labels
    
    def get_hour_distribution(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get email distribution by hour of day."""
        where_clauses = []
        params = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append("date_timestamp >= ?")
                params.append(int(filters['date_from']))
            if 'date_to' in filters:
                where_clauses.append("date_timestamp <= ?")
                params.append(int(filters['date_to']))
            if 'label' in filters and filters['label']:
                where_clauses.append("label_ids LIKE ?")
                params.append(f'%"{filters["label"]}"%')
            if 'from_domain' in filters and filters['from_domain']:
                where_clauses.append("from_domain = ?")
                params.append(filters['from_domain'])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT 
                CAST(strftime('%H', date) AS INTEGER) as hour,
                COUNT(*) as count
            FROM emails
            WHERE {where_sql}
            GROUP BY hour
            ORDER BY hour
        """, params)
        
        return [{'hour': row[0], 'count': row[1]} for row in cursor.fetchall()]
    
    def get_recent_threads(self, limit: int = 20, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get most recent email threads."""
        where_clauses = []
        params = []
        
        if filters:
            if 'date_from' in filters:
                where_clauses.append("date_timestamp >= ?")
                params.append(int(filters['date_from']))
            if 'date_to' in filters:
                where_clauses.append("date_timestamp <= ?")
                params.append(int(filters['date_to']))
            if 'label' in filters and filters['label']:
                where_clauses.append("label_ids LIKE ?")
                params.append(f'%"{filters["label"]}"%')
            if 'from_domain' in filters and filters['from_domain']:
                where_clauses.append("from_domain = ?")
                params.append(filters['from_domain'])
            if 'unread_only' in filters and filters['unread_only']:
                where_clauses.append("is_unread = 1")
            if 'search' in filters and filters['search']:
                where_clauses.append("(subject LIKE ? OR snippet LIKE ? OR from_email LIKE ?)")
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term, search_term])
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT 
                thread_id,
                MAX(date_timestamp) as last_date,
                COUNT(*) as message_count,
                GROUP_CONCAT(DISTINCT subject) as subjects
            FROM emails
            WHERE {where_sql}
            GROUP BY thread_id
            ORDER BY last_date DESC
            LIMIT ?
        """, params + [limit])
        
        return [
            {
                'thread_id': row[0],
                'last_date': row[1],
                'message_count': row[2],
                'subject': row[3].split(',')[0] if row[3] else 'No Subject'
            }
            for row in cursor.fetchall()
        ]
    
    def get_thread_messages(self, thread_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get messages in a thread."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                message_id, date, from_email, subject, snippet,
                is_unread, is_starred
            FROM emails
            WHERE thread_id = ?
            ORDER BY date_timestamp DESC
            LIMIT ?
        """, (thread_id, limit))
        
        return [
            {
                'message_id': row[0],
                'date': row[1],
                'from': row[2],
                'subject': row[3],
                'snippet': row[4],
                'is_unread': bool(row[5]),
                'is_starred': bool(row[6])
            }
            for row in cursor.fetchall()
        ]
    
    def get_all_domains(self) -> List[str]:
        """Get list of all unique domains."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT from_domain 
            FROM emails 
            WHERE is_from_me = 0
            ORDER BY from_domain
        """)
        return [row[0] for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection."""
        self.conn.close()


def export_gmail_metadata_to_sqlite(emails: List[Dict[str, Any]], db_path: str = "data/gmail_stats.db"):
    """Export Gmail metadata to SQLite database.
    
    Args:
        emails: List of email dictionaries from GmailClient
        db_path: Path to SQLite database file
    
    Returns:
        Tuple of (inserted_count, updated_count)
    """
    db = GmailDatabase(db_path)
    result = db.export_emails(emails)
    db.close()
    return result
