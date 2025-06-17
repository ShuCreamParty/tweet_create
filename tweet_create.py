import tweepy
import os
import sys
import datetime
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import traceback
from dotenv import load_dotenv
import schedule
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai import GenerationConfig, Tool, GoogleSearch


load_dotenv()

TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET_KEY = os.environ.get("TWITTER_API_SECRET_KEY")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
NOTIFICATION_EMAIL = os.environ.get("NOTIFICATION_EMAIL")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

GENERATION_PROMPT = "以降の応答では、思考プロセスや補足説明、前置きは一切出力せず、生成するツイートの本文のみを直接出力してください。一言の面白いツイートの内容を1つ考えてください。生成するテキストは、ツイートの本文そのものだけにしてください。前置き、解説、追加のコメントなどは一切含めないでください。言語は日本語に限定します。絵文字や特殊文字は、全く使わないor大量に使うのどちらかにしてください。ツイッターの使用上、280文字まで投稿できますが、5~20文字程度が望ましいです。できるだけ最近の情報を、Google検索機能を用いて投稿のネタに取り入れるとよいです。投稿の内容は自由ですが、高専、富山県、音ゲー、ボーカロイド、ポケモン、麻雀、プログラミング、IT、スイーツなどのジャンルの要素を１つ以上絡めていると、少しだけ好ましいです。ただ常に似通った内容だと面白みがないので、きわめて稀にこの条件をみたさない内容の投稿でも面白いと思います。"


gemini_model = None
try:
    genai.configure(api_key=GEMINI_API_KEY)
        
    generation_config = GenerationConfig(
        temperature=0.9,
        max_output_tokens=280,
    )

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    grounding_tool = Tool(google_search=GoogleSearch())

    gemini_model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-05-20",
        generation_config=generation_config,
        safety_settings=safety_settings,
        tools=[grounding_tool]
    )
    print(f"[{datetime.datetime.now()}] Geminiモデルの初期化完了。")

except Exception as e:
    print(f"[{datetime.datetime.now()}] Geminiモデルの初期化中にエラー: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    gemini_model = None


twitter_client = None
try:
    twitter_client = tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET_KEY,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
    )
    print(f"[{datetime.datetime.now()}] Twitter Client初期化試行完了。")
