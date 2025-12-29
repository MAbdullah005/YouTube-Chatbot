from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama   
import time
from backend.evaluation.retrieval_eval import evaluate_retrieval
from backend.evaluation.grounding_eval import evaluation_grounding
from backend.evaluation.latency_eval import latency_eval
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

    llm = ChatOllama(model="llama3.2:1b",
                     temperature=0.2,num_predict=256)
    memory = get_memory()

    prompt = PromptTemplate(
        input_variables=["context", "question", "chat_history"],
        template=template
    )
    retriever = vector_db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
    


    def rag(query: str):

        retrival_time=time.perf_counter()
        
        retrieved_docs = retriever.invoke(query)
        retrival_time=time.perf_counter()-retrival_time
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)

        retrieval_score=evaluate_retrieval(query,context)


        #  Load chat history
        chat_history = memory.load_memory_variables({}).get("chat_history", "")

        #  Build final prompt
        print("chat history *** ",chat_history)
        final_prompt = prompt.invoke({
            "chat_history": chat_history,
            "context": context,
            "question": query
        })

        #  Call LLM
        response = llm.invoke(final_prompt)

        #  Save to memory
        memory.save_context(
            {"question": query},
            {"answer": response.content}
        )
        grounding_score=evaluation_grounding(response.content,context)
        llm_evaluation=llm_faithfullness_eval(llm,context,response.content)

        return {"Chatbot":response.content,
                "Evaluation":
                {
                'retrieval_time':retrieval_score,
                'Grounding_score':grounding_score,
                "LLm Evaluation":llm_evaluation
                }
                }

    return rag