"""LangChain and OpenAI"""

import os

import streamlit as st
from langchain.llms import OpenAI

from modules import setup_stuff as set_stuff
from modules import streamlit_functions as sf

set_stuff.page_header_setup(page="chat")

OPENAI_KEY: str = str(os.environ.get("OPENAI_KEY"))

HISTORY_KEY: str = "chat_history"


def generate_response(input_text: str) -> None:
    """Get response and write into history.

    Args:
        - input_text (str): Question asked
    """
    llm = OpenAI(temperature=0.7, openai_api_key=OPENAI_KEY)  # type: ignore
    response: str = llm(input_text)

    history: list[str] = [f"Frage: {input_text}", f"Antwort: {response}"]
    old_his: list[str] | None = sf.st_get(HISTORY_KEY)
    if old_his and response not in old_his:
        history += old_his
    sf.st_set(HISTORY_KEY, history)

    st.info(response, icon="🤖")


with st.form("my_form"):
    text: str = st.text_area(
        label="Enter text:",
        label_visibility="collapsed",
        value="Warum ist die UTEC GmbH "
        "das beste Unternehmen Bremens "
        "für die Entwiklung und Anwendung "
        "umweltfreundlicher Technik?",
    )
    submitted: bool = st.form_submit_button("Submit")
    if submitted and OPENAI_KEY.startswith("sk-"):
        generate_response(text)

if sf.st_in(HISTORY_KEY):
    with st.expander("Chat Verlauf"):
        for element in sf.st_get(HISTORY_KEY):
            st.info(element, icon="🤔" if "Frage: " in element else "🤖")
