import os

def create(path):
    os.makedirs(path, exist_ok=True)

def touch(path):
    with open(path, "w") as f:
        pass


create("youtube-rag-chatbot/backend/core")
create("youtube-rag-chatbot/backend/utils")
create("youtube-rag-chatbot/frontend")


touch("youtube-rag-chatbot/backend/main.py")
touch("youtube-rag-chatbot/backend/config.py")
touch("youtube-rag-chatbot/backend/requirements.txt")
touch("youtube-rag-chatbot/backend/.env.example")


touch("youtube-rag-chatbot/backend/core/__init__.py")
touch("youtube-rag-chatbot/backend/core/loader.py")
touch("youtube-rag-chatbot/backend/core/splitter.py")
touch("youtube-rag-chatbot/backend/core/embeddings.py")
touch("youtube-rag-chatbot/backend/core/vectorstore.py")
touch("youtube-rag-chatbot/backend/core/rag_chain.py")



touch("youtube-rag-chatbot/backend/utils/__init__.py")
touch("youtube-rag-chatbot/backend/utils/helper.py")



touch("youtube-rag-chatbot/frontend/app.py")



touch("youtube-rag-chatbot/.gitignore")
touch("youtube-rag-chatbot/README.md")
touch("youtube-rag-chatbot/LICENSE")

print("✔ Project structure created successfully!")
