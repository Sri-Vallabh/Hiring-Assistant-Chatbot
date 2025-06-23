from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
groq_api_key = os.getenv('GROQ_API_KEY')

# Initialize the ChatOpenAI model
chat = ChatOpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1",
    model="llama3-8b-8192"
)

# Prepare a simple test prompt
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Say hello in Assamese.")
]

# Invoke the model and print the output
response = chat.invoke(messages)
print("Groq LLM Response:", response.content)
