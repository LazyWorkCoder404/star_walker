import ollama

MODEL = "gemma4:e2b"

def ask_about_entry(question: str, entry: dict) -> str:
    context = (
        f"Title: {entry['title']}\n"
        f"Date: {entry['date']}\n"
        f"Description: {entry['explanation']}"
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You answer questions about an image from the NASA Image and "
                "Video Library. Use the provided entry as your main source for "
                "facts about the image. If the entry doesn't cover the question, "
                "say so, then answer from general knowledge and make clear that "
                "part isn't from the entry.\n\n"
                "When asked about myths or folklore, describe stories from "
                "different cultures that relate to the object or region of sky "
                "shown. Name the culture for each story, and only include ones "
                "you are confident are real. If you aren't sure a myth exists "
                "for this object, say so instead of making one up. Make clear "
                "that myths come from general knowledge, not the NASA entry."
            ),
        },
        {
            "role": "user",
            "content": f"Image entry:\n{context}\n\nQuestion: {question}",
        },
    ]
    try:
        response = ollama.chat(model=MODEL, messages=messages)
        return response["message"]["content"]
    except Exception as e:
        return f"Couldn't reach the model. Is Ollama running? ({e})"