from langchain.tools import tool
from pydantic import BaseModel, Field

class ScriptPack(BaseModel):
    validation: str = Field(..., description="Non-judgmental validation for the parent.")
    script_to_child: str = Field(..., description="What the parent can say out loud.")
    if_child_pushes_back: str = Field(..., description="Follow-up script if child resists.")
    parent_next_step: str = Field(..., description="One small next action for the parent.")

@tool
def make_parenting_script(situation: str, child_age: str = "") -> ScriptPack:
    """
    Generates short, practical scripts for a parenting situation.
    This is a structured tool output that the model can format nicely.
    """
    age_line = f" (child age: {child_age})" if child_age else ""
    # Keep it simple + reusable. The LLM will still present it in a warm way.
    return ScriptPack(
        validation=f"That sounds like a lot{age_line}. You’re not failing — you’re in a hard moment.",
        script_to_child="“I won’t let you hurt me. You can be mad. I’m right here.”",
        if_child_pushes_back="“You really don’t like this boundary. I get it. The boundary is still here.”",
        parent_next_step="Take one slow breath, lower your voice, and repeat the same short line once."
    )