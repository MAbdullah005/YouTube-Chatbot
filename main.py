from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.db.session import SessionLocal
from backend.models.chat import ChatSession, ChatMessage
from backend.auth.routes import router as auth_router
from backend.auth.email import get_current_user
from backend.models.users import User
from backend.db.base import Base
from backend.db.session import engine

from backend.core.loader import load_youtube_transcript, extract_video_id
from backend.core.splitter import chunk_text
from backend.core.embeddings import get_embeddings
from backend.core.vectorstore import create_vector_db
from backend.core.rag_chain import build_rag_chain

from jose import jwt, JWTError
from backend.auth.jwt_utils import SECRET_KEY, ALGORITHM

app = FastAPI()

# ---------------- DB ----------------
Base.metadata.create_all(bind=engine)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROUTERS ----------------
app.include_router(auth_router, prefix="/auth")

# ---------------- STATIC ----------------
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# =========================
# PAGE ROUTES
# =========================
@app.get("/")
def root():
    return FileResponse("frontend/auth.html")

@app.get("/chat")
def serve_chat():
    return FileResponse("frontend/index.html")


# =========================
# RAG CACHE (per user + video)
# =========================
rag_cache = {}

class AskRequest(BaseModel):
    video_url: str
    question: str


# =====================================================
# STREAM ANSWER (MAIN WORKING ENDPOINT)
# =====================================================
@app.get("/stream")
async def stream_answer(
    video_url: str,
    question: str,
    token: str = Query(...)
):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    video_id = extract_video_id(video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    cache_key = f"{user_id}_{video_id}"

    if cache_key not in rag_cache:
        text = load_youtube_transcript(video_url)

        if not text.strip():
            return StreamingResponse(
                iter(["data: Transcript not available\n\n", "data: [DONE]\n\n"]),
                media_type="text/event-stream",
            )

        chunks = chunk_text(text)
        embeddings = get_embeddings()
        vector_db = create_vector_db(chunks, embeddings)

        rag_cache[cache_key] = build_rag_chain(
            vector_db,
            session_key=cache_key
        )

    rag = rag_cache[cache_key]

    def event_generator():
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter_by(
                user_id=user_id,
                video_id=video_id
            ).first()

            if not session:
                session = ChatSession(user_id=user_id, video_id=video_id)
                db.add(session)
                db.commit()
                db.refresh(session)

            db.add(ChatMessage(
                session_id=session.id,
                role="user",
                content=question
            ))
            db.commit()

            answer_chunks = []

            for chunk in rag.stream(question):
                answer_chunks.append(chunk)
                yield f"data: {chunk}\n\n"

            full_answer = "".join(answer_chunks)

            db.add(ChatMessage(
                session_id=session.id,
                role="assistant",
                content=full_answer
            ))
            db.commit()

            yield "data: [DONE]\n\n"

        finally:
            db.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# =====================================================
# CHAT HISTORY
# =====================================================
@app.get("/chat/history")
def get_chat_history(
    video_url: str,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    video_id = extract_video_id(video_url)
    if not video_id:
        return []

    session = db.query(ChatSession).filter_by(
        user_id=current_user.id,
        video_id=video_id
    ).first()

    if not session:
        return []

    messages = db.query(ChatMessage).filter_by(
        session_id=session.id
    ).order_by(ChatMessage.created_at).all()

    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


# =====================================================
# USER VIDEO SESSIONS
# =====================================================
@app.get("/chat/sessions")
def get_user_sessions(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    sessions = db.query(ChatSession).filter_by(
        user_id=current_user.id
    ).order_by(ChatSession.created_at.desc()).all()

    return [
        {
            "video_id": s.video_id,
            "created_at": s.created_at.isoformat()
        }
        for s in sessions
    ]
