"""
LangGraph state definition for the AI-CRM HCP Agent.

Defines the typed state dictionary that flows through the
LangGraph state machine, carrying messages, tool results,
and contextual information between nodes.
"""

from typing import Optional, Annotated
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State schema for the LangGraph agent.

    This TypedDict defines every field that the agent graph can
    read from or write to as it processes a user request.

    Attributes:
        messages: Conversation history managed by LangGraph's
                  add_messages reducer (appends new messages).
        current_tool: Name of the tool currently being invoked, if any.
        tool_result: The result returned by the most recent tool call.
        hcp_id: Optional HCP identifier providing context to the agent.
        interaction_data: Arbitrary dict carrying interaction-related
                         data between nodes.
        error: Error message string if something goes wrong during
               processing.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    current_tool: Optional[str]
    tool_result: Optional[str]
    hcp_id: Optional[int]
    interaction_data: Optional[dict]
    error: Optional[str]
