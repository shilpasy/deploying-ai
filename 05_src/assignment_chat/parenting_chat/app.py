import gradio as gr
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

from .main import get_graph
#app.py is where we glue together the interface (via gradio) and logic and memory (via langgraph) and print the results
#load_dotenv(".secrets")
from pathlib import Path
from dotenv import load_dotenv

ROOT_05_SRC = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_05_SRC / ".secrets")

# we use a LangGraph graph instead of direct llm.invoke(...) : just writing the alternatives if no LangGraph graph was used #flowchart of reasoning via langgraph
graph = get_graph()

def parenting_chat(message: str, history: list[dict]) -> str:
    langchain_messages = [] # retrival, tool, memory
    for msg in history:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))
    langchain_messages.append(HumanMessage(content=message))

    # llm.invoke(...) instead of graph.invoke(...) if no LangGraph graph was used #response = llm.invoke(langchain_messages) # however with langgraph we can have a more complex flow with retrieval, and memory like here parents can check weather to determine if they can plan an outing
    state = {"messages": langchain_messages}
    result = graph.invoke(state)

    # LangGraph returns updated state with messages
    return result["messages"][-1].content

gr.ChatInterface(
    fn=parenting_chat,
    type="messages"
).launch(share=True)