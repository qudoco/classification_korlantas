from fastapi import FastAPI, BackgroundTasks
from .tasks import scoring_task
from .schemas import NewsRequest
from .tasks import celery  
from celery.result import AsyncResult

app = FastAPI()


@app.post("/predict")
async def predict(news: NewsRequest):
    task = scoring_task.delay(news.dict())

    return {
        "statusCode": 202,
        "message": "processing",
        "task_id": task.id
    }

@app.get("/predict/result/{task_id}")
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