from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama   # <-- Correct LLM
# from langchain_ollama import OllamaEmbeddings  # (Not used here)

template = """
You are a YouTube Video Chatbot.
Use the following context to answer the question.
If the answer is not in the video, say "Not found in video".

CONTEXT:
{context}

QUESTION:
{question}
"""

def build_rag_chain(vector_db):

    # Correct LLM for answering
    llm = ChatOllama(model="llama3.2:1b")   # <-- FIXED

    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=template
    )

    def rag(query):
        docs = vector_db.similarity_search(query, k=4)
        context = "\n".join([d.page_content for d in docs])
        final_prompt = prompt.format(context=context, question=query)
        print("this is final prompt",final_prompt)

        # LLM can invoke
        response = llm.invoke(final_prompt)
        return response.content

    return rag
