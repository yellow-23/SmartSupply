from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models.orm import User
from app.services import stocky_service

router = APIRouter()


class StockyChatRequest(BaseModel):
    messages: list[dict]
    business_id: int


class StockyChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=StockyChatResponse)
def stocky_chat(
    body: StockyChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reply = stocky_service.chat(db, body.business_id, body.messages)
    return StockyChatResponse(reply=reply)
