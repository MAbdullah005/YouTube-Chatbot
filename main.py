from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import time
from backend.core.loader import load_youtube_transcript, extract_video_id
from backend.core.splitter import chunk_text
from backend.core.embeddings import get_embeddings
from backend.core.vectorstore import create_vector_db
from backend.core.rag_chain import build_rag_chain

# Test sample video of 
# https://www.youtube.com/watch?v=FCG6pVGPn9I  

app = FastAPI()

# RAG cache
rag_cache = {"question_no": 0}

# CORS
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

# Request body
class AskRequest(BaseModel):
    video_url: str
    question: str

# Non-streaming (optional)
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
    return {"answer": answer["answer"], "evaluations": answer["Evaluation"]}

# Streaming endpoint
@app.get("/stream")
async def stream_answer(video_url: str, question: str):
    video_id = extract_video_id(video_url)
    rag_cache["question_no"] += 1

    if video_id not in rag_cache:
        text = load_youtube_transcript(video_url)
        if not text.strip():
            return StreamingResponse(iter(["Transcript not available"]), media_type="text/event-stream")
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
