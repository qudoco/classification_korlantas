import asyncio
import httpx
import json
import requests
import time
#from openai import OpenAI
from openai import AsyncOpenAI
from .config import (
    OPENAI_API_KEY,
    GPT_MODEL_NAME,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL_NAME,
    OPENROUTER_MODEL_NAME2
)

SYSTEM_PROMPT = """
You are an AI system that evaluates the relevance of a news article to a list of client organizations. 

Your task is to analyze the given news input and determine how relevant the article is for each client listed. 

Input structure: 
* title: news title 
* content: full news article 
* client: list of client organization names 

--- 

INSTRUCTIONS: 
1. Read and understand the title and full content of the article. 
2. Identify the main topic, key entities, institutions involved, and overall context. 
3. Evaluate relevance for EACH client provided in the input. 

--- 

RELEVANCE RULE: 
For each client: 
* "relevan": true → if the article has meaningful connection to the client 
* "relevan": false → if there is no clear or significant connection 

Score guideline: 
* 0.0–0.3 → Not relevant 
* 0.4–0.6 → Slightly related 
* 0.7–0.8 → Clearly relevant 
* 0.9–1.0 → Highly relevant 

--- 

IMPORTANT RULES: 
* Do NOT assume relevance without textual evidence. 
* Be objective and conservative in scoring. 
* Do NOT include explanations or commentary. 
* Output ONLY valid JSON. 

--- 

Special routing rules (ONLY apply when client is NOT provided or empty): 

If the article contains any relationship, mention, or contextual relevance to the following keywords or entities: 

Korlantas Polri, Kakorlantas Polri, Irjen Agus Suryonugroho, Operasi Keselamatan, Operasi Ketupat, 
Polantas Menyapa, mudik lebaran, arus mudik, arus balik, one way tol japek, jadwal ganjil genap, 
jadwal one way, jalan pulang, koorlantas 

→ Then automatically assign client: ["Korlantas Polri"]

If NONE of the keywords are found:
→ Then assign client: ["Multipool"]

--- 

OUTPUT FORMAT (STRICT): 

Return JSON with structure:

[
    {
      "client": string,
      "relevan": boolean,
      "score": float
    }
]

--- 

OUTPUT RULES: 

* The number of objects inside "relevances" MUST match the number of clients in the input array.
* **If 1 client → output 1 object**
* **If 2 clients → output 2 objects**
* **If N clients → output N objects**
* **DO NOT add or remove clients**
* Preserve client names EXACTLY as provided
* DO NOT wrap with additional fields
* DO NOT return explanations

--- 

VALID OUTPUT EXAMPLES:

Input client: ["Korlantas Polri"]

[
    {
      "client": "Korlantas Polri",
      "relevan": false,
      "score": 0.2
    }
]

Input client: ["Korlantas Polri", "Multipool"]

[
    {
      "client": "Multipool",
      "relevan": true,
      "score": 0.8
    },
    {
      "client": "Korlantas Polri",
      "relevan": false,
      "score": 0.2
    }
]

--- 

VALIDATION RULE: 
If the output does not strictly follow the *JSON structure above, it is INVALID.*
"""

client_openai = AsyncOpenAI(api_key=OPENAI_API_KEY)

semaphore = asyncio.Semaphore(5)

# =========================
# SAFE JSON PARSER
# =========================
def _safe_json_loads(output: str):
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print("⚠️ JSON invalid, retry cleaning...")
        # simple fix attempt
        output = output.strip().replace("```json", "").replace("```", "")
        return json.loads(output)

async def _call_openrouter(model_name, system_prompt, user_prompt, max_retries=3):

    url = "https://openrouter.ai/api/v1/chat/completions"

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

    if "gpt-oss" in model_name:
        payload["reasoning"] = {"enabled": True}

    async with httpx.AsyncClient(timeout=60) as client:

        for attempt in range(max_retries):
            try:
                async with semaphore:
                    response = await client.post(url, headers=headers, json=payload)

                # 429 retry
                if response.status_code == 429:
                    wait_time = 2 ** attempt
                    print(f"[OpenRouter] Rate limited. Wait {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue

                # 404 model not found
                if response.status_code == 404:
                    raise ValueError(f"Model '{model_name}' not found.")

                response.raise_for_status()

                data = response.json()
                output = data["choices"][0]["message"]["content"]

                return _safe_json_loads(output)

            except Exception as e:
                print(f"[OpenRouter] attempt {attempt+1} failed: {e}")
                await asyncio.sleep(1)

    raise RuntimeError("OpenRouter max retries exceeded")

async def _call_openai(system_prompt, user_prompt):
    async with semaphore:
        response = await client_openai.chat.completions.create(
            model=GPT_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

    output = response.choices[0].message.content
    return _safe_json_loads(output)


async def call_llm(title: str, content: str, clients):

    user_prompt = f"""
Judul: {title}

Konten:
{content}

Client:
{clients}
""" 
    # ==========================
    # 3️⃣ Try OpenAI
    # ==========================
    try:
        print("Trying OpenAI...")
        return await _call_openai(SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"OpenAI failed: {e}")

    # ==========================
    # 1️⃣ Try OpenRouter MODEL 2
    # ==========================
    try:
        print("Trying OpenRouter MODEL 2...")
        return await _call_openrouter(OPENROUTER_MODEL_NAME2, SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"OpenRouter MODEL2 failed: {e}")

    # ==========================
    # 2️⃣ Try OpenRouter MODEL 1
    # ==========================
    try:
        print("Trying OpenRouter MODEL 1...")
        return await _call_openrouter(OPENROUTER_MODEL_NAME, SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"OpenRouter MODEL1 failed: {e}")    
        raise RuntimeError("All LLM providers failed.")