except Exception as e:
    print(f"[{datetime.datetime.now()}] Twitter Clientの初期化中にエラー: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    twitter_client = None


def send_email_notification(subject, body):
    try:
        smtp_host = 'smtp.gmail.com'
        smtp_port = 587
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = NOTIFICATION_EMAIL
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"[{datetime.datetime.now()}] メール送信成功: {subject}")
        return True
    except Exception as e:
        print(f"[{datetime.datetime.now()}] メール送信エラー: {e}, 件名: {subject}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False


def post_tweet_to_twitter(tweet_text):
    global twitter_client
    if not twitter_client:
        print(f"[{datetime.datetime.now()}] Twitter Clientが無効なためツイート不可。", file=sys.stderr)
        return False, "Twitter Client初期化失敗または未設定"
    if not tweet_text or not tweet_text.strip():
        print(f"[{datetime.datetime.now()}] ツイート内容が空のため投稿スキップ。", file=sys.stderr)
        return False, "ツイート内容が空です"
    try:
        print(f"[{datetime.datetime.now()}] ツイート試行 (Client使用): {tweet_text[:50]}...")
        response = twitter_client.create_tweet(text=tweet_text)
        tweet_id = response.data['id']
        user = client.get_me(user_auth=True).data
        username = user.username
        print(f"[{datetime.datetime.now()}] ツイート成功! ID: {tweet_id}, Text: {tweet_text[:30]}...")
        tweet_url = f"https://twitter.com/{username}/status/{tweet_id}"
        return True, tweet_url
    except tweepy.TweepyException as e:
        error_detail = f"TweepyException: {e}\n"
        if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'text'):
            error_detail += f"API Response: {e.response.text}\n"
        if hasattr(e, 'api_codes'):
            error_detail += f"API Codes: {e.api_codes}\n"
        if hasattr(e, 'api_errors'):
            error_detail += f"API Errors: {e.api_errors}\n"
        print(f"[{datetime.datetime.now()}] ツイート投稿Tweepyエラー:\n{error_detail}", file=sys.stderr)
        return False, error_detail
    except Exception as e:
        error_detail = f"ツイート投稿中の予期せぬエラー: {e}"
        print(f"[{datetime.datetime.now()}] {error_detail}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False, error_detail


def generate_tweet_idea_with_gemini(prompt):
    if not gemini_model:
        return "【エラー】Geminiモデルが利用できません。"
    try:
        print(f"[{datetime.datetime.now()}] Geminiプロンプト送信 (Grounding有効):\n{prompt}")
        response = gemini_model.generate_content(prompt)
        raw_response_text = response.text
        print(f"[{datetime.datetime.now()}] Gemini Raw応答:\n{raw_response_text}")
        
        generated_text = raw_response_text.strip().strip('"')
        if not generated_text:
            print(f"[{datetime.datetime.now()}] 警告: Geminiが空または空白のみのテキストを生成しました。Raw: '{raw_response_text}'")
            return "【エラー】Geminiが有効なテキストを生成しませんでした。"

        possible_tweets = [t.strip() for t in generated_text.split('\n') if t.strip() and not t.startswith("候補")] 
        if "いくつか候補を提案します" in generated_text and possible_tweets: 
             generated_text = possible_tweets[0]
        elif not possible_tweets and "いくつか候補を提案します" in generated_text: 
             generated_text = generated_text.split('\n')[1] if len(generated_text.split('\n')) > 1 else generated_text

        if len(generated_text) > 280:
            print(f"[{datetime.datetime.now()}] Gemini生成テキストが長すぎるため切り詰めます。元: {len(generated_text)}文字")
            generated_text = generated_text[:277] + "..."
            
        print(f"[{datetime.datetime.now()}] Gemini整形後応答(返却前): '{generated_text}' (長さ: {len(generated_text)})")
        return generated_text
    except Exception as e:
        error_msg = f"Gemini APIアイデア生成エラー: {e}"
        print(f"[{datetime.datetime.now()}] {error_msg}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return f"【エラー】アイデア生成失敗。({type(e).__name__})"

def scheduled_job():
    print(f"--- 定期ジョブ開始 ({datetime.datetime.now()}) ---")
    start_time = datetime.datetime.now()
    job_status, email_body_content = "不明", ""
    error_occurred = False
    
    try:
        if not gemini_model:
            job_status = "ネタ生成スキップ (Geminiモデル無効)"
            error_occurred = True
            email_body_content = "Geminiモデルが無効なため、ネタ生成をスキップしました。"
        else:
            tweet_content_generated = generate_tweet_idea_with_gemini(GENERATION_PROMPT)
            if "【エラー】" in tweet_content_generated or not tweet_content_generated.strip():
                job_status = "ネタ生成失敗"
                error_occurred = True
                email_body_content = f"Gemini APIでのネタ生成に失敗、または空の内容が生成されました。\nプロンプト:\n{GENERATION_PROMPT}\n\nエラー/生成内容:\n{tweet_content_generated}"
            else:
                success, result = post_tweet_to_twitter(tweet_content_generated)
                if success:
                    job_status = "ツイート成功"
                    email_body_content = f"以下の内容でツイートを投稿しました。\nツイートURL: {result}\n内容:\n{tweet_content_generated}"
                else:
                    job_status = "ツイート失敗"
                    error_occurred = True
                    email_body_content = f"ツイート投稿に失敗しました。\n試行内容:\n{tweet_content_generated}\n\nエラー詳細:\n{result}"
    except Exception as e:
        job_status = "ジョブ全体で予期せぬエラー"
        error_occurred = True
        tb_str = traceback.format_exc()
        email_body_content = f"Botの定期ジョブ実行中に予期せぬエラーが発生しました。\nエラータイプ: {type(e).__name__}\nエラー詳細: {e}\n\nトレースバック:\n{tb_str}"
        print(f"[{datetime.datetime.now()}] !!! scheduled_job実行中に予期せぬエラー !!!", file=sys.stderr)
        print(tb_str, file=sys.stderr)
    finally:
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        print(f"--- 定期ジョブ終了 ({end_time}), ステータス: {job_status}, 処理時間: {duration} ---")
        
        email_subject = f"【Botエラー】{job_status}" if error_occurred else f"【Bot】{job_status}"
        email_subject += f" ({start_time.strftime('%Y-%m-%d %H:%M')})"
        
        final_email_body = (
            f"定期ジョブの結果報告です。\n\n"
            f"実行時刻: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"ステータス: {job_status}\n"
            f"処理時間: {duration}\n\n"
            f"{email_body_content}"
        )
        send_email_notification(email_subject, final_email_body)


if __name__ == "__main__":
    abort_execution = False
    init_fail_body = "Botの起動に失敗しました。設定を確認してください。\n"
    if not GEMINI_API_KEY:
        print("致命的エラー: GEMINI_API_KEYが.envファイルに設定されていません。処理を終了します。", file=sys.stderr)
        init_fail_body += "- GEMINI_API_KEY がありません。\n"
        abort_execution = True
    if not twitter_client:
        print("致命的エラー: Twitter Clientの初期化に失敗しました。Twitter API認証情報を確認してください。処理を終了します。", file=sys.stderr)
        init_fail_body += "- Twitter Clientの初期化に失敗 (API認証情報等)。\n"
        abort_execution = True
        
    if abort_execution:
        init_fail_subject = f"【緊急Botエラー】起動失敗 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
        send_email_notification(init_fail_subject, init_fail_body)
        sys.exit(1)

    print(f"[{datetime.datetime.now()}] Twitterネタ生成＆投稿ボット起動。")
    schedule.every().day.at("08:00").do(scheduled_job)
    schedule.every().day.at("12:00").do(scheduled_job)
    schedule.every().day.at("16:00").do(scheduled_job)
    print(f"[{datetime.datetime.now()}] 毎日 08:00, 12:00, 16:00 (JST想定) に処理を実行します。")
    print(f"[{datetime.datetime.now()}] スケジュール設定完了。Ctrl+Cで停止します。")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print(f"[{datetime.datetime.now()}] Botを手動で停止しました (KeyboardInterrupt)。")
    except Exception as e:
        tb_str = traceback.format_exc()
        print(f"[{datetime.datetime.now()}] !!! メインループで予期せぬエラー発生 !!!", file=sys.stderr)
        print(tb_str, file=sys.stderr)
        emergency_subject = f"【緊急Botエラー】メインループがエラー停止 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"
        emergency_body = (
            f"Botのメインループが予期せぬエラーで停止した可能性があります。\n\n"
            f"発生時刻: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"エラータイプ: {type(e).__name__}\nエラー詳細: {e}\n\nトレースバック:\n{tb_str}"
        )
        send_email_notification(emergency_subject, emergency_body)
    finally:
        print(f"[{datetime.datetime.now()}] Twitterネタ生成＆投稿ボットを終了します。")