from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from memo_agent.api.schemas import ChatRequest, ChatResponse
from memo_agent.api.deps import get_session_manager

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_manager = get_session_manager()

    if request.session_id and request.session_id != session_manager.conversation_id:
        session_manager.start_session()

    if not session_manager.conversation_id:
        session_manager.start_session()

    result = session_manager.process_turn(request.message)

    return ChatResponse(
        response=result.response,
        session_id=session_manager.conversation_id,
        entities=result.entities,
        guidelines_used=result.guidelines_used,
        is_reflection=result.is_reflection,
        guideline=result.guideline.rule if result.guideline else None,
    )


@router.websocket("/chat/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    session_manager = get_session_manager()

    if not session_manager.conversation_id:
        session_manager.start_session()

    try:
        while True:
            data = await websocket.receive_text()
            result = session_manager.process_turn(data)
            await websocket.send_text(result.response)
            await websocket.send_text("[DONE]")
    except WebSocketDisconnect:
        pass
