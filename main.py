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
    text = load_youtube_transcript(request.video_url)
    chunks = chunk_text(text)
    embeddings = get_embeddings()
    db = create_vector_db(chunks, embeddings)
    rag = build_rag_chain(db)

    answer = rag(request.question)
    return {"answer": answer}
