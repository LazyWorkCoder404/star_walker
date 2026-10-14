import html
import random
import streamlit as st
from nasa import search_images
from ai import STYLES, ask_about_entry, intro_blurb, suggest_questions

st.set_page_config(page_title="Space Explorer", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(ellipse at top, #1a1650 0%, #0b0b1e 65%);
    }
    header[data-testid="stHeader"] { background: transparent; }
    .block-container {
        max-width: 1150px;
        padding-top: 1.2rem;
        padding-bottom: 1rem;
    }

    .app-title {
        text-align: center;
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0 0 0.2rem 0;
        letter-spacing: 0.04em;
    }
    .app-sub {
        text-align: center;
        opacity: 0.7;
        margin-bottom: 1.2rem;
    }

    /* Centered image with a glowing blue frame */
    [data-testid="stImage"] { display: flex; justify-content: center; }
    [data-testid="stImage"] img {
        border: 10px solid #1c00a8;
        border-radius: 14px;
        box-shadow: 0 0 34px rgba(90, 70, 255, 0.45);
    }
    .img-title {
        text-align: center;
        font-size: 0.9rem;
        opacity: 0.8;
        margin-top: 0.6rem;
    }

    /* Blue rounded buttons (suggestion text wraps instead of clipping) */
    .stButton > button {
        background-color: #1c00a8;
        color: white;
        border: none;
        border-radius: 10px;
        width: 100%;
        height: auto;
        white-space: normal;
        padding: 0.45rem 0.8rem;
    }
    .stButton > button:hover { background-color: #2a10c8; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- State ---
st.session_state.setdefault("query", "galaxy")
for key in ("entry", "intro", "suggestions", "answer", "asked", "error"):
    st.session_state.setdefault(key, None)


def reset_ai():
    """Clear AI text so it regenerates (new image or new style)."""
    st.session_state.intro = None
    st.session_state.answer = None
    st.session_state.asked = None
    st.session_state.error = None


def do_search():
    reset_ai()
    st.session_state.suggestions = None
    try:
        results = search_images(st.session_state.query)
    except Exception as e:
        st.session_state.entry = None
        st.session_state.error = f"Couldn't search NASA right now: {e}"
        return
    if not results:
        st.session_state.entry = None
        st.session_state.error = "No images found. Try a different search term."
        return
    pool = [r for r in results if r["explanation"]] or results
    st.session_state.entry = random.choice(pool[:5])


def request_ask():
    st.session_state.run_ask = True


def pick_question(q: str):
    st.session_state.question = q
    st.session_state.run_ask = True


if "started" not in st.session_state:
    st.session_state.started = True
    do_search()

entry = st.session_state.entry

# --- Header ---
st.markdown('<div class="app-title"> Space Explorer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-sub">Search NASA images, then ask the AI about what you see</div>',
    unsafe_allow_html=True,
)

# --- Top: image (left) | inputs (right) ---
top_left, top_right = st.columns([3, 2], gap="large", vertical_alignment="center")

with top_left:
    if entry:
        st.image(entry["thumb"], width=420)
        st.markdown(
            f'<div class="img-title">{html.escape(entry["title"])}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.info("Search for something to see a NASA image.")

with top_right:
    # Row 1: search + Go
    c1, c2 = st.columns([3, 1])
    c1.text_input(
        "Search", key="query", label_visibility="collapsed",
        placeholder="Search NASA images (e.g. nebula, Apollo)",
    )
    c2.button("Go", key="search", on_click=do_search)

    # Row 2: question + Go
    a1, a2 = st.columns([3, 1])
    a1.text_input(
        "Ask", key="question", label_visibility="collapsed",
        placeholder="Ask about Space!",
    )
    a2.button("Go", key="ask", on_click=request_ask)

    # Storyteller style
    st.selectbox("Storyteller style", list(STYLES), key="style", on_change=reset_ai)

    # Suggested questions (generated once per image)
    if entry and st.session_state.suggestions is None:
        with st.spinner("Thinking up questions..."):
            st.session_state.suggestions = suggest_questions(entry)

    if st.session_state.suggestions:
        st.caption("Not sure what to ask? Try one:")
        for n, q in enumerate(st.session_state.suggestions):
            st.button(q, key=f"sugg_{n}", on_click=pick_question, args=(q,))

# --- Handle an ask (typed or from a suggestion button) ---
if st.session_state.pop("run_ask", False):
    question = st.session_state.get("question", "").strip()
    if not entry:
        st.session_state.error = "Search for an image first."
    elif not question:
        st.session_state.error = "Type a question first."
    else:
        st.session_state.error = None
        with st.spinner("Thinking..."):
            st.session_state.answer = ask_about_entry(
                question, entry, st.session_state.style
            )
        st.session_state.asked = question

# --- Bottom: AI feedback + Sources panel (scrolls if the answer is long) ---
bottom_left, _ = st.columns([3, 2], gap="large")

with bottom_left:
    with st.container(border=True, height=280):
        st.markdown("**✨ AI feedback**")
        if st.session_state.error:
            st.error(st.session_state.error)

        if entry and st.session_state.intro is None:
            with st.spinner("The AI is looking at this image..."):
                st.session_state.intro = intro_blurb(entry, st.session_state.style)
        if st.session_state.intro:
            st.write(st.session_state.intro)

        if st.session_state.answer:
            st.divider()
            st.markdown(f"**You asked:** {st.session_state.asked}")
            st.write(st.session_state.answer)

        st.divider()
        st.markdown("**📚 Sources**")
        if entry:
            st.caption(
                f"Image info: NASA Image Library ({entry['nasa_id']}). "
                "Anything beyond the description, including myths, comes from "
                "the model's general knowledge, so verify before citing."
            )