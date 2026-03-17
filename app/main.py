from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult

from .tasks import scoring_task, celery
from .schemas import NewsRequest

router = APIRouter(
    prefix="/news_classify",
    tags=["classify"]
)

@router.post("/predict")
async def predict(news: NewsRequest):

    task = scoring_task.delay(news.dict())

    return {
        "statusCode": 202,
        "message": "processing",
        "task_id": task.id
    }

"""
@router.get("/predict/result/{task_id}")
async def get_result(task_id: str):

    task = AsyncResult(task_id, app=celery)

    if task.state == "PENDING":
        return {"status": "pending"}

    if task.state == "STARTED":
        return {"status": "processing"}

    if task.state == "SUCCESS":
        return task.result

    if task.state == "FAILURE":
        return {
            "status": "failed",
            "error": str(task.info)
        }

    return {"status": task.state}
"""

app = FastAPI(
    title="Classify News for Multipool and Korlantas",
    description="API for classifying news multipool or korlantas",
    version="0.1.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/v1")