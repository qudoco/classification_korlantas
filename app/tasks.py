from celery import Celery
import requests
import logging

from .config import REDIS_URL
from .llm import call_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery = Celery("tasks", broker=REDIS_URL, backend=REDIS_URL)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=5,           # mulai 5 detik
    retry_backoff_max=60,      # max 1 menit
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def scoring_task(self, payload):

    try:
        relevances = call_llm(
            payload["title"],
            payload["content"],
            payload["client"]
        )

        result = {
            "statusCode": 200,
            "message": "success",
            "data": {
                "id": payload["id"],
                "mediaId": payload["mediaId"],
                "relevances": relevances,
            }
        }

        # callback
        if payload.get("urlCallback"):
            try:
                response = requests.post(
                    payload["urlCallback"],
                    json=result,
                    timeout=300
                )

                logger.info(f"Callback status: {response.status_code}")

                if response.status_code != 200:
                    logger.warning(
                        f"Callback failed | status={response.status_code} | body={response.text}"
                    )

                # jika mau dianggap error dan retry
                response.raise_for_status()

            except requests.exceptions.RequestException as err:
                logger.error(f"Callback request error: {err}")
                raise

    except Exception as e:
        logger.exception("Error in scoring_task")
        raise e