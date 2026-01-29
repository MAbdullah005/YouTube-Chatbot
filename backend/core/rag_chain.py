from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
import time
from langchain.messages import HumanMessage
from backend.core.memorey import get_memory
from backend.evaluation.retrieval_eval import evaluate_retrieval
from backend.evaluation.grounding_eval import evaluation_grounding
from backend.evaluation.llm_eval import llm_faithfullness_eval

template = """
You are a YouTube Video Chatbot.
Use the following context and chat history to answer the question.
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
        input_variables=["chat_history", "context", "question"],
        template=template
    )

    retriever = vector_db.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    class RAG:
        def __init__(self):
            self.llm = llm
            self.prompt = prompt
            self.memory = memory
            self.retriever = retriever
            self.last_context = None  # store context for streaming

        # Standard non-streaming method
        def __call__(self, query: str):
            # Retrieve docs
            retrieved_docs = self.retriever.invoke(query)
            context = "\n\n".join(doc.page_content for doc in retrieved_docs)
            self.last_context = context
            retrieval_score = evaluate_retrieval(query, context)

            # Load chat history
            chat_history = self.memory.load_memory_variables({}).get("chat_history", "")

            # Build prompt
            final_prompt = self.prompt.invoke({
                "chat_history": chat_history,
                "context": context,
                "question": query
            })
            human_msg = HumanMessage(str(final_prompt))

            # Stream internally but collect full text
            answer_chunks = []
            for chunk in self.llm.stream([human_msg], config={"configurable": {"thread_id": "thread-1"}}):
                if chunk.content:
                    answer_chunks.append(chunk.content)
                    print(chunk.content, end="", flush=True)  # debug optional

            answer_text = "".join(answer_chunks)
            self.memory.save_context({"question": query}, {"answer": answer_text})

            # Optional evaluations
            grounding_score = evaluation_grounding(answer_text, context)
            llm_eval = llm_faithfullness_eval(self.llm, context, answer_text)

            return {
                "answer": answer_text,
                "Evaluation": {
                    "retrieval_time": retrieval_score,
                    "Grounding_score": grounding_score,
                    "LLM_Evaluation": llm_eval
                }
            }

        # ✅ New streaming generator method
        def stream(self, query: str ):
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
    return RAG()
