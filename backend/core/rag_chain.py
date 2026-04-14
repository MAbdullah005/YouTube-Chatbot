from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage
from backend.core.memorey import get_memory
from backend.evaluation.retrieval_eval import evaluate_retrieval
from backend.evaluation.grounding_eval import evaluation_grounding
from backend.evaluation.llm_eval import llm_faithfullness_eval

template = """
You are an AI assistant that answers questions strictly based on a YouTube video transcript.

RULES:
1. Use ONLY the provided CONTEXT to answer.
2. Do NOT use outside knowledge.
3. Do NOT guess.
4. Do NOT hallucinate.
5. If the answer is not clearly present in the context, respond exactly with:
   "I could not find this information in the video. Please try asking another question."

STYLE:
- Be clear and concise.
- Be professional and helpful.
- Do not mention the context or transcript in your answer.
- Do not explain your reasoning unless explicitly asked.

CHAT HISTORY:
{chat_history}

CONTEXT:
{context}

QUESTION:
{question}
"""


def build_rag_chain(vector_db, session_key: str):

    llm = ChatOllama(model="qwen2.5:7b", temperature=0.2, num_predict=256)

    # ✅ FIXED: dynamic session memory
    memory = get_memory(session_id=session_key)

    prompt = PromptTemplate(
        input_variables=["chat_history", "context", "question"],
        template=template
    )

    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )

    class RAG:
        def __init__(self):
            self.llm = llm
            self.prompt = prompt
            self.memory = memory
            self.retriever = retriever

        def __call__(self, query: str):

            retrieved_docs = self.retriever.invoke(query)
            context = "\n\n".join(doc.page_content for doc in retrieved_docs)

            chat_history = self.memory.load_memory_variables({}).get(
                "chat_history", ""
            )

            final_prompt = self.prompt.invoke({
                "chat_history": chat_history,
                "context": context,
                "question": query
            })

            human_msg = HumanMessage(str(final_prompt))

            answer_chunks = []

            for chunk in self.llm.stream(
                [human_msg],
                config={"configurable": {"thread_id": session_key}}
            ):
                if chunk.content:
                    answer_chunks.append(chunk.content)

            answer_text = "".join(answer_chunks)

            self.memory.save_context(
                {"question": query},
                {"answer": answer_text}
            )

            return {"answer": answer_text}

        def stream(self, query: str):

            retrieved_docs = self.retriever.invoke(query)
            context = "\n\n".join(doc.page_content for doc in retrieved_docs)

            chat_history = self.memory.load_memory_variables({}).get(
                "chat_history", ""
            )

            final_prompt = self.prompt.invoke({
                "chat_history": chat_history,
                "context": context,
                "question": query
            })

            human_msg = HumanMessage(str(final_prompt))

            full_answer = []

            for chunk in self.llm.stream(
                [human_msg],
                config={"configurable": {"thread_id": session_key}}
            ):
                if chunk.content:
                    full_answer.append(chunk.content)
                    yield chunk.content

            self.memory.save_context(
                {"question": query},
                {"answer": "".join(full_answer)}
            )

    return RAG()
