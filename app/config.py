import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
GPT_MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5-mini")
OPENROUTER_MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME", "google/gemma-3-27b-it:free")
OPENROUTER_MODEL_NAME2 = os.getenv("OPENROUTER_MODEL_NAME2", "openai/gpt-oss-120b:free")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")

