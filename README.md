# Gemini Auto Tweet Bot
This program automatically generates tweets using Google's Gemini API, posts them to Twitter at scheduled times, and sends a notification email (for success or failure) via Gmail.

## ✨ Features

- **AI-Powered Content**: Generates unique and interesting tweets using the Gemini API.
- **Timely Topics**: Utilizes Google Search integration to create tweets based on recent topics.
- **Automatic Scheduling**: Tweets are posted automatically at pre-defined times (e.g., 8:00, 12:00, 16:00).
- **Email Notifications**: Sends a report via Gmail upon successful tweeting or if an error occurs.
- **Duplicate Prevention**: Keeps a log of past tweets to avoid posting the same content repeatedly.

## 📋 Requirements

- Python 3.9 or higher

## 🚀 Installation & Setup

Follow these steps to set up and run the program.

### 1. Clone the Repository

First, clone this repository to your machine:
```bash
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
```

### 2. Install Dependencies

Create a file named `requirements.txt` in the project's root directory and paste the following content into it.

**requirements.txt**
```
google-genai
python-dotenv
schedule
tweepy
```

Next, run the following command in your terminal to install the required libraries:
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create a file named `.env` in the root directory of the project. This file will store your secret keys and credentials. (It is listed in `.gitignore` to prevent it from being committed to your repository.)

Copy the following template into your `.env` file and fill in your own values within the `\"\"`.

**.env**
```
# Gemini API Key
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Twitter API v2 Keys
TWITTER_API_KEY="YOUR_TWITTER_API_KEY"
TWITTER_API_SECRET_KEY="YOUR_TWITTER_API_SECRET_KEY"
TWITTER_ACCESS_TOKEN="YOUR_TWITTER_ACCESS_TOKEN"
TWITTER_ACCESS_TOKEN_SECRET="YOUR_TWITTER_ACCESS_TOKEN_SECRET"
TWITTER_BEARER_TOKEN="YOUR_TWITTER_BEARER_TOKEN"

# Gmail Credentials for Sending Notifications
GMAIL_ADDRESS="your_email@gmail.com"
GMAIL_APP_PASSWORD="YOUR_GMAIL_APP_PASSWORD"
```
**How to get the credentials:**
- **Gemini API Key**: Obtain from [Google AI Studio](https://aistudio.google.com/app/apikey).
- **Twitter API Keys**: Apply for access and create a new App in the [Twitter Developer Portal](https://developer.twitter.com/).
- **Gmail App Password**: You need to generate an \"App Password\" for your Google Account. This is a 16-digit code that gives an app permission to access your Google Account. See Google's official guide: [Sign in with App Passwords](https://support.google.com/accounts/answer/185833).

## 🏃 How to Run

Once you have completed the setup, run the script from your terminal:
```bash
python tweet_create.py
```
The script will start and run continuously in the background. It will automatically post tweets at the times specified in the code and send you a notification email for each action.

## 🔧 Customization

- **Scheduling**: To change the tweeting times, modify the `schedule.every().day.at(\"HH:MM\").do(job)` lines at the bottom of `tweet_create.py`.
- **Tweet Content/Prompt**: To change the style or topic of the generated tweets, edit the `PROMPT_TEMPLATE` string variable within `tweet_create.py`.

## 📜 License

This project is licensed under the MIT License.


##  Finally

It took six months to create this program. My feelings after completing it were very painful.

Have a good Twitter life!!!
