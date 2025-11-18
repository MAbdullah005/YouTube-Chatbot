from langchain_community.vectorstores import FAISS

def create_vector_db(chunks, embeddings):
    db = FAISS.from_documents(chunks, embedding=embeddings)
    return db