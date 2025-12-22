#from langchain.memory import ConversationBufferMemory
from langchain_classic.memory import ConversationBufferMemory

_memory=ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
def get_memory():
  return _memory