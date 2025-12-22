#from langchain.memory import ConversationBufferMemory
from langchain_classic.memory import ConversationBufferMemory,ConversationBufferWindowMemory

_memory=ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=5,
    )
def get_memory():
  return _memory