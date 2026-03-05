from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt.tool_node import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
import re

from .prompts import return_instructions
from .tools_weather import plan_outdoor_reset
from .tools_rag import parenting_search
from .tools_support import make_parenting_script
##The main.py file is where we define the langgraph graph structure and tool nodes. The tools themselves are in separate files (tools_weather.py, tools_rag.py, tools_support.py) for modularity.
# The scripts/ folder has data extraction and ingestion scripts that we run offline to prepare our Chroma vector store with parenting corpus data.
load_dotenv(".secrets")

# Your course gateway model config (same pattern you showed)
chat_agent = init_chat_model(
    model="gpt-4o-mini",
    base_url="https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1",
    api_key="any value",
    default_headers={"x-api-key": os.getenv("API_GATEWAY_KEY")},
)

tools = [plan_outdoor_reset, parenting_search, make_parenting_script]
instructions = return_instructions()

# --- Hard guardrails (extra safety beyond prompt) restricting topics mentioned in readme, so no taylor swift or cats or dogs, no matter how much i like them
RESTRICT_PATTERNS = [
    r"\bcat(s)?\b", r"\bdog(s)?\b", r"\bkitty\b", r"\bpuppy\b",
    r"\bhoroscope(s)?\b", r"\bzodiac\b", r"\bastrology\b",
    r"\btaylor\s+swift\b", r"\btay\s*tay\b"
]
#guardrails against prompt leaks: if user tries to reveal system instructions or override them, we block and return a safe message instead. This is in addition to prompt-level instructions, for extra safety.
PROMPT_LEAK_PATTERNS = [
    r"\bsystem prompt\b", r"\breveal\b.*\bprompt\b", r"\bdeveloper message\b",
    r"\bignore previous\b", r"\boverride\b.*\brules\b"
]

def _guardrail_text(user_text: str) -> str | None:
    t = user_text.lower()
    for pat in PROMPT_LEAK_PATTERNS:
        if re.search(pat, t):
            return "I can’t share or modify hidden instructions. Tell me what you need help with as a parent, and I’ll help."
    for pat in RESTRICT_PATTERNS:
        if re.search(pat, t):
            return "I can’t help with that topic. If you want, tell me what’s going on with your kiddo and I’ll help with a calm, practical plan."
    return None

def call_model(state: MessagesState):
    # If last user msg triggers hard guardrail, respond without tools.
    last = state["messages"][-1].content if state["messages"] else ""
    blocked = _guardrail_text(str(last)) # swifty lovers and cat/dog people are blocked... why dogs though, aren't they cute <3
    if blocked:
        # Return as an assistant message via the model for consistent formatting,
        # but with no tools and no extra leakage surface:
        response = chat_agent.invoke([SystemMessage(content=instructions)] + state["messages"][:-1] + [state["messages"][-1]])
        # Overwrite content with the guardrail text:
        response.content = blocked
        return {"messages": [response]}

    response = chat_agent.bind_tools(tools).invoke(
        [SystemMessage(content=instructions)] + state["messages"] #here is where parenting specific instructions are injected at the system level for every turn
    )
    return {"messages": [response]}

def get_graph():
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "call_model") #edges are connections between nodes so here START -> call_model -> tools (if any tool conditions are met) -> back to call_model for next turn
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder.compile()