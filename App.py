import random
import streamlit as st
from nasa import search_images, MODES
from ai import ask_about_entry

st.selectbox("Show", MODES, key="mode")

st.set_page_config(page_title="Space Explorer", layout="centered")

# --- Styling: blue image border and blue Go buttons ---
st.markdown(
    """
    <style>
    [data-testid="stImage"] img { border: 14px solid #1c00a8; }
    .stButton > button {
        background-color: #1c00a8; color: white; border: none; width: 100%;
    }
    .stButton > button:hover { background-color: #2a10c8; color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- State ---
st.session_state.setdefault("query", "galaxy")
st.session_state.setdefault("entry", None)
st.session_state.setdefault("answer", None)
st.session_state.setdefault("error", None)


def do_search():
    """Runs before the page redraws, so the image above updates right away."""
    st.session_state.answer = None
    try:
        results = search_images(st.session_state.query, mode=st.session_state.mode)
    except Exception as e:
        st.session_state.error = f"Couldn't search NASA right now: {e}"
        return
    if not results:
        st.session_state.entry = None
        st.session_state.error = "No images found. Try a different search term."
        return
    st.session_state.error = None
    # Prefer images that have a description, since the AI needs one
    pool = [r for r in results if r["explanation"]] or results
    st.session_state.entry = random.choice(pool[:5])


if "started" not in st.session_state:
    st.session_state.started = True
    do_search()

# --- Image ---
entry = st.session_state.entry
if entry:
    st.image(entry["thumb"], use_container_width=True)
    st.caption(entry["title"])
else:
    st.info("Search for something to see a NASA image.")

# --- Row 1: search + Go ---
c1, c2 = st.columns([4, 1])
c1.text_input(
    "Search",
    key="query",
    label_visibility="collapsed",
    placeholder="Search NASA images (e.g. nebula, Apollo)",
)
c2.button("Go", key="search", on_click=do_search)

# --- Row 2: question + Go ---
a1, a2 = st.columns([4, 1])
a1.text_input(
    "Ask",
    key="question",
    label_visibility="collapsed",
    placeholder="Ask about Space!",
)
ask_clicked = a2.button("Go", key="ask")

if ask_clicked:
    question = st.session_state.get("question", "")
    if not entry:
        st.session_state.error = "Search for an image first."
    elif not question:
        st.session_state.error = "Type a question first."
    elif not entry["explanation"]:
        st.session_state.error = "This image has no description for the AI to use."
    else:
        st.session_state.error = None
        with st.spinner("Thinking..."):
            st.session_state.answer = ask_about_entry(question, entry)

# --- AI feedback + Sources panel ---
with st.container(border=True):
    st.markdown("**AI feedback**")
    if st.session_state.error:
        st.error(st.session_state.error)
    elif st.session_state.answer:
        st.write(st.session_state.answer)
    else:
        st.caption("Answers will appear here.")

    st.markdown("**Sources**")
    if entry:
        st.caption(
            f"Image info: NASA Image Library ({entry['nasa_id']}). "
            "Anything beyond the description, including myths, comes from "
            "the model's general knowledge, so verify before citing."
        )