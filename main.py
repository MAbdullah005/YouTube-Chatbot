from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel  # <-- import this

from backend.core.loader import load_youtube_transcript
from backend.core.splitter import chunk_text
from backend.core.embeddings import get_embeddings
from backend.core.vectorstore import create_vector_db
from backend.core.rag_chain import build_rag_chain

app = FastAPI()
rag_cache={}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")


# ✅ Define a Pydantic model for the request body
class AskRequest(BaseModel):
    video_url: str
    question: str

@app.post("/ask")
def ask_youtube(request: AskRequest):

    video_url = request.video_url

    #  Reuse RAG if already built for this video
    if video_url not in rag_cache:
        text = load_youtube_transcript(video_url)

        if not text.strip():
            return {"answer": "Transcript not available for this video."}

        chunks = chunk_text(text)
        embeddings = get_embeddings()
        db = create_vector_db(chunks, embeddings)
        rag_cache[video_url] = build_rag_chain(db)

    rag = rag_cache[video_url]
    answer = rag(request.question)

    return {"answer": answer}
