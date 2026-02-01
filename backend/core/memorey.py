from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_classic.memory import ConversationBufferWindowMemory

# Store memory per session
_memory_store = {}

def get_memory(session_id: str = "default"):
    if session_id not in _memory_store:
        _memory_store[session_id] = ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=False,
            k=3,
            chat_memory=ChatMessageHistory()
        )
    return _memory_store[session_id]
