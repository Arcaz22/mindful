from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.di import get_chat_use_case
from app.domain.llm.exceptions import DigitalWellbeingException
from app.presentatation.schemas.chat_schema import ChatRequest, ChatResponse

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, use_case=Depends(get_chat_use_case), raw_req: Request = None):
    try:
        return await use_case.execute(
            request.user_id,
            request.message,
            fingerprint=request.visitor_id
        )
    except DigitalWellbeingException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
