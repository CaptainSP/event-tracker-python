import requests
from flask import current_app as app
from rq import Queue
from services.gemini_service import process_job

class MailsService:
    def __init__(self, app,redis_conn,pg_conn):
        self.queue = Queue('gemini', connection=redis_conn)

    def fetch_emails(self, access_token):
        try:
            response = requests.get(
                f"{app.config['GRAPH_API_URL']}/me/messages",
                headers={'Authorization': f'Bearer {access_token}'},
                params={'$top': 10, '$select': 'subject,sender,receivedDateTime,bodyPreview,body'}
            )
            response.raise_for_status()
            emails = response.json().get('value', [])
            for email in emails:
                self.process_email(email, access_token)
            return {'status': 'Emails fetched successfully'}
        except requests.RequestException as e:
            app.logger.error(f"Error fetching emails: {e}")
            return {'error': 'Failed to fetch emails'}

    def process_email(self, email, access_token):
        print('Processing email')
        self.queue.enqueue(process_job, email, access_token)