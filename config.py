"""Reads config from .env locally, or st.secrets when deployed on Streamlit Cloud."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def get_setting(key: str) -> str:
    try:
        import streamlit as st

        if key in st.secrets:
            value = st.secrets[key]
        else:
            value = os.environ[key]
    except Exception:
        value = os.environ[key]

    # Web secret editors can silently inject a BOM, a stray newline (from
    # auto-wrapping a long value) or other whitespace into the middle of a
    # pasted value. Neither a URL nor an API key legitimately contains
    # whitespace, so strip ALL of it, then drop any non-ASCII leftovers.
    cleaned = "".join(value.split())
    return cleaned.encode("ascii", "ignore").decode("ascii")


DATABASE_URL = get_setting("DATABASE_URL")
GEMINI_API_KEY = get_setting("GEMINI_API_KEY")
