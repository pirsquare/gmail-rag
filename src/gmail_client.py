"""Gmail API client for fetching emails."""
import os
import pickle
from typing import List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .config import Config


class GmailClient:
    """Client for interacting with Gmail API."""
    
    def __init__(self):
        """Initialize Gmail client."""
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API using OAuth2."""
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', Config.GMAIL_SCOPES)
        
        # If credentials don't exist or are invalid, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "credentials.json not found. Please download it from Google Cloud Console.\n"
                        "See: https://developers.google.com/gmail/api/quickstart/python"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', Config.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✓ Successfully authenticated with Gmail API")
    
    def fetch_emails(self, max_results: int = None) -> List[Dict]:
        """
        Fetch emails from Gmail inbox.
        
        Args:
            max_results: Maximum number of emails to fetch (default from config)
        
        Returns:
            List of email dictionaries with id, subject, body, sender, date
        """
        if max_results is None:
            max_results = Config.MAX_EMAILS
        
        try:
            emails = []
            page_token = None
            
            print(f"Fetching up to {max_results} emails from your inbox...")
            
            while len(emails) < max_results:
                # List messages
                results = self.service.users().messages().list(
                    userId='me',
                    maxResults=min(100, max_results - len(emails)),
                    pageToken=page_token
                ).execute()
                
                messages = results.get('messages', [])
                
                if not messages:
                    break
                
                # Fetch full message details
                for message in messages:
                    email_data = self._get_email_details(message['id'])
                    if email_data:
                        emails.append(email_data)
                    
                    if len(emails) % 50 == 0:
                        print(f"  Fetched {len(emails)} emails...")
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
            
            print(f"✓ Successfully fetched {len(emails)} emails")
            return emails
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return []
    
    def _get_email_details(self, message_id: str) -> Dict:
        """
        Get detailed information for a specific email.
        
        Args:
            message_id: Gmail message ID
        
        Returns:
            Dictionary with email details
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            
            # Extract headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Extract body
            body = self._extract_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }
        
        except HttpError as error:
            print(f'Error fetching message {message_id}: {error}')
            return None
    
    def _extract_body(self, payload: Dict) -> str:
        """
        Extract email body from payload.
        
        Args:
            payload: Email payload from Gmail API
        
        Returns:
            Email body text
        """
        import base64
        
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
                elif part['mimeType'] == 'multipart/alternative':
                    body = self._extract_body(part)
                    if body:
                        break
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        
        return body


if __name__ == "__main__":
    # Test the Gmail client
    client = GmailClient()
    emails = client.fetch_emails(max_results=10)
    print(f"\nFetched {len(emails)} emails")
    if emails:
        print(f"\nFirst email:")
        print(f"  Subject: {emails[0]['subject']}")
        print(f"  From: {emails[0]['sender']}")
        print(f"  Date: {emails[0]['date']}")
