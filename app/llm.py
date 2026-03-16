import requests
import time
import json
from openai import OpenAI
from .config import (
    OPENAI_API_KEY,
    GPT_MODEL_NAME,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL_NAME,
    OPENROUTER_MODEL_NAME2
)

SYSTEM_PROMPT = """
You are an AI system that evaluates the relevance of a news article to a list of client organizations.

Your task is to analyze the given news input and determine how relevant the article is for each client listed in the "client" array.

Input structure:

title: news title
content: full news article
client: list of client organization names

Instructions:

Read and understand the title and full content of the article.

Identify the main topic, key entities, institutions involved, and overall context.

For each client in the client list:

Determine whether the article is relevant to the client.

Relevance should be based on direct mention, institutional role, core function, or strong contextual relationship.

Assign:

"relevan": true if the article has meaningful connection to the client.
"relevan": false if there is no clear or significant connection.

Assign a relevance "score" between 0.0 and 1.0 using the following guideline:

0.0–0.3 → Not relevant (no connection)
0.4–0.6 → Slightly or indirectly related
0.7–0.8 → Clearly relevant
0.9–1.0 → Highly relevant (directly about the client or core responsibility)

Important rules:

Do not assume relevance without textual evidence.
Be objective and conservative in scoring.
Do not include explanations or commentary.
Return only valid JSON.

Special routing rules:

If the article contains any relationship, mention, or contextual relevance to the following keywords or entities:

**Korlantas Polri, Kakorlantas Polri, Irjen Agus Suryonugroho, Operasi Keselamatan,
Operasi Ketupat, Polantas Menyapa, mudik lebaran 2026, arus mudik 2026, arus balik 2026,
one way tol japek 2026, jadwal ganjil genap 2026, jadwal one way 2026, jalan pulang 2026, koorlantas**

*Then automatically set the client to* : "Korlantas Polri" and evaluate it accordingly.

If the article does *NOT contain any of the keywords listed above*, then automatically assign the client to: *"Multipool"* and evaluate it accordingly.

*The output must strictly follow this structure:*

{
    [
      {
        "client": "Multipool",
        "relevan": true,
        "score": 0.7
      },
      {
        "client": "Korlantas",
        "relevan": false,
        "score": 0.5
      }
    ]
}
"""

client_openai = OpenAI(api_key=OPENAI_API_KEY)

def _call_openrouter(model_name, system_prompt, user_prompt, max_retries=3):

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"}
    }

    # Khusus gpt-oss reasoning model
    if "gpt-oss" in model_name:
        payload["reasoning"] = {"enabled": True}

    for attempt in range(max_retries):

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            timeout=60
        )

        # ========================
        # 429 → retry exponential
        # ========================
        if response.status_code == 429:
            wait_time = 3 * (attempt + 1)
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
            continue

        # ========================
        # 404 → model not found
        # ========================
        if response.status_code == 404:
            raise ValueError(
                f"Model '{model_name}' not found or not available for your key."
            )

        response.raise_for_status()

        data = response.json()
        output = data["choices"][0]["message"]["content"]

        return json.loads(output)

    raise RuntimeError("OpenRouter max retries exceeded")


def _call_openai(system_prompt, user_prompt):
    response = client_openai.chat.completions.create(
        model=GPT_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    output = response.choices[0].message.content
    return json.loads(output)


def call_llm(title: str, content: str, clients):

    user_prompt = f"""
Judul: {title}

Konten:
{content}

Client:
{clients}
""" 
    # ==========================
    # 1️⃣ Try OpenRouter MODEL 2
    # ==========================
    try:
        print("Trying OpenRouter MODEL 2...")
        return _call_openrouter(OPENROUTER_MODEL_NAME2, SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"OpenRouter MODEL2 failed: {e}")

    # ==========================
    # 2️⃣ Try OpenRouter MODEL 1
    # ==========================
    try:
        print("Trying OpenRouter MODEL 1...")
        return _call_openrouter(OPENROUTER_MODEL_NAME, SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"OpenRouter MODEL1 failed: {e}")

    # ==========================
    # 3️⃣ Fallback to OpenAI
    # ==========================
    try:
        print("Trying OpenAI...")
        return _call_openai(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"OpenAI failed: {e}")
        raise RuntimeError("All LLM providers failed.")