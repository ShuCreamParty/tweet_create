from google import genai
from google.genai import types

# Configure the client
client = genai.Client(api_key="")

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

# Make the request
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="高岡西部中学校の今日の給食は？",
    config=config,
)

# Print the grounded response
print(response.text)