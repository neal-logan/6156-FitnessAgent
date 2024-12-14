import streamlit as st
import prompts
import re
from openai import OpenAI
from model_utils import call_chat_model, call_image_model
import os

client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

st.set_page_config(layout="wide")

# Header
title = "MySupportAgent"
logo_path = "logo.png"

col1, col2 = st.columns([1, 10])

with col1:
    st.image(logo_path, width=100)

# Display the title in the second column
with col2:
    st.title(title)

# Initialize internal and external chat history
if "internal_messages" not in st.session_state:
    st.session_state.internal_messages = [{
        "role": "system",
        "content": prompts.system_prompt
    }]

if "external_messages" not in st.session_state:
    st.session_state.external_messages = []

# Initialize trackers
if "nutrition_tracker" not in st.session_state:
    st.session_state.nutrition_tracker = ""
if "training_tracker" not in st.session_state:
    st.session_state.training_tracker = ""


# Function to extract tracker tags from response
def parse_messages(text):

    message_pattern = r"<message>(.*?)</message>"
    product_pattern = r"<product>(.*?)</product>"
    issue_pattern = r"<issue>(.*?)</issue>"

    message = re.findall(message_pattern, text, re.DOTALL)
    product = re.findall(product_pattern, text, re.DOTALL)
    issue = re.findall(issue_pattern, text, re.DOTALL)

    return message[0] if message else "", product[
        0] if product else "", issue[0] if issue else ""


# Create two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Chat with Support")

    # Create a container for chat messages
    chat_container = st.container(height=400)

    # Create a container for the input box
    input_container = st.container()

    # Display chat messages from history on app rerun
    with chat_container:
        for message in st.session_state.external_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Accept user input
    with input_container:
        upload_col1, upload_col2 = st.columns([4, 1])

        with upload_col1:
            # image upload and processing
            uploaded_file = st.file_uploader("Choose an image...",
                                             type=["jpg", "png"],
                                             label_visibility="collapsed")

            if uploaded_file is not None:
                with upload_col2:
                    if st.button("Process Image"):
                        st.write('Processing image...')
                        st.session_state.internal_messages.append({
                            "role":
                            "user",
                            "content":
                            "Uploaded a photo of food"
                        })
                        st.session_state.external_messages.append({
                            "role":
                            "user",
                            "content":
                            "Uploaded a photo of food"
                        })

                        message, product_tracker = call_image_model(
                            client, uploaded_file)

                        if product_tracker:
                            st.session_state.nutrition_tracker = product_tracker

                        st.session_state.internal_messages.append({
                            "role":
                            "assistant",
                            "content":
                            message
                        })
                        st.session_state.external_messages.append({
                            "role":
                            "assistant",
                            "content":
                            message
                        })

                        st.rerun()

        if prompt := st.chat_input("Enter text..."):
            # Add user message to chat history
            st.session_state.internal_messages.append({
                "role": "user",
                "content": prompt
            })
            st.session_state.external_messages.append({
                "role": "user",
                "content": prompt
            })

            with chat_container:
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.markdown(prompt)

            # with chat_container:
                with st.chat_message("assistant"):
                    messages = [{
                        "role": m["role"],
                        "content": m["content"]
                    } for m in st.session_state.internal_messages]

                    # call the chat model to generate a completion
                    completion = call_chat_model(client, messages)

                    response = completion.choices[0].message.content

                    print('***RAW OUTPUTS***')
                    print(response)

                    # add raw message to internal messages
                    st.session_state.internal_messages.append({
                        "role":
                        "assistant",
                        "content":
                        response
                    })

                    message, product_tracker, issue_tracker = parse_messages(
                        response)

                    # add parsed message to external messages
                    st.session_state.external_messages.append({
                        "role":
                        "assistant",
                        "content":
                        message
                    })

                    # Update session state trackers
                    if product_tracker:
                        st.session_state.nutrition_tracker = product_tracker
                    if issue_tracker:
                        st.session_state.training_tracker = issue_tracker
                    st.rerun()

with col2:
    st.header("Support Ticket Information")
    product_log_container = st.container(height=260)
    with product_log_container:
        st.write("### Product")
        if len(st.session_state.nutrition_tracker) > 0:
            st.write(st.session_state.nutrition_tracker)

    issue_log_container = st.container(height=260)
    with issue_log_container:
        st.write("### Issue")
        if len(st.session_state.training_tracker) > 0:
            st.write(st.session_state.training_tracker)

    
