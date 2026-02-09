from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.auth.routes import router as auth_router
from backend.db.base import Base
from backend.db.session import engine

from backend.core.loader import load_youtube_transcript, extract_video_id
from backend.core.splitter import chunk_text
from backend.core.embeddings import get_embeddings
from backend.core.vectorstore import create_vector_db
from backend.core.rag_chain import build_rag_chain


# ---------------- APP ----------------
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
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

# ---------------- STATIC FILES ----------------
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def serve_chatbot():
    return FileResponse("frontend/index.html")


@app.get("/auth")
def serve_auth():
    return FileResponse("frontend/auth.html")


# ---------------- RAG CACHE ----------------
rag_cache = {"question_no": 0}


# ---------------- REQUEST BODY ----------------
class AskRequest(BaseModel):
    video_url: str
    question: str


# ---------------- NON-STREAM ----------------
@app.post("/ask")
async def ask_youtube(request: AskRequest):
    video_url = request.video_url
    question = request.question

    video_id = extract_video_id(video_url)
    rag_cache["question_no"] += 1

    if video_id not in rag_cache:
        text = load_youtube_transcript(video_url)
        if not text.strip():
            return {"answer": "Transcript not available."}

        chunks = chunk_text(text)
        embeddings = get_embeddings()
        db = create_vector_db(chunks, embeddings)
        rag_cache[video_id] = {"rag": build_rag_chain(db)}

    rag = rag_cache[video_id]["rag"]
    answer = rag(question)

    return {
        "answer": answer["answer"],
        "evaluations": answer.get("Evaluation"),
    }


# ---------------- STREAM ----------------
@app.get("/stream")
async def stream_answer(video_url: str, question: str):
    video_id = extract_video_id(video_url)
    rag_cache["question_no"] += 1

    if video_id not in rag_cache:
        text = load_youtube_transcript(video_url)
        if not text.strip():
            return StreamingResponse(
                iter(["Transcript not available"]),
                media_type="text/event-stream",
            )

        chunks = chunk_text(text)
        embeddings = get_embeddings()
        db = create_vector_db(chunks, embeddings)
        rag_cache[video_id] = {"rag": build_rag_chain(db)}

    rag = rag_cache[video_id]["rag"]

    def event_generator():
        for chunk in rag.stream(question):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
