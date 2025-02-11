from dotenv import load_dotenv, find_dotenv
import os

dotenv_path = find_dotenv()  # Find the .env file
print(f".env file found at: {dotenv_path}")  # Debugging line

load_dotenv(dotenv_path)  # Load environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    print("API Key Loaded Successfully!")
else:
    print("Error: GEMINI_API_KEY not found. Make sure it's in the .env file.")
