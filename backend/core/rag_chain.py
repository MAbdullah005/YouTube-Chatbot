from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama   
import time
from langchain_core.runnables import RunnablePassthrough,RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from backend.evaluation.retrieval_eval import evaluate_retrieval
from backend.evaluation.grounding_eval import evaluation_grounding
from langgraph.checkpoint.memory import InMemorySaver
from backend.evaluation.latency_eval import latency_eval
from langchain.messages import HumanMessage
from backend.evaluation.llm_eval import llm_faithfullness_eval
#from backend.evaluation import grounding_eval,llm_eval,retrieval_eval
from backend.core.memorey import get_memory
# from langchain_ollama import OllamaEmbeddings  # (Not used here)

template = """
You are a YouTube Video Chatbot.
Use the following context and chat history to answer the question .
If the answer is not in the video, say "Not found in video".

CHAT HISTORY:
{chat_history}

CONTEXT:
{context}

QUESTION:
{question}
"""

def build_rag_chain(vector_db):
    llm = ChatOllama(model="llama3.2:1b", temperature=0.2, num_predict=256)
    memory = get_memory()

    prompt = PromptTemplate(
        input_variables=["chat_history","context", "question"],
        template=template
    )

    retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    def rag(query: str):
        # Retrieve docs
        retrieved_docs = retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)
        retrieval_score = evaluate_retrieval(query, context)

        # Load chat history
        chat_history = memory.load_memory_variables({}).get("chat_history", "")

        # Build prompt
        final_prompt = prompt.invoke({
            "chat_history": chat_history,
            "context": context,
            "question": query
        })
        human_msg = HumanMessage(str(final_prompt))


        # Stream response
        answer_chunks = []
        for chunk, meta in llm.stream(
            [human_msg],
            config={"configurable":{"thread_id":"thread-1"}},
            stream_model="message"
        ):
            if chunk.content:
                answer_chunks.append(chunk.content)
                # Here you could also push the chunk to frontend via WebSocket
                print(chunk.content, end="", flush=True)  # optional: debug streaming

        answer_text = "".join(answer_chunks)

        # Save full answer to memory
        memory.save_context({"question": query}, {"answer": answer_text})

        # Optional evaluations
        grounding_score = evaluation_grounding(answer_text, context)
        llm_eval = llm_faithfullness_eval(llm, context, answer_text)

        return {
            "answer": answer_text,
            "Evaluation": {
                "retrieval_time": retrieval_score,
                "Grounding_score": grounding_score,
                "LLM_Evaluation": llm_eval
            }
        }

    return rag