import json
from config import client, MODEL_REPROMPT

def refine_topic_data(current_data: dict, feedback: str) -> dict:
    """Refines and updates curriculum JSON based on teacher feedback."""
    prompt = f"""
    You are an AI curriculum assistant. Adjust the current curriculum plan based on teacher feedback.

    Current Plan: {json.dumps(current_data)}
    Teacher Feedback: "{feedback}"

    Return ONLY updated JSON matching the original key structure:
    {{
        "topic": "...",
        "duration": "...",
        "audience_level": "...",
        "key_goals": [...]
    }}
    """
    response = client.chat.completions.create(
        model=MODEL_REPROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    
    clean_text = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_text)