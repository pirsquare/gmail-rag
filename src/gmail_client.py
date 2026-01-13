"""Gmail API client."""
import os
import base64
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config


class GmailClient:
    """Gmail API client."""
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', Config.GMAIL_SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "credentials.json not found. Download from Google Cloud Console.\n"
                        "See: https://developers.google.com/gmail/api/quickstart/python"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', Config.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✓ Authenticated with Gmail")
    
    def fetch_emails(self, max_results=None):
        """Fetch emails from Gmail."""
        max_results = max_results or Config.MAX_EMAILS
        
        try:
            emails = []
            page_token = None
            print(f"Fetching up to {max_results} emails...")
            
            while len(emails) < max_results:
                results = self.service.users().messages().list(
                    userId='me',
                    maxResults=min(100, max_results - len(emails)),
                    pageToken=page_token
                ).execute()
                
                messages = results.get('messages', [])
                if not messages:
                    break
                
                for message in messages:
                    email_data = self._get_email_details(message['id'])
                    if email_data:
                        emails.append(email_data)
                    
                    if len(emails) % 50 == 0:
                        print(f"  Fetched {len(emails)}...")
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            print(f"✓ Fetched {len(emails)} emails")
            return emails
        
        except HttpError as error:
            print(f'Error: {error}')
            return []
    
    def _get_email_details(self, message_id):
        """Get email details with full metadata."""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            to = next((h['value'] for h in headers if h['name'] == 'To'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            message_id_header = next((h['value'] for h in headers if h['name'] == 'Message-ID'), message_id)
            body = self._extract_body(message['payload'])
            
            # Get labels
            label_ids = message.get('labelIds', [])
            
            # Check for attachments
            has_attachments = self._has_attachments(message['payload'])
            
            return {
                'id': message_id,
                'message_id': message_id_header,
                'thread_id': message.get('threadId', message_id),
                'subject': subject,
                'sender': sender,
                'to': to,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', ''),
                'labelIds': label_ids,
                'hasAttachments': has_attachments
            }
        except HttpError as error:
            print(f'Error fetching message {message_id}: {error}')
            return None
    
    def _has_attachments(self, payload):
        """Check if message has attachments."""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
                if 'parts' in part:
                    if self._has_attachments(part):
                        return True
        return False
    
    def _extract_body(self, payload):
        """Extract full email body from payload."""
        import base64
        
        body = ""
        
        # Handle multipart messages
        if 'parts' in payload:
            # First pass: try to find text/plain
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    return body
            
            # Second pass: try text/html if no plain text
            for part in payload['parts']:
                if part['mimeType'] == 'text/html' and 'data' in part['body']:
                    html = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    # Convert HTML to plain text
                    body = BeautifulSoup(html, 'html.parser').get_text()
                    return body
            
            # Recursively handle nested parts
            for part in payload['parts']:
                if 'parts' in part:
                    body = self._extract_body(part)
                    if body:
                        return body
        
        # Handle simple message with body
        if 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            return body
        
        return body

