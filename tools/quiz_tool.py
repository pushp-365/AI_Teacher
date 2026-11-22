from config import client, MODEL_QUIZ

def generate_quiz(topic_data: dict, output_filepath: str = "Quiz.txt") -> str:
    """Generates a 3-question quiz with explanations."""
    prompt = f"""
    Generate a 3-question multiple-choice quiz for: {topic_data['topic']}.
    Audience: {topic_data['audience_level']}.

    Format each question cleanly with Options (A-D), Correct Answer, and a brief Explanation.
    """
    response = client.chat.completions.create(
        model=MODEL_QUIZ,
        messages=[{"role": "user", "content": prompt}]
    )
    
    quiz_content = response.choices[0].message.content.strip()
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(quiz_content)

    print(f"[+] Quiz generated ({MODEL_QUIZ}): {output_filepath}")
    return quiz_content