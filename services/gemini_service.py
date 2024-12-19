import json
import random
from datetime import datetime
from flask import current_app as app
import google.generativeai as genai
from dotenv import load_dotenv
import os
from datetime import datetime
import requests
import psycopg2
from jsonschema import validate
import typing_extensions as typing


current_year = datetime.now().year


load_dotenv()

class EventData:
    title: str
    summary: str
    startDate: str
    endDate: str
    location: str
    priority: int
    imageUrl: str
    tags: list[str]
    

class EventExtractorResponse(typing.TypedDict):
    hasEvent: bool
    eventData: typing.Optional[EventData]
    

class EventExtractor:
    def __init__(self, conn, user):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=self.api_key)
        self.conn = conn
        self.user = user
        
        self.adder = CalendarAdder(conn, user)
        
        self.schema = {
            "type": "object",
            "properties": {
                "hasEvent": {
                    "type": "boolean"
                },
                "eventData": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string"
                        },
                        "summary": {
                            "type": "string"
                        },
                        "startDate": {
                            "type": "string"
                        },
                        "endDate": {
                            "type": "string"
                        },
                        "location": {
                            "type": "string"
                        },
                        "priority": {
                            "type": "number"
                        },
                        "imageUrl": {
                            "type": "string"
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["title", "summary", "startDate", "endDate"]
                }
            },
            "required": ["hasEvent"]
        }

        # Create the model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
            "response_schema": EventExtractorResponse,
        }
       
        self.system_instruction = """

### System Instruction for LLM: Handling Mail Content and Extracting Event Data

**Objective:**
Develop a system that processes mail content, identifies whether the mail contains event data, and if so, extracts and returns the event details in a structured JSON format.

**Input:**
Mail content (plain text)

**Output:**
A structured JSON object indicating the presence of event details and, if applicable, the event data itself.

### Steps:

1. **Identify Event Information:**
   - Scan the mail content to determine if it contains event-related information.
   - Events may include meetings, conferences, exams, summits, appointments, etc.

2. **Extract Event Data:**
   If event information is identified, extract the following details:
   - **Date:** Extract the date of the event in ISO format (YYYY-MM-DDTHH:MM:SSZ).
   - **Title:** Extract the title or name of the event.
   - **Priority:** Assign a priority level to the event based on its importance or urgency, represented as an integer between 0 and 100.
   - **Tags:** Generate relevant tags based on the event content. Tags may include keywords such as "Exam," "Summit," "Meeting," etc.

3. **Formulate Response:**
   - If the mail contains event information, construct a JSON object with `hasEvent` set to true and include the extracted `eventData`.
   - If no event information is identified, set `hasEvent` to false.
4. **Date and Time Extraction:**
   - If there is no year mentioned in the date, assume the current year. (The current year is {current_year})  
   - Do not forget! Current year is {current_year} 
   - Always use the UTC timezone for the date and time.

### Example:

#### Mail Content:
```
Subject: Project Kick-off Meeting

Dear Team,

We are excited to launch our new project! Please join us for the kick-off meeting on November 15, 2024, at 10:00 AM.

Agenda:
1. Introduction
2. Project Overview
3. Roles and Responsibilities
4. Q&A Session

Looking forward to your participation.

Best regards,
Project Manager
```

#### Output:
```json
{
  "hasEvent": true,
  "eventData": {
    "startDate": "ISO Date string",
    "endDate": "ISO Date string",
    "title": "string",
    "summary":"string",
    "location": "string",
    "title": "Project Kick-off Meeting",
    "priority": 75,
    "imageUrl": "string",
    "tags": ["Meeting"]
  }
}
```

### Implementation:

#### 1. Parse Mail Content:
   - Extract key sections (e.g., subject, body, dates, times, etc.)
   - Identify patterns indicative of event data (e.g., dates, times, event-related keywords)

#### 2. Extract Event Details:
   - Use natural language processing (NLP) techniques to identify dates, titles, and relevant content
   - Calculate or assign a priority based on predefined rules

#### 3. Generate Tags:
   - Use keyword extraction techniques to generate relevant tags from the content

### JSON Response Structure:
```json
{
  "hasEvent": boolean,
  "eventData": {
    "startDate": "ISO Date string",
    "endDate": "ISO Date string",
    "title": "string",
    "summary":"string",
    "location": "string",
    "priority": number,
    "imageUrl": "string",
    "tags": ["string"]
  }
}
```

### Notes:
- Ensure the date is converted to the ISO format correctly.
- Assign priority rationally, considering factors like urgency, date proximity, and content significance.
- Tag generation should be contextually relevant and accurate.

---

This instruction sets a clear task for the LLM and provides guidance on how to achieve the objective while ensuring clarity in the expected output format.
        """.replace("{current_year}", str(current_year))
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=self.system_instruction,
        )

        
    
    def handle_email(self, email, access_token):
        body_content = email.get('body', {}).get('content', '')
        if body_content:
            chat = self.model.start_chat()
            response = chat.send_message(f"Sender: {email['sender']['emailAddress']['name']} - {email['sender']['emailAddress']['address']}\n\n{body_content}")
            text = response.text
            print(text)
            data_object = json.loads(text) # Parse the response
            validate(data_object, self.schema) # Validate the response here
            print(data_object)
            has_event = data_object['hasEvent']
            if has_event:
                print('Event data found')
            return data_object

    def add_event(self, event_data, access_token):
        try:
            print(event_data.get('title', ''))
            print(event_data.get('summary', ''))
            print(event_data.get('startDate', ''))
            print(event_data.get('endDate', ''))
            print(event_data.get('location', ''))
            
            if not event_data.get('startDate', ''):
                raise ValueError('Start date is required')
            if not event_data.get('endDate', ''):
                raise ValueError('End date is required')
            if not event_data.get('title', ''):
                raise ValueError('Title is required')
            
            added_data = self.adder.handle_event(event_data)
            if not added_data['addToCalendar']:
                print('Event not added to calendar')
                return
            
            event_details = {
                'subject': event_data.get('title', ''),
                'body': {
                    'contentType': 'text',
                    'content': event_data.get('summary', '')
                },
                'start': {
                    'dateTime': event_data.get('startDate', ''),
                    'timeZone': 'UTC'
                },
                'end': {
                    'dateTime': event_data.get('endDate', ''),
                    'timeZone': 'UTC'
                },
                'location': {
                    'displayName': event_data.get('location', '')
                }
            }
            response = requests.post(
                f"https://graph.microsoft.com/v1.0/me/events",
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json=event_details
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error creating event: {e}")
            # print response body
            print(e.response.text)
            raise e
    def add_event_to_database(self, event_data):
        try:
            # Insert the event into the event table
            with self.conn.cursor() as cursor:
                cursor.execute(
                    '''
                    INSERT INTO "event" ("title", "summary", "location", "startDate", "endDate","priority","user_id","imageUrl")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING "id";
                    ''',
                    (event_data.get('title',''), event_data.get('summary',''), event_data.get('location', ''),
                     event_data['startDate'], event_data['endDate'], event_data.get('priority', random.randint(0, 100)), self.user['id'], event_data.get('imageUrl', ''))
                )
                event_id = cursor.fetchone()[0]

                # Insert into tag table if not exists and get the tag id 
                for tag in event_data['tags']:
                    cursor.execute(
                        '''
                        INSERT INTO "tag" ("name") VALUES (%s)
                        ON CONFLICT ("name") DO NOTHING
                        RETURNING id;
                        ''', (tag,)
                    )
                    tag_id = cursor.fetchone()
                    # if INSERT INTO tag did not return id, fetch the id
                    if tag_id is None:
                        cursor.execute('SELECT "id" FROM "tag" WHERE "name" = %s;', (tag,))
                        tag_id = cursor.fetchone()[0]
                    else:
                        tag_id = tag_id[0]

                    # Insert into events_tags_tag to establish relation
                    cursor.execute(
                        '''
                        INSERT INTO "event_tags_tag" ("eventId", "tagId")
                        VALUES (%s, %s)
                        ''', (event_id, tag_id)
                    )

                # Commit the transaction
                self.conn.commit()

        except Exception as e:
            print(f"Error in database operation: {e}")
            self.conn.rollback()
            raise
        
class CalendarAddedResponse(typing.TypedDict):
    addToCalendar: bool

class CalendarAdder:
    def __init__(self, conn, user):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=self.api_key)
        self.conn = conn
        self.user = user
        
        self.schema = {
            "type": "object",
            "properties": {
                "addToCalendar": {
                    "type": "boolean"
                }
            },
        }

        # Create the model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type":"application/json",
            "response_schema":CalendarAddedResponse,
        }
        
        self.system_instruction = """
    
**System Instruction:**

The agent is designed to process user settings and event data. Upon receiving user settings prompt and event data, the agent will proceed through the following steps:

1. **Extract Event Data**: The agent will extract the following event details from the input:
   - Title
   - Description
   - Dates
   - Tags
   - Location

2. **Decision Making**: Using a set of predefined criteria based on user settings, the agent will decide whether to add the event to the calendar. The criteria might include factors such as:
   - Relevance of the event to the user's interests (inferred from tags and description).
   - Conflicts with existing calendar events (dates and times).
   - Importance and priority of the event (through tags, title, or user settings).

3. **Return Output**: Based on the decision, the agent will return a JSON object indicating whether the event should be added to the calendar.

The expected output format is:

```json
{
  "addToCalendar": boolean
}
```
        """
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction=self.system_instruction,
        )     
        
    def handle_event(self,event):
        
        cursor = self.conn.cursor()
        settings_query = cursor.execute(
                        '''
                        SELECT * FROM "setting" WHERE "user_id" = %s
                        ''', (self.user['id'],)
                    )
        settings = cursor.fetchone()
        settings_text = settings[2]
        print(f"User settings is {settings_text}")
        chat = self.model.start_chat()
        response = chat.send_message(f"""
                                     ***The event data***\n
                                     {json.dumps(event)}\n\n\n
                                     ***The user settings prompot***\n
                                     {settings_text}
                                     """)
        text = response.text # Get the response text
        data_object = json.loads(text) # Parse the response
        validate(data_object, self.schema) # Validate the response here
        
        return data_object       

def process_job(email, access_token, user):
    conn = psycopg2.connect(database=os.getenv('POSTGRES_DB'),
                    user=os.getenv('POSTGRES_USER'),
                    password=os.getenv('POSTGRES_PASSWORD'),
                    host=os.getenv('POSTGRES_HOST'),
                    port=os.getenv('POSTGRES_PORT'))
    extractor = EventExtractor(conn, user)
    extractor.handle_email(email, access_token)