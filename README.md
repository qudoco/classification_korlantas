# Classification Korlantas
<br>This project involves classification tasks related to Korlantas data. It leverages machine learning models to process and classify traffic-related data for the Indonesian National Police (Polri).

## Installation Instructions<br>

To set up the project on your local machine, follow these steps:
1. Clone the repository:<br>
```bash git clone https://github.com/your-username/classification_korlantas.git```
2. Navigate to the project directory:<br>
```bash cd classification_korlantas-main```

## Docker Setup<br>

To run the project with Docker, follow these steps:
1. Build the Docker image:<br>
```bash\n docker-compose up --build\n ```

## file .env
# ===============================
# OPENAI
# ===============================
OPENAI_API_KEY=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

# Model default kalau pakai OpenAI langsung
OPENAI_MODEL=gpt-5-mini-2025-08-07

# ===============================
# OPENROUTER
# ===============================
OPENROUTER_API_KEY=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

# Model bisa diganti:
# openai/gpt-4o-mini
# anthropic/claude-3.5-sonnet
# mistralai/mistral-large
OPENROUTER_MODEL_NAME2=qwen/qwen3-235b-a22b-2507
OPENROUTER_MODEL_NAME=google/gemma-3-27b-it

# ===============================
# REDIS (Celery Broker & Backend)
# ===============================
REDIS_URL=redis://redis:6379/0
#REDIS_URL=redis://localhost:6379/0

# ===============================
# CELERY CONFIG
# ===============================
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIMEOUT=120
CELERY_MAX_RETRIES=3
