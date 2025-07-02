import streamlit as st
import os
import sys
from google import genai
from google.genai import types
from urllib.parse import quote


# Load API Key from Streamlit Secrets
API_KEY = os.getenv("GOOGLE_API_KEY")


# Language Selection
if "lang" not in st.session_state:
    st.session_state.lang = "English"

col1, col2 = st.columns([3, 7])
with col1:
    if st.session_state.lang == "English":
        lang_btn_label = "Language : **EN** / JP"
    else:
        lang_btn_label = "Language : EN / **JP**"
    if st.button(lang_btn_label, key="lang_btn", use_container_width=True, help="言語を切り替え"):
        st.session_state.lang = "日本語" if st.session_state.lang == "English" else "English"

lang = st.session_state.lang

# Page Configuration
if lang == "English":
    page_title = "🤖 AI Tweet Generator"
    page_icon = "🤖"
    main_text = "Click the button to generate a short, interesting tweet with AI."

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

    button_text_default = "🚀 Generate Tweet"
    button_text_regen = "🔄 Regenerate Tweet"
    generated_label = "✨ Generated Tweet!"
    copy_label = "You can copy this text:"
    post_label = "🐦 Post on Twitter"

elif lang == "日本語":
    page_title = "🤖 AIツイートジェネレーター"
    page_icon = "🤖"
    main_text = "AIが今からめちゃくちゃ面白いツイートを生成します。ボタンを押してください。"

    prompt = """
# 指示
以降の応答では、思考プロセス、補足説明、前置き、候補の提案、生成後の感想などは一切出力せず、ツイートの本文そのものだけを直接出力してください。
# 要件
- 面白い一言ツイートの内容を**1つだけ**生成してください。
- 生成するテキストは、ツイートの本文そのものだけにする必要があります。
- 言語は日本語に限定します。
- 絵文字や特殊文字は、使わないようにしてください。
- #(ハッシュタグ)は絶対に生成テキストに含めてはいけません。
- 5～30文字程度の短い内容が望ましいです。
- Google検索機能を用いて検索した、最近の話題や情報を内容に含めたツイートを生成してください。
"""

    button_text_default = "🚀 ツイート生成"
    button_text_regen = "🔄 再生成"
    generated_label = "✨ 生成されたツイート"
    copy_label = "下記テキストをコピーできます："
    post_label = "🐦 Twitterで投稿"

# Set Streamlit page configuration
st.set_page_config(page_title=page_title, page_icon=page_icon)
st.title(page_title)
st.write(main_text)


# Stop the app if the API Key is not configured on the server
if not API_KEY:
    st.error("FATAL: GOOGLE_AI_KEY is not set on the server.")
    st.info("Please set the GOOGLE_AI_KEY in the deployment environment's secrets.")
    st.stop()


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


# Initialize session state for tweet content
if "generating" not in st.session_state:
    st.session_state.generating = False

if "tweet_content" in st.session_state and st.session_state.tweet_content:
    btn_text = button_text_regen
else:
    btn_text = button_text_default

button_disabled = st.session_state.generating

if st.button(btn_text, type="primary", disabled=button_disabled):
    st.session_state.generating = True
    with st.spinner("AI is thinking..." if lang == "English" else "AIが考え中..."):
        generated_text = generate(PROMPT if lang == "English" else prompt)
        st.session_state.tweet_content = generated_text
    st.session_state.generating = False

if "tweet_content" in st.session_state and st.session_state.tweet_content:
    st.subheader(generated_label)
    text_to_display = st.session_state.tweet_content
    st.text_area(
        label=copy_label,
        value=text_to_display,
        height=100
    )
    # 投稿用テキストを組み立て
    tweet_suffix = "\n\n#AI\nhttps://huggingface.co/spaces/ShuCreamParty/tweet_create"
    tweet_full = text_to_display + tweet_suffix
    tweet_text_encoded = quote(tweet_full, safe='')
    tweet_url = f"https://twitter.com/intent/tweet?text={tweet_text_encoded}"
    st.link_button(post_label, tweet_url, use_container_width=True)
