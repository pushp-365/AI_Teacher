import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive"
]

groq_client = Groq(api_key=GROQ_API_KEY)

# =====================================================================
# GROQ SYSTEM PROMPT FOR GOOGLE SLIDES
# =====================================================================
GROQ_SYSTEM_PROMPT = """
You are an expert Presentation Agent generating structured slide content for Google Slides API.
Output a JSON payload describing 3 slides:

Slide 0: Cover Slide (Title, Subtitle, Image URL)
Slide 1: Process Flowchart (Header, Step 1, Step 2, Step 3)
Slide 2: Data Table (Header, 3x3 Table Matrix)

CRITICAL INSTRUCTIONS:
- Return ONLY valid raw JSON.
- Match this EXACT schema structure:

{
  "title": "Main Presentation Deck Title",
  "slides": {
    "cover": {
      "title": "Title Text",
      "subtitle": "Subtitle Text",
      "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&q=80"
    },
    "flowchart": {
      "header": "System Flowchart Architecture",
      "steps": [
        {"title": "1. Input Stream", "details": "• Camera Capture\\n• Frame Preprocessing"},
        {"title": "2. AI Inference", "details": "• YOLO Detection\\n• Hand Tracking"},
        {"title": "3. Actuation", "details": "• ESP32 Dispatch\\n• Servo Motor Control"}
      ]
    },
    "table": {
      "header": "System Specifications",
      "matrix": [
        ["Component", "Specification", "Function"],
        ["Compute", "Raspberry Pi 4 (8GB)", "Edge Processing"],
        ["Microcontroller", "ESP32-WROOM-32", "Motor Actuation"]
      ]
    }
  }
}
"""

def get_slides_service():
    """Authenticates using Service Account credentials."""
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("slides", "v1", credentials=creds)

def fetch_content_from_groq(topic: str) -> dict:
    """Queries Groq to generate slide content."""
    print(f"🤖 Groq Agent generating slide structure for: '{topic}'...")
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": GROQ_SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate presentation content for: {topic}"}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )
    return json.loads(response.choices[0].message.content)

def create_google_slides_presentation(data: dict):
    """Builds presentation via Google Slides API batch requests."""
    slides_service = get_slides_service()
    
    # 1. Create a blank presentation
    presentation = slides_service.presentations().create(
        body={"title": data.get("title", "Generated Presentation")}
    ).execute()
    
    presentation_id = presentation.get("presentationId")
    first_slide_id = presentation.get("slides")[0].get("objectId")
    
    print(f"📄 Created Google Slides Deck: https://docs.google.com/presentation/d/{presentation_id}/edit")

    requests = []

    # Slide 1 (Cover): Add Title, Subtitle, and Hero Image
    requests.extend([
        {
            "createShape": {
                "objectId": "cover_title_box",
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": first_slide_id,
                    "size": {"width": {"magnitude": 600, "unit": "PT"}, "height": {"magnitude": 60, "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 50, "unit": "PT"}
                }
            }
        },
        {"insertText": {"objectId": "cover_title_box", "text": data["slides"]["cover"]["title"]}},
        {
            "createShape": {
                "objectId": "cover_subtitle_box",
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": first_slide_id,
                    "size": {"width": {"magnitude": 600, "unit": "PT"}, "height": {"magnitude": 40, "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 120, "unit": "PT"}
                }
            }
        },
        {"insertText": {"objectId": "cover_subtitle_box", "text": data["slides"]["cover"]["subtitle"]}},
        {
            "createImage": {
                "objectId": "cover_hero_img",
                "url": data["slides"]["cover"]["image_url"],
                "elementProperties": {
                    "pageObjectId": first_slide_id,
                    "size": {"width": {"magnitude": 620, "unit": "PT"}, "height": {"magnitude": 220, "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 180, "unit": "PT"}
                }
            }
        }
    ])

    # Slide 2 (Flowchart): Create Slide & 3 Process Nodes
    slide2_id = "flowchart_slide_id"
    requests.append({"createSlide": {"objectId": slide2_id, "slideLayoutPageProperties": {"layoutTemplate": "BLANK"}}})

    # Header
    requests.extend([
        {
            "createShape": {
                "objectId": "flow_header",
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide2_id,
                    "size": {"width": {"magnitude": 600, "unit": "PT"}, "height": {"magnitude": 40, "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 30, "unit": "PT"}
                }
            }
        },
        {"insertText": {"objectId": "flow_header", "text": data["slides"]["flowchart"]["header"]}}
    ])

    # Process Nodes
    steps = data["slides"]["flowchart"]["steps"]
    x_positions = [50, 270, 490]
    for idx, step in enumerate(steps[:3]):
        node_id = f"flow_node_{idx}"
        requests.extend([
            {
                "createShape": {
                    "objectId": node_id,
                    "shapeType": "ROUNDED_RECTANGLE",
                    "elementProperties": {
                        "pageObjectId": slide2_id,
                        "size": {"width": {"magnitude": 180, "unit": "PT"}, "height": {"magnitude": 240, "unit": "PT"}},
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": x_positions[idx], "translateY": 100, "unit": "PT"}
                    }
                }
            },
            {"insertText": {"objectId": node_id, "text": f"{step['title']}\n\n{step['details']}"}}
        ])

    # Slide 3 (Table): Create Slide & Table Matrix
    slide3_id = "table_slide_id"
    table_id = "specs_table_id"
    requests.extend([
        {"createSlide": {"objectId": slide3_id, "slideLayoutPageProperties": {"layoutTemplate": "BLANK"}}},
        {
            "createShape": {
                "objectId": "table_header",
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide3_id,
                    "size": {"width": {"magnitude": 600, "unit": "PT"}, "height": {"magnitude": 40, "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 30, "unit": "PT"}
                }
            }
        },
        {"insertText": {"objectId": "table_header", "text": data["slides"]["table"]["header"]}},
        {
            "createTable": {
                "objectId": table_id,
                "elementProperties": {
                    "pageObjectId": slide3_id,
                    "size": {"width": {"magnitude": 620, "unit": "PT"}, "height": {"magnitude": 200, "unit": "PT"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 100, "unit": "PT"}
                },
                "rows": 3,
                "columns": 3
            }
        }
    ])

    # Insert Table Cell Data
    matrix = data["slides"]["table"]["matrix"]
    for row_idx in range(len(matrix)):
        for col_idx in range(len(matrix[row_idx])):
            cell_text = str(matrix[row_idx][col_idx])
            requests.append({
                "insertText": {
                    "objectId": table_id,
                    "cellLocation": {"rowIndex": row_idx, "columnIndex": col_idx},
                    "text": cell_text
                }
            })

    # Execute all operations in one batch request
    print("🚀 Sending batchUpdate commands to Google Slides API...")
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={"requests": requests}
    ).execute()

    print("✅ Presentation built successfully!")

if __name__ == "__main__":
    topic = "Autonomous Micro-Robotic Prosthetics using ESP32 and YOLO"
    content_data = fetch_content_from_groq(topic)
    create_google_slides_presentation(content_data)