import streamlit as st
from streamlit_extras.keyboard_url import copy_to_clipboard
import os
import sys
from google import genai
from google.genai import types
from urllib.parse import quote


# Load API Key from Streamlit Secrets or environment variables
API_KEY = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Stop the app if the API Key is not configured on the server
if not API_KEY:
    st.error("FATAL: GOOGLE_AI_KEY is not set on the server.")
    st.info("Please set the GOOGLE_AI_KEY in the deployment environment's secrets.")
    st.stop()

# Define the prompt as a constant
PROMPT = """
# Instruction
In subsequent responses, do not output any thought processes, supplementary explanations, preambles, candidate suggestions, or post-generation comments. Only output the tweet text itself directly.

# Requirements
- Generate only **one** interesting one-liner tweet.
- The language is limited to English.
- Do not use emojis or special characters.
- Never include #(hashtags) in the generated text.
- Short content, around 5-30 characters, is desirable.
- Generate a tweet that includes recent topics or information found using the Google Search tool.
"""


#Generate Tweet Function
def generate(texts):
    try:
        #Gemini Setup
        gemini_client = genai.Client(api_key = API_KEY)
        grounding_tool = types.Tool(
            google_search = types.GoogleSearch()
        )
        config = types.GenerateContentConfig(
            tools = [grounding_tool]
        )
        
        print("Generating tweet content...")
        response = gemini_client.models.generate_content(
            model = "gemini-2.0-flash",
            contents = texts,
            config = config
        )
        print("Generation complete.")
        
        if response.text:
            return response.text.strip()
        else:
            st.error("Generation failed. The response may have been blocked by safety settings.")
            return None
    
    except Exception as e:
        st.error(f"An error occurred during generation: {e}")
        print(f"An error occurred during tweet content generation: {e}", file=sys.stderr)
        return None


# Setting Page
st.set_page_config(page_title="AI Tweet Generator", page_icon="🤖")
st.title("🤖 AI Tweet Generator")
st.write("Click the button to generate a short, interesting tweet with AI.")


#Main Processing
if "tweet_content" in st.session_state and st.session_state.tweet_content:
    button_text = "🔄 Regenerate Tweet"
else:
    button_text = "🚀 Generate Tweet"

if st.button(button_text, type="primary"):
    with st.spinner("AI is thinking..."):
        generated_text = generate(PROMPT)
        st.session_state.tweet_content = generated_text

if "tweet_content" in st.session_state and st.session_state.tweet_content:
    st.subheader("✨ Generated Tweet!")
    text_to_display = st.session_state.tweet_content
    st.text_area(
        label="You can copy this text:",
        value=st.session_state.tweet_content,
        height=100
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        # Twitter Post Button
        tweet_text_encoded = quote(text_to_display)
        tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text_encoded}"
        st.link_button("Post on Twitter", tweet_url, use_container_width=True)
    
    with col2:
        if st.button("📋 Copy Text", use_container_width=True):
            copy_to_clipboard(text_to_display)
