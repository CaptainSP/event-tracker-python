import requests
from flask import current_app as app
from rq import Queue
from services.gemini_service import process_job

class MailsService:
    def __init__(self, app, redis_conn, pg_conn):
        self.queue = Queue('gemini', connection=redis_conn)
        self.pg_conn = pg_conn

    def fetch_emails(self, access_token, user):
        try:
            response = requests.get(
                f"{app.config['GRAPH_API_URL']}/me/messages",
                headers={'Authorization': f'Bearer {access_token}'},
                params={'$top': 10, '$select': 'subject,sender,receivedDateTime,bodyPreview,body'}
            )
            response.raise_for_status()
            emails = response.json().get('value', [])
            for email in emails:
                email_id = email.get('id')
                cursor = self.pg_conn.cursor()
                cursor.execute('SELECT * FROM "mail" WHERE "outlookId" = %s', (email_id,))
                email_exists = cursor.fetchone()
                cursor.close()
                if email_exists:
                    print('Email already exists')
                    continue
                self.process_email(email, access_token, user)
            return {'status': 'Emails fetched successfully'}
        except requests.RequestException as e:
            app.logger.error(f"Error fetching emails: {e}")
            return {'error': 'Failed to fetch emails'}
        
    def fetch_events_from_db(self, user_id):
        cursor = self.pg_conn.cursor()
        cursor.execute('''SELECT * FROM "event" WHERE "user_id" = %s ''', (user_id,))
        events = cursor.fetchall()

        # Fetch tags for each event
        events_with_tags = []
        for event in events:
            event_id = event[0]
            cursor.execute('''
                SELECT "t".* FROM "tag" "t"
                JOIN "event_tags_tag" "ett" ON "t"."id" = "ett"."tagId"
                WHERE "ett"."eventId" = %s
            ''', (event_id,))
            tags = cursor.fetchall()
            event_with_tags = {
                'event': event,
                'tags': tags
            }
            events_with_tags.append(event_with_tags)

        cursor.close()
        return events_with_tags

    def process_email(self, email, access_token, user):
        print('Processing email')
        cursor = self.pg_conn.cursor()
        cursor.execute('''
            INSERT INTO "mail" ("outlookId", "subject", "body", "sender", "senderName") VALUES (%s, %s, %s, %s, %s)
        ''', (email['id'], email['subject'], email['bodyPreview'], email['sender']['emailAddress']['address'], email['sender']['emailAddress']['name']))
        cursor.close()
        self.queue.enqueue(process_job, email, access_token, user)