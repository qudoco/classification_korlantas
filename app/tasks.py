from celery import Celery
import requests
import logging
import time

from .config import REDIS_URL
from .llm import call_llm

# logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL
)


@celery.task(
    bind=True,
    autoretry_for=(requests.exceptions.RequestException,),  # retry hanya network error
    retry_backoff=5,
    retry_backoff_max=60,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def scoring_task(self, payload):
    start_time = time.time()

    logger.info("=" * 50)
    logger.info(f"[TASK START] ID={payload.get('id')} | mediaId={payload.get('mediaId')}")
    logger.info(f"Client: {payload.get('client')}")
    logger.info("=" * 50)

    try:
        # ========================
        # 1. CALL LLM
        # ========================
        logger.info("Calling LLM...")

        relevances = call_llm(
            payload["title"],
            payload["content"],
            payload["client"]
        )

        logger.info("LLM predict success")

        # ========================
        # 2. BUILD RESULT
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

        logger.info(f"[RESULT READY] {result['data']['id']}")

        # ========================
        # 3. CALLBACK
        # ========================
        if payload.get("urlCallback"):
            callback_url = payload["urlCallback"]

            logger.info(f"Sending callback to {callback_url}")

            try:
                response = requests.post(
                    callback_url,
                    json=result,
                    timeout=15   # jangan 300, bahaya
                )

                logger.info(f"[CALLBACK STATUS] {response.status_code}")
                logger.info(f"[CALLBACK RESPONSE] {response.text}")

                if response.status_code != 200:
                    logger.warning(
                        f"[CALLBACK FAILED] status={response.status_code}"
                    )
                    # OPTIONAL: jangan retry kalau logic error
                    return

                logger.info("[CALLBACK SUCCESS]")

            except requests.exceptions.RequestException as err:
                logger.error(f"[CALLBACK ERROR] {err}")
                raise  # retry hanya network error

        else:
            logger.warning("[NO CALLBACK URL PROVIDED]")

        duration = time.time() - start_time
        logger.info(f"[TASK DONE] ID={payload.get('id')} | duration={duration:.2f}s")

        return result

    except Exception as e:
        logger.exception(f"[TASK ERROR] ID={payload.get('id')}")
        raise e
