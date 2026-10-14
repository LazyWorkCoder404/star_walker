import re
import ollama

MODEL = "gemma4:e2b"

BASE_RULES = (
    "You talk about an image from the NASA Image and Video Library. "
    "Use the provided entry as your main source for facts about the image. "
    "If the entry doesn't cover something, say so, then answer from general "
    "knowledge and make clear that part isn't from the entry. "
    "If you mention myths or folklore, name the culture for each story, "
    "only include ones you are confident are real, and say so if you aren't "
    "sure a myth exists for this object. Myths come from general knowledge, "
    "not the NASA entry."
)

STYLES = {
    "Friendly guide": "Speak like a warm, curious guide. Keep it conversational.",
    "Myth teller": (
        "Focus on myths and folklore from different cultures that relate to "
        "the object or region of sky shown. If there are none you're sure of, "
        "say so and share one fascinating real fact instead."
    ),
    "Explain like I'm 10": "Use simple words, short sentences, and fun comparisons.",
    "Astronomer": (
        "Be precise and a little technical: mention physical processes, "
        "scale, and distance where the entry or your knowledge supports it."
    ),
    "Poet": "Answer in vivid, poetic language, but keep every fact accurate.",
    "Ancient stargazer": (
        "Speak as a sky-watcher from long ago marveling at this sight, "
        "but never state wrong facts as true."
    ),
}


def _context(entry: dict) -> str:
    keywords = ", ".join(entry.get("keywords", [])[:15])
    return (
        f"Title: {entry['title']}\n"
        f"Date: {entry['date']}\n"
        f"Keywords: {keywords}\n"
        f"Description: {entry['explanation']}"
    )


def _system(style: str) -> str:
    return f"{BASE_RULES}\n\nStyle: {STYLES.get(style, STYLES['Friendly guide'])}"


def _chat(messages: list[dict]) -> str:
    """Call the model; raises on failure. Strips any <think> block."""
    try:
        response = ollama.chat(model=MODEL, messages=messages, think=False)
    except TypeError:  # older ollama versions don't accept think=
        response = ollama.chat(model=MODEL, messages=messages)
    text = response["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _error_text(e: Exception) -> str:
    if isinstance(e, ollama.ResponseError):
        return f"Ollama error: {e}. Is the model pulled? (`ollama pull {MODEL}`)"
    return f"Couldn't reach the model ({type(e).__name__}: {e}). Is Ollama running?"


def intro_blurb(entry: dict, style: str) -> str:
    messages = [
        {"role": "system", "content": _system(style)},
        {
            "role": "user",
            "content": (
                f"Image entry:\n{_context(entry)}\n\n"
                "Write a short 'Did you know?' blurb (2-3 sentences) about "
                "this image, in your style."
            ),
        },
    ]
    try:
        return _chat(messages)
    except Exception as e:
        return _error_text(e)


def suggest_questions(entry: dict) -> list[str]:
    messages = [
        {
            "role": "system",
            "content": "You write short, fun questions for a space-curious person.",
        },
        {
            "role": "user",
            "content": (
                f"Image entry:\n{_context(entry)}\n\n"
                "Write exactly 3 short, specific questions someone might ask "
                "about this image. One per line, no numbering, no extra text."
            ),
        },
    ]
    try:
        text = _chat(messages)
    except Exception:
        return []
    lines = [re.sub(r"^[\s\-\*\d\.\)]+", "", ln).strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln.endswith("?") and len(ln) < 120][:3]


def ask_about_entry(question: str, entry: dict, style: str = "Friendly guide") -> str:
    messages = [
        {"role": "system", "content": _system(style)},
        {
            "role": "user",
            "content": f"Image entry:\n{_context(entry)}\n\nQuestion: {question}",
        },
    ]
    try:
        return _chat(messages)
    except Exception as e:
        return _error_text(e)