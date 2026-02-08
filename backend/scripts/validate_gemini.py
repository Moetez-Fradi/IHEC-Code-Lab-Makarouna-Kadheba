import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("backend/services/sentiment-analysis/.env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try parent env
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

print(f"Key found: {'Yes' if api_key else 'No'}")

if api_key:
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-lite-preview-02-05")
        response = model.generate_content("Hello")
        print(f"Model 2.0-flash-lite works: {response.text}")
    except Exception as e:
        print(f"Model 2.0-flash-lite failed: {e}")

    try:
        model = genai.GenerativeModel("gemini-flash-lite-latest")
        response = model.generate_content("Hello")
        print(f"Model flash-lite-latest works: {response.text}")
    except Exception as e:
        print(f"Model flash-lite-latest failed: {e}")
