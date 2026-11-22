import json
from config import client, MODEL_PARSER

def parse_teacher_input(raw_prompt: str) -> dict:
    """Parses raw input into structured JSON format using Groq."""
    prompt = f"""
    You are an AI input parser for an educational app.
    Parse the following teacher prompt into a clean JSON structure.

    Return ONLY a valid JSON object matching this key structure:
    {{
        "topic": "Main topic title",
        "duration": "Estimated time limit",
        "audience_level": "Target audience level",
        "key_goals": ["Goal 1", "Goal 2", "Goal 3"]
    }}

    Teacher Prompt: "{raw_prompt}"
    """
    response = client.chat.completions.create(
        model=MODEL_PARSER,
        messages=[{"role": "user", "content": prompt}]
    )
    
    clean_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)