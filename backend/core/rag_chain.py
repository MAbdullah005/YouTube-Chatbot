from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama   
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

    llm = ChatOllama(model="llama3.2:1b")
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

        
        retrieved_docs = retriever.invoke(query)
        context = "\n\n".join(doc.page_content for doc in retrieved_docs)

        #  Load chat history
        chat_history = memory.load_memory_variables({}).get("chat_history", "")

        #  Build final prompt
        final_prompt = prompt.invoke({
            "context": context,
            "question": query,
            "chat_history": chat_history
        })

        #  Call LLM
        response = llm.invoke(final_prompt)

        #  Save to memory
        memory.save_context(
            {"question": query},
            {"answer": response.content}
        )

        return response.content

    return rag