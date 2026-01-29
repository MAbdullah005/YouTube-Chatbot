from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain.messages import HumanMessage
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import time
import json

from backend.core.loader import load_youtube_transcript, extract_video_id
from backend.core.splitter import chunk_text
from backend.core.embeddings import get_embeddings
from backend.core.vectorstore import create_vector_db
from backend.core.rag_chain import build_rag_chain

app = FastAPI()

rag_cache = {"question_no": 0}

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


class AskRequest(BaseModel):
    video_url: str
    question: str


@app.post("/ask")
async def ask_youtube(request: AskRequest):
    start = time.perf_counter()
    video_url = request.video_url
    video_id = extract_video_id(video_url)
    rag_cache["question_no"] += 1

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
def stream(self, query: str):
    retrieved_docs = self.retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in retrieved_docs)

    chat_history = self.memory.load_memory_variables({}).get("chat_history", "")

    final_prompt = self.prompt.invoke({
        "chat_history": chat_history,
        "context": context,
        "question": query
    })

    human_msg = HumanMessage(str(final_prompt))

    full_answer = []

    for chunk in self.llm.stream(
        [human_msg],
        config={"configurable": {"thread_id": "thread-1"}}
    ):
        if chunk.content:
            full_answer.append(chunk.content)
            yield chunk.content  # 🔥 stream to frontend

    # ✅ Save ONLY ONCE
    self.memory.save_context(
        {"question": query},
        {"answer": "".join(full_answer)}
    )

    def event_generator():
        for chunk in rag.stream(question):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield f"data: {json.dumps({'chunk': '[DONE]'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
