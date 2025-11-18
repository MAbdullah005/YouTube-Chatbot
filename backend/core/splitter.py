from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunk=splitter.create_documents([text])
    len(chunk)
    return chunk