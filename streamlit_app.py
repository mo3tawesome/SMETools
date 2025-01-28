import streamlit as st
import time
import json
import re
from openai import OpenAI

assistant_id = "asst_CPjGyfgWF1n2qPIBUzXdlYnR"

# Initialize Streamlit app
st.title("💬 AI Project Manager")
st.write("This chatbot uses OpenAI's Assistants API to help with project management.")

# Prompt for OpenAI API key
api_key = st.text_input("Enter your OpenAI API key:", type="password")
if not api_key:
    st.warning("Please enter your OpenAI API key to proceed.")
    st.stop()

# Initialize OpenAI client with user-provided API key
client = OpenAI(api_key=api_key)

# Initialize session state variables
if "thread_id" not in st.session_state:
    # Create a new thread only once
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
else:
    thread = client.beta.threads.retrieve(st.session_state.thread_id)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_message_id" not in st.session_state:
    st.session_state.last_message_id = None

# Ask for user message
prompt = st.chat_input("Type your message here...")

# Display Chat History
st.write("### Chat History:")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send user message to the assistant
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=[{"type": "text", "text": prompt}]
    )

    # Start a run
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

    # Wait for the assistant to finish responding
    def wait_on_run(run_obj, t_id):
        while run_obj.status in ["queued", "in_progress"]:
            time.sleep(1)
            run_obj = client.beta.threads.runs.retrieve(thread_id=t_id, run_id=run_obj.id)
        return run_obj

    run = wait_on_run(run, st.session_state.thread_id)

    # Retrieve new messages
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id,
        order='asc',
        after=st.session_state.last_message_id
    )

    if messages.data:
        st.session_state.last_message_id = messages.data[-1].id

    # Display assistant responses
    for msg in messages.data:
        if msg.role == "assistant":
            assistant_reply = ""
            for content_block in msg.content:
                if content_block.type == "text":
                    assistant_reply += content_block.text.value
                elif content_block.type == "json":
                    assistant_reply += json.dumps(content_block.json, indent=2)
            if assistant_reply:
                with st.chat_message("assistant"):
                    st.markdown(assistant_reply)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
