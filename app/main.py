from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult
from contextlib import asynccontextmanager
import logging

from .tasks import scoring_task, celery
from .schemas import NewsRequest

# ========================
# CONFIG
# ========================
APP_NAME = "news-classifier"
APP_VERSION = "0.1.0"
APP_ENV = "production"

# ========================
# LOGGING
# ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | "
           f"{APP_NAME} | v={APP_VERSION} | %(message)s"
)

logger = logging.getLogger(__name__)

# ========================
# STARTUP LOG
# ========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    logger.info("🚀 ===============================")
    logger.info("🚀 APP STARTED")
    logger.info(f"🚀 name={APP_NAME}")
    logger.info(f"🚀 version={APP_VERSION}")
    logger.info(f"🚀 env={APP_ENV}")
    logger.info("🚀 ===============================")

    yield

    # SHUTDOWN (optional)
    logger.info("🛑 APP SHUTDOWN")


# ========================
# APP INIT
# ========================
app = FastAPI(
    title="Classify News for Multipool and Korlantas",
    description="API for classifying news multipool or korlantas",
    version=APP_VERSION,
    docs_url="/docs",
    lifespan=lifespan,  # 🔥 ini pengganti on_event
)

# ========================
# ROUTER
# ========================
router = APIRouter(
    prefix="/news_classify",
    tags=["classify"]
)


@router.post("/predict")
async def predict(news: NewsRequest):

    logger.info(
        f"[API REQUEST] id={news.id} | mediaId={news.mediaId} | client={news.client}"
    )

    payload = news.dict()

    logger.info(f"[API PAYLOAD KEYS] {list(payload.keys())}")
    logger.info(f"[API CALLBACK URL] {payload.get('urlCallback')}")

    task = scoring_task.delay(payload)

    logger.info(f"[TASK CREATED] task_id={task.id}")

    return {
        "statusCode": 202,
        "message": "processing",
        "task_id": task.id
    }


# ========================
# OPTIONAL RESULT CHECK
# ========================
@router.get("/predict/result/{task_id}")
async def get_result(task_id: str):

    logger.info(f"[CHECK RESULT] task_id={task_id}")

    task = AsyncResult(task_id, app=celery)

    if task.state == "PENDING":
        return {"status": "pending"}

    if task.state == "STARTED":
        return {"status": "processing"}

    if task.state == "SUCCESS":
        logger.info(f"[RESULT SUCCESS] task_id={task_id}")
        return task.result

    if task.state == "FAILURE":
        logger.error(f"[RESULT FAILED] task_id={task_id} | error={task.info}")
        return {
            "status": "failed",
            "error": str(task.info)
        }

    return {"status": task.state}


# ========================
# MIDDLEWARE
# ========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# REGISTER ROUTER
# ========================
app.include_router(router, prefix="/v1")
