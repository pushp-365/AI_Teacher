from config import client, MODEL_SCRIPT

def generate_script(topic_data: dict, slides_content: list, output_filepath: str = "Speaker_Script.txt") -> str:
    """Generates an engaging speaker script with a subtle Bollywood twist using Groq."""
    slides_summary = "\n".join([f"Slide {i+1}: {s['title']}" for i, s in enumerate(slides_content)])

    prompt = f"""
    You are a charismatic, high-energy educator who uses a subtle touch of Bollywood flair and cinematic analogies to make lessons unforgettable.
    Write a clear, spoken lecture script for: {topic_data['topic']}.
    Target Audience: {topic_data['audience_level']}.

    Slide Structure:
    {slides_summary}

    Style Guidelines:
    - Inject subtle Bollywood references, mini-dramas, or twist dialogs (e.g., "Rishte mein toh yeh primary key lagta hai...", "Picture abhi baaki hai...", dramatic interval moments).
    - Use cinematic metaphors to simplify tricky concepts (e.g., explaining algorithms as hero-villain chases or multi-threading as multi-hero action sequences).
    - Maintain strong educational rigor—the Bollywood humor should act as light seasoning, keeping the core technical explanation clear and accurate.
    - Include spoken cues in brackets like [Pause for dramatic effect] or [Enthusiastic tone].
    """
    response = client.chat.completions.create(
        model=MODEL_SCRIPT,
        messages=[{"role": "user", "content": prompt}]
    )
    
    script_text = response.choices[0].message.content.strip()
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(script_text)

    print(f"[+] Bollywood-infused Speaker Script generated ({MODEL_SCRIPT}): {output_filepath}")
    return script_text