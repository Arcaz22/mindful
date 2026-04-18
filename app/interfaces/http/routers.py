from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.di import get_chat_use_case
from app.core.di import llm_client
from app.domain.llm.exceptions import DigitalWellbeingException
from app.presentatation.schemas.chat_schema import ChatRequest, ChatResponse

router = APIRouter()


@router.get("/health")
async def health(llm=Depends(llm_client)):
    llm_status = await llm.check_connection()
    return {
        "status": "ok" if llm_status["ok"] else "degraded",
        "ollama": llm_status,
    }

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, use_case=Depends(get_chat_use_case), raw_req: Request = None):
    try:
        return await use_case.execute(
            request.user_id,
            request.message,
            fingerprint=request.visitor_id
        )
    except DigitalWellbeingException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
