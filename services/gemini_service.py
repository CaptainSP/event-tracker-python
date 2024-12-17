import json
import random
from datetime import datetime
from flask import current_app as app
import google.generativeai as genai
from dotenv import load_dotenv
import os
from datetime import datetime
import requests

current_year = datetime.now().year


load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        genai.configure(api_key=self.api_key)

        # Create the model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
            system_instruction="\n### System Instruction for LLM: Handling Mail Content and Extracting Event Data\n\n**Objective:**\nDevelop a system that processes mail content, identifies whether the mail contains event data, and if so, extracts and returns the event details in a structured JSON format.\n\n**Input:**\nMail content (plain text)\n\n**Output:**\nA structured JSON object indicating the presence of event details and, if applicable, the event data itself.\n\n### Steps:\n\n1. **Identify Event Information:**\n   - Scan the mail content to determine if it contains event-related information.\n   - Events may include meetings, conferences, exams, summits, appointments, etc.\n\n2. **Extract Event Data:**\n   If event information is identified, extract the following details:\n   - **Date:** Extract the date of the event in ISO format (YYYY-MM-DDTHH:MM:SSZ).\n   - **Title:** Extract the title or name of the event.\n   - **Priority:** Assign a priority level to the event based on its importance or urgency, represented as an integer between 0 and 100.\n   - **Tags:** Generate relevant tags based on the event content. Tags may include keywords such as \"Exam,\" \"Summit,\" \"Meeting,\" etc.\n\n3. **Formulate Response:**\n   - If the mail contains event information, construct a JSON object with `hasEvent` set to true and include the extracted `eventData`.\n   - If no event information is identified, set `hasEvent` to false.\n\n### Example:\n\n#### Mail Content:\n```\nSubject: Project Kick-off Meeting\n\nDear Team,\n\nWe are excited to launch our new project! Please join us for the kick-off meeting on November 15, 2023, at 10:00 AM.\n\nAgenda:\n1. Introduction\n2. Project Overview\n3. Roles and Responsibilities\n4. Q&A Session\n\nLooking forward to your participation.\n\nBest regards,\nProject Manager\n```\n\n#### Output:\n```json\n{\n  \"hasEvent\": true,\n  \"eventData\": {\n    \"startDate\": \"ISO Date string\",\n    \"endDate\": \"ISO Date string\",\n    \"title\": \"string\",\n   \"summary\":\"string\",\n    \"title\": \"Project Kick-off Meeting\",\n    \"priority\": 75,\n    \"tags\": [\"Meeting\"]\n  }\n}\n```\n\n### Implementation:\n\n#### 1. Parse Mail Content:\n   - Extract key sections (e.g., subject, body, dates, times, etc.)\n   - Identify patterns indicative of event data (e.g., dates, times, event-related keywords)\n\n#### 2. Extract Event Details:\n   - Use natural language processing (NLP) techniques to identify dates, titles, and relevant content\n   - Calculate or assign a priority based on predefined rules\n\n#### 3. Generate Tags:\n   - Use keyword extraction techniques to generate relevant tags from the content\n\n### JSON Response Structure:\n```json\n{\n  \"hasEvent\": boolean,\n  \"eventData\": {\n    \"startDate\": \"ISO Date string\",\n    \"endDate\": \"ISO Date string\",\n    \"title\": \"string\",\n   \"summary\":\"string\",\n    \"priority\": number,\n    \"tags\": [\"string\"]\n  }\n}\n```\n\n### Notes:\n- Ensure the date is converted to the ISO format correctly.\n- Assign priority rationally, considering factors like urgency, date proximity, and content significance.\n- Tag generation should be contextually relevant and accurate.\n\n---\n\nThis instruction sets a clear task for the LLM and provides guidance on how to achieve the objective while ensuring clarity in the expected output format.",
        )

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
   - If there is no year mentioned in the date, assume the current year. ({current_year})   
   - Always use the UTC timezone for the date and time.

### Example:

#### Mail Content:
```
Subject: Project Kick-off Meeting

Dear Team,

We are excited to launch our new project! Please join us for the kick-off meeting on November 15, 2023, at 10:00 AM.

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
        """
    
    def handle_email(self, email, access_token):
        body_content = email.get('body', {}).get('content', '')
        if body_content:
            chat = self.model.start_chat()
            response = chat.send_message(f"Sender: {email['sender']['emailAddress']['name']} - {email['sender']['emailAddress']['address']}\n\n{body_content}")
            text = response.text
            json_in_text = text[text.index('```json') + len('```json'): text.rindex('```')]
            data_object = json.loads(json_in_text)
            has_event = data_object['hasEvent']
            if has_event:
                self.add_event(data_object['eventData'], access_token)
            return data_object

    def add_event(self, event_data, access_token):
        try:
            print(event_data.get('title', ''))
            print(event_data.get('summary', ''))
            print(event_data.get('startDate', ''))
            print(event_data.get('endDate', ''))
            print(event_data.get('location', ''))
            
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
            raise e


def process_job(email, access_token):
    gemini_service = GeminiService()
    gemini_service.handle_email(email, access_token)