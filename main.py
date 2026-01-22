from fastapi import FastAPI, Request
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

app = FastAPI()

# Cache for RAG chains per video
rag_cache = {"question_no": 0}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

# Request body model
class AskRequest(BaseModel):
    video_url: str
    question: str

# Normal non-streaming endpoint
@app.post("/ask")
async def ask_youtube(request: AskRequest):
    start = time.perf_counter()
    video_url = request.video_url
    video_id = extract_video_id(video_url)
    rag_cache["question_no"] += 1

    # Build RAG chain if not exists
    if video_id not in rag_cache:
        text = load_youtube_transcript(video_url)
        if not text.strip():
            return {"answer": "Transcript not available for this video."}
        chunks = chunk_text(text)
        embeddings = get_embeddings()
        db = create_vector_db(chunks, embeddings)
        rag_cache[video_id] = {"rag": build_rag_chain(db)}

    rag = rag_cache[video_id]["rag"]

    answer = rag(request.question)
    total_time = time.perf_counter() - start

    print(f"Question #{rag_cache['question_no']} | Time: {round(total_time,2)}s")
    print("Answer:", answer["answer"])

    return {"answer": answer["answer"], "evaluations": answer["Evaluation"]}


# ✅ Streaming endpoint
@app.get("/stream")
async def stream_answer(video_url: str, question: str):
    video_id = extract_video_id(video_url)
    rag_cache["question_no"] += 1

    # Build RAG if not exists
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
        # Assuming your rag function supports streaming via llm.stream
        for chunk, meta in rag.stream(question):
            if chunk.content:
                yield f"data: {chunk.content}\n\n"  # SSE format

        yield "data: [DONE]\n\n"  # End signal

    return StreamingResponse(event_generator(), media_type="text/event-stream")
