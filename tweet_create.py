import os
import sys
import traceback

from dotenv import load_dotenv
import schedule
import time

from google import genai
from google.genai import types

import tweepy

import smtplib
from email.mime.text import MIMEText
from email.header import Header


#Load .env and Variable Declaration
load_dotenv()

GENAI_KEY = os.getenv("GEMINI_API_KEY")

API_KEY = os.getenv("TWITTER_API_KEY")
API_SECRET_KEY = os.getenv("TWITTER_API_SECRET_KEY")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

MAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

LOG_FILE = 'generate.log'

PROMPT_TEMPLATE = f"""
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
- 高専、富山県、音ゲー、ボーカロイド、ポケモン、麻雀、プログラミング、IT、スイーツなどのジャンルの要素を1つ以上絡めてください。

# 良い出力例
プログラミングしてるときの「あ、完全に理解した」は、だいたい何も理解してない。

# 悪い出力例1（候補を提案している）
ツイートの候補をいくつか提案します。
1. プログラミングしてるときの「あ、完全に理解した」は、だいたい何も理解してない。
2. 富山県の白えびバーガー、また食べたい。

# 悪い出力例2（前置きと後置きがある）
承知しました。面白いツイートを生成しますね。

「麻雀の役、全部覚えるより先に実践で覚えた方が早い説」

いかがでしょうか？

# 悪い出力例3（思考プロセスを書いている）
[思考]最近のITニュースを検索...新しいプログラミング言語が話題か。それをネタにしよう。[生成]
新しい言語、とりあえず触ってみるけど、結局手に馴染んだ言語に戻ってきちゃう。

# 特別条件
- 過去に生成したツイートを以下にあげます。これらと全く同じ内容のものは生成しないでください。
- ジャンル、話題、しゃべり方などが過去のものと少しだけ似ているものは許容します。
- 最後投稿については、ジャンルや話題を離したものを生成してください。
{past_tweets}


上記の指示と例を厳守し、ツイートの本文のみを生成してください。
"""


#Gemini Setup
gemini_client = genai.Client(api_key = GENAI_KEY)
grounding_tool = types.Tool(
    google_search = types.GoogleSearch()
)
config = types.GenerateContentConfig(
    tools = [grounding_tool]
)


#Tweepy Setup
twitter_client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET_KEY,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    bearer_token=BEARER_TOKEN
)


#Generate Tweet Function
def generate(texts):
    try:
        print("ツイート内容を生成中...")
        response = gemini_client.models.generate_content(
            model = "gemini-2.0-flash",
            contents = texts,
            config = config
        )
        print("生成完了。")
    
        if not response.parts:
            raise ValueError("Geminiからの応答が空です。")
        
        return response.text.strip()
    
    except Exception as e:
        print(f"ツイート内容作成中にエラーが発生しました: {e}", file=sys.stderr)
        raise


#Do Tweet Function
def tweet(content):
    try:
        print(f"ツイート投稿中: {content}")
        response = twitter_client.create_tweet(text = content)
        user = twitter_client.get_me(user_auth=True).data
        username = user.username
        tweet_id = response.data['id']
        link = f"https://twitter.com/{username}/status/{tweet_id}"
        print(f"ツイート成功: {link}")

        return link
    
    except Exception as e:
        print(f"ツイート投稿中にエラーが発生しました: {e}", file=sys.stderr)
        raise


#Send Mail Function
def mail(body):
    subject = "ツイートBot 結果報告"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = MAIL_ADDRESS
    msg["To"] = MAIL_ADDRESS

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(MAIL_ADDRESS, GMAIL_PASSWORD)
            smtp.send_message(msg)
        print("メールを送信しました。")

    except Exception as e:
        print(f"メール送信中にエラーが発生しました: {e}", file=sys.stderr)
        raise


#Function Calling
def job():
    error_stage = "初期化中"
    try:

        error_stage = "プロンプトの準備"
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                log_lines = [line.strip() for line in f][-20:]
            past_tweets_text = "\n".join(f"- {line}" for line in log_lines)
        except Exception as e:
            print("ログファイルが見つかりません。初回実行として処理を続けます。")
            past_tweets_text="(まだありません)"

        PROMPT = PROMPT_TEMPLATE.format(past_tweets = past_tweets_text)

        error_stage = "ツイートの生成"
        tweet_content = generate(PROMPT)

        error_stage = "ツイートの投稿"
        tweet_link = tweet(tweet_content)

        error_stage = "メールの送信"
        body = f"""
        正常にツイートされました。

        ■ ツイート内容: {tweet_content}
        ■ ツイート先リンク: {tweet_link}
        """
        mail(body)

        error_stage = "ログファイルの書き込み"
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(tweet_content+"\n")

    except Exception as e:
        error_details = traceback.format_exc()
        body = f""" 
        自動ツイートの実行中にエラーが発生しました。

        ■ エラー発生箇所: {error_stage}
        ■ エラーメッセージ: {e}
        ■ 詳細情報: {error_details}
        """

        try:
            mail(body)
            print("エラー通知メールを送信しました。")

        except Exception as mail_e:
            print(f"致命的エラー: エラー通知メールの送信中にもエラーが発生しました: {mail_e}", file=sys.stderr)
            print("\n--- 元のエラー情報 ---\n", file=sys.stderr)
            print(error_details, file=sys.stderr)
            print("\n--- メール送信時のエラー情報 ---\n", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)


#Main Processing
if __name__ == "__main__":
    schedule.every().day.at("08:00").do(job)
    schedule.every().day.at("12:00").do(job)
    schedule.every().day.at("16:00").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)