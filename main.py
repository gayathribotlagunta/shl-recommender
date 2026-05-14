from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from agent import get_agent_reply

app = FastAPI(title="SHL Assessment Recommender")


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")
    
    # Validate roles
    for msg in request.messages:
        if msg.role not in ["user", "assistant"]:
            raise HTTPException(status_code=400, detail=f"Invalid role: {msg.role}")
    
    # Convert to dicts
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    
    # Get agent reply
    result = get_agent_reply(messages)
    
    # Build response
    recommendations = []
    for rec in result.get("recommendations", []):
        recommendations.append(Recommendation(
            name=rec.get("name", ""),
            url=rec.get("url", ""),
            test_type=rec.get("test_type", "")
        ))
    
    return ChatResponse(
        reply=result.get("reply", ""),
        recommendations=recommendations,
        end_of_conversation=result.get("end_of_conversation", False)
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)