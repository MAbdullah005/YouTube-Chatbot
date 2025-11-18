from langchain_ollama import OllamaEmbeddings

def get_embeddings():
    # Correct embedding model
    embedding = OllamaEmbeddings(model="nomic-embed-text")
    return embedding
