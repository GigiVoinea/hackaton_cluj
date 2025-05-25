# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
from orchestrator import Orchestrator

app = FastAPI()

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chat Models
class ChatMessage(BaseModel):
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

class ChatSession(BaseModel):
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

class SendMessageRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class SendMessageResponse(BaseModel):
    session_id: str
    message: ChatMessage
    status: str

# Legacy models for backward compatibility
class WorkflowInput(BaseModel):
    user_message: str

class WorkflowResult(BaseModel):
    status: str
    output: str | None = None
    messages: list = None

# In-memory session storage (in production, use Redis or database)
chat_sessions: dict[str, ChatSession] = {}

orchestrator = Orchestrator()

@app.get("/")
def read_root():
    return {"message": "Agentic Workflow API is running."}

# Chat endpoints
@app.post("/chat/send", response_model=SendMessageResponse)
async def send_message(request: SendMessageRequest):
    # Create new session if none provided
    if not request.session_id:
        session_id = str(uuid.uuid4())
        chat_sessions[session_id] = ChatSession(
            session_id=session_id,
            messages=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    else:
        session_id = request.session_id
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    
    # Add user message
    user_message = ChatMessage(
        id=str(uuid.uuid4()),
        role="user",
        content=request.message,
        timestamp=datetime.now()
    )
    session.messages.append(user_message)
    
    # Get AI response using orchestrator with conversation history
    try:
        result = await orchestrator.run_with_history(request.message, session.messages)
        print(f"Orchestrator result: {result}")  # Debug log
        
        # Extract content from the last AI message in the result
        output_content = result.get("output")
        if not output_content:
            # Try to extract from the last message in the messages array
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    output_content = last_message.content
                else:
                    print(f"Last message has no content: {last_message}")
                    output_content = "I'm sorry, I couldn't process that request."
            else:
                print(f"No messages in result. Full result: {result}")
                output_content = "I'm sorry, I couldn't process that request."
        
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=output_content,
            timestamp=datetime.now()
        )
        session.messages.append(assistant_message)
        session.updated_at = datetime.now()
        
        return SendMessageResponse(
            session_id=session_id,
            message=assistant_message,
            status="success"
        )
    except Exception as e:
        print(f"Error in chat processing: {str(e)}")  # Debug log
        import traceback
        traceback.print_exc()  # Print full stack trace
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/chat/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_sessions[session_id]

@app.get("/chat/sessions")
async def list_chat_sessions():
    return {"sessions": list(chat_sessions.keys())}

@app.delete("/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    del chat_sessions[session_id]
    return {"message": "Session deleted successfully"}

# Legacy endpoint for backward compatibility
@app.post("/run-workflow", response_model=WorkflowResult)
async def run_workflow(input: WorkflowInput):
    result = await orchestrator.run(input.user_message)
    return WorkflowResult(
        status="success",
        output=result.get("output"),
        messages=result.get("messages", [])
    ) 