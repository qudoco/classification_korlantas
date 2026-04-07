from celery import Celery
import requests
import logging
import time
import json
import redis

from .config import REDIS_URL
from .llm import call_llm

# ========================
# LOGGING
# ========================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_VERSION = "0.1.4"

# ========================
# CELERY
# ========================
celery = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# ========================
# REDIS TRACKING
# ========================
redis_client = redis.Redis.from_url(REDIS_URL)


@celery.task(
    bind=True,
    autoretry_for=(requests.exceptions.RequestException,),
    retry_backoff=5,
    retry_backoff_max=60,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def scoring_task(self, payload):
    start_time = time.time()
    task_id = self.request.id

    # ========================
    # TRACK QUEUE
    # ========================
    redis_client.lrem("job_pending", 0, task_id)
    redis_client.lpush("job_active", task_id)

    logger.info("=" * 50)
    logger.info(f"[WORKER] version={APP_VERSION}")
    logger.info(f"[TASK START] ID={payload.get('id')} | task_id={task_id}")
    logger.info("=" * 50)

    try:
        # ========================
        # UPDATE STATE
        # ========================
        self.update_state(state="STARTED")

        # ========================
        # CALL LLM
        # ========================
        relevances = call_llm(
            payload["title"],
            payload["content"],
            payload["client"]
        )

        # ========================
        # BUILD RESULT
        # ========================
        result = {
            "statusCode": 200,
            "message": "success",
            "data": {
                "id": payload["id"],
                "mediaId": payload["mediaId"],
                "relevances": relevances,
            }
        }

        # ========================
        # CALLBACK
        # ========================
        if payload.get("urlCallback"):
            callback_url = payload["urlCallback"]

            logger.info(f"[CALLBACK URL] {callback_url}")

            # print payload yang dikirim (pretty JSON biar enak dibaca)
            logger.info("[CALLBACK PAYLOAD]")
            logger.info(json.dumps(result, indent=2))

            try:
                response = requests.post(
                    callback_url,
                    json=result,
                    timeout=15
                )

                logger.info(f"[CALLBACK STATUS] {response.status_code}")
                logger.info(f"[CALLBACK RESPONSE] {response.text}")

                if response.status_code != 200:
                    logger.warning(
                        f"[CALLBACK FAILED] status={response.status_code}"
                    )
                    return

                logger.info("[CALLBACK SUCCESS]")

            except requests.exceptions.RequestException as err:
                logger.error(f"[CALLBACK ERROR] {err}")
                raise err

        # ========================
        # MOVE QUEUE
        # ========================
        redis_client.lrem("job_active", 0, task_id)
        redis_client.lpush("job_done", task_id)

        duration = time.time() - start_time
        logger.info(f"[TASK DONE] {task_id} | {duration:.2f}s")

        return result

    except Exception as e:
        logger.exception(f"[TASK ERROR] {task_id}")

        redis_client.lrem("job_active", 0, task_id)
        redis_client.lpush("job_failed", task_id)

        raise e
