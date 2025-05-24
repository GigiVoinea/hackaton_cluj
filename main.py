# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator import Orchestrator

app = FastAPI()

class WorkflowInput(BaseModel):
    user_message: str

class WorkflowResult(BaseModel):
    status: str
    result: dict = None

orchestrator = Orchestrator()

@app.get("/")
def read_root():
    return {"message": "Agentic Workflow API is running."}

@app.post("/run-workflow", response_model=WorkflowResult)
async def run_workflow(input: WorkflowInput):
    result = await orchestrator.run(input.user_message)
    return WorkflowResult(status=result.get("status", "ok"), result=result) 