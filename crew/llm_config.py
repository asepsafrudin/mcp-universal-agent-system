import os
from crewai import LLM
from dotenv import load_dotenv

# Load .env explicitly from current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '.env')
load_dotenv(env_path)

def get_llm():
    google_key = os.getenv('GOOGLE_API_KEY')
    groq_key = os.getenv('GROQ_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')

    # Use Groq (has LiteLLM now)
    if groq_key:
        print('Using Groq')
        return LLM(model='groq/llama-3.3-70b-versatile', api_key=groq_key)
    elif openai_key:
        print('Using OpenAI (Gemini quota exceeded)')
        return LLM(model='gpt-4o-mini', api_key=openai_key)
    elif google_key:
        print('Using Google Gemini')
        return LLM(model='gemini/gemini-2.5-flash', api_key=google_key)
    else:
        print('No API Key found')
        return None
