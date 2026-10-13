import requests
import streamlit as st
import re

PEOPLE = [
    "astronaut", "astronauts", "crew", "engineer", "engineers", "technician",
    "scientist", "scientists", "team", "portrait", "administrator", "ceremony",
    "employees", "students", "visitors", "president",
]
CRAFT = [
    "spacecraft", "rocket", "launch", "shuttle", "capsule", "rover", "lander",
    "satellite", "space station", "spacewalk", "probe", "booster", "launch pad",
    "cleanroom", "test",
]
SPACE = [
    "galaxy", "galaxies", "nebula", "star", "stars", "cluster", "supernova",
    "planet", "moon", "comet", "asteroid", "black hole", "milky way", "sun",
    "solar", "cosmic", "universe", "aurora", "eclipse", "jupiter", "saturn",
    "mars", "venus", "mercury", "neptune", "uranus", "pluto",
]

MODES = ["Space only", "Space + spacecraft", "Everything"]


def _has(text: str, words: list[str]) -> bool:
    return any(re.search(rf"\b{re.escape(w)}\b", text) for w in words)


def _passes(mode: str, flag_text: str, full_text: str) -> bool:
    if mode == "Everything":
        return True
    if _has(flag_text, PEOPLE):
        return False
    if mode == "Space + spacecraft":
        return True
    # "Space only": must mention a space object, and no craft words
    return _has(full_text, SPACE) and not _has(flag_text, CRAFT)

BASE_URL = "https://images-api.nasa.gov"


def _image_url(item: dict) -> str:
    """Return the first link that is actually an image, or ''."""
    for link in item.get("links", []):
        if link.get("render") == "image" and link.get("href"):
            return link["href"].replace("http://", "https://")
    return ""


def _image_works(url: str) -> bool:
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        return r.status_code == 200 and r.headers.get("content-type", "").startswith("image")
    except requests.RequestException:
        return False


@st.cache_data(ttl=3600)
def search_images(query: str, limit: int = 10, mode: str = "Space only") -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/search",
        params={"q": query, "media_type": "image", "page_size": 50},
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json()["collection"]["items"]

    words = query.lower().split()
    candidates = []
    for item in items:
        info = item["data"][0]
        thumb = _image_url(item)
        if not thumb:
            continue

        title = info.get("title", "").lower()
        keywords = " ".join(info.get("keywords", [])).lower()
        desc = (info.get("description") or "").lower()
        flag_text = f"{title} {keywords}"
        if not _passes(mode, flag_text, f"{flag_text} {desc}"):
            continue

        # Title matches count most, then keywords, then description
        score = (
            sum(3 for w in words if w in title)
            + sum(2 for w in words if w in keywords)
            + sum(1 for w in words if w in desc)
        )
        if score == 0:
            continue

        candidates.append((score, {
            "nasa_id": info.get("nasa_id", ""),
            "title": info.get("title", ""),
            "date": info.get("date_created", "")[:10],
            "explanation": info.get("description", ""),
            "thumb": thumb,
        }))

    candidates.sort(key=lambda c: c[0], reverse=True)

    # Keep only images that actually load, best matches first
    results = []
    for _, entry in candidates[:25]:
        if _image_works(entry["thumb"]):
            results.append(entry)
        if len(results) >= limit:
            break
    return results