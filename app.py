import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception:
        api_key = None

SYSTEM_PROMPT = """You are an expert SQL assistant. The user describes what data they want in plain English, and you write a clean, correct SQL query that answers it.

Rules:
- Return the SQL query in a code block first.
- Then briefly explain what the query does in 1-2 sentences.
- If the request is ambiguous about table or column names, make reasonable assumptions and state them.
- Prefer standard ANSI SQL unless the user specifies a dialect."""

st.title("🗃️ English → SQL Generator By GP CUBE")
st.caption("Describe the data you want, and I'll write the SQL.")

if not api_key:
    st.error("No API key found. Make sure GEMINI_API_KEY is set.")
    st.stop()

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("e.g. Show total sales by region for last quarter"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            contents = "\n".join(
                f"{m['role']}: {m['content']}" for m in st.session_state.messages
            )
            response = st.session_state.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
                contents=contents,
            )
            answer = response.text
        except errors.ServerError:
            answer = "⚠️ The model is busy right now. Please try again in a moment."
        except Exception as e:
            answer = f"⚠️ Something went wrong: {e}"

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})