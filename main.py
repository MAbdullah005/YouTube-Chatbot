from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel  # <-- import this

from backend.core.loader import load_youtube_transcript
from backend.core.splitter import chunk_text
from backend.core.embeddings import get_embeddings
from backend.core.loader import extract_video_id
import time
from backend.core.vectorstore import create_vector_db
from backend.core.rag_chain import build_rag_chain

app = FastAPI()
rag_cache={}
questions_no=1
rag_cache["question_no"]=0

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
    start=time.perf_counter()
    video_url = request.video_url
    video_id=extract_video_id(video_url)
    rag_cache["question_no"]+=1
    #questions_no=questions_no+1

    #  Reuse RAG if already built for this video
    if video_id not in rag_cache:
        
        text = load_youtube_transcript(video_url)

        if not text.strip():
            return {"answer": "Transcript not  available for this video."}

        chunks = chunk_text(text)
        embeddings = get_embeddings()
        db = create_vector_db(chunks, embeddings)
       # rag_cache[video_id] = db
        rag_cache[video_id] = {
        "db": db,
        "rag": build_rag_chain(db)
        }
        

    #rag = rag_cache[video_url]
   # rag = build_rag_chain(rag_cache[video_id])
    rag = rag_cache[video_id]["rag"]
    answer = rag(request.question)
    end_time=time.perf_counter()
    total_time=end_time-start
    print(f"Execution took Question { rag_cache["question_no"]} got time {total_time} ")

    return {"answer": answer}
