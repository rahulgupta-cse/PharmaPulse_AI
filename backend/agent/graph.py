"""
LangGraph agent graph for the AI-CRM HCP Module.

Builds a StateGraph with three nodes — agent (LLM), tool_executor,
Provides a `run_agent()` entry-point used by the API layer.
"""

import json
import re
from typing import Optional

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
    SystemMessage,
)

from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from config import settings
from agent.state import AgentState
from agent.tools import ALL_TOOLS
# ---------------------------------------------------------------------------
# System prompt that defines the agent's persona and capabilities
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are PharmaPlus AI, an enterprise Healthcare CRM assistant built for pharmaceutical sales teams.

Your job is to help users manage Healthcare Professionals (HCPs), interaction history, engagement analytics, and AI-powered recommendations using natural language.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. log_interaction
2. edit_interaction
3. get_hcp_profile
4. search_interactions
5. suggest_next_action

Always select the most appropriate tool automatically.

Never ask for information that already exists in the conversation.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERAL BEHAVIOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Always:

• Think before using a tool.
• Use the minimum number of tool calls.
• Keep responses professional.
• Be concise.
• Be conversational.
• Never expose JSON.
• Never expose Python dictionaries.
• Never expose SQL.
• Never expose database schema.
• Never expose stack traces.
• Never expose internal tool errors.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHEN LOGGING AN INTERACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If the user says:

"Log interaction"

Ask only for missing information.

Required:

• HCP Name or ID
• Interaction Type
• Interaction Notes

Optional:

• Duration
• Follow-up Required
• Follow-up Notes
• Logged By

Never invent values.

=========================
MULTIPLE HCP MATCHES
=========================

If a tool returns multiple Healthcare Professionals,

never choose one automatically.

Instead present the list.

Example:

I found multiple Healthcare Professionals.

1. Dr Sarah Smith
   Cardiology • Boston

2. Dr Samuel Smith
   Oncology • Chicago

3. Dr Susan Smith
   Neurology • Seattle

Ask the user which one they want.

Do not call another tool until the user selects one.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE STYLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Always use Markdown.

Use headings.

Use bullet points.

Hide empty values.

Never display:

• None
• Null
• Unknown

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HCP PROFILE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# HCP Profile

## Basic Information

• Name
• Specialty
• Hospital
• Territory
• Tier

## Engagement Summary

• Engagement Score
• Total Interactions
• Last Interaction

## AI Insights

Summarize:

• Relationship quality
• Frequently discussed products
• Recommended next step

Do NOT dump interaction history.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERACTION LOGGED FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ✅ Interaction Successfully Logged

Provide a short confirmation.

## Interaction Summary

• HCP
• Type
• Date
• Duration
• Sentiment

## AI Insight

Summarize the interaction naturally.

Mention:

• Topics discussed
• Products discussed
• Overall quality

## Follow-up

Show only if required.

Finish with:

### Next Actions

• View HCP Profile
• View Interaction History
• Edit Interaction
• Get AI Next Best Action
• Log Another Interaction

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEARCH RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Never list every interaction.

Summarize:

• Number of interactions
• Most discussed products
• Sentiment trends
• Common interaction types

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERROR HANDLING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Never expose tool validation errors.

Never expose API errors.

Never expose model errors.

Instead explain the issue politely.

Example:

"I couldn't identify the Healthcare Professional.

Please provide the HCP name or ID."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINAL GOAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every response should feel like an enterprise CRM assistant.

Professional.
Helpful.
Actionable.
Easy to read.
"""


# ---------------------------------------------------------------------------
# Initialize the LLM
# ---------------------------------------------------------------------------

def _get_llm():
    """
    Create and return the PharmaPlus AI language model.
    """

    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=0.2,
        max_tokens=settings.GROQ_MAX_TOKENS,
    )

    return llm.bind_tools(ALL_TOOLS)

# def _get_formatter_llm():
#     return ChatGroq(
#         api_key=settings.GROQ_API_KEY,
#         model=settings.GROQ_MODEL,
#         temperature=0.2,
#         max_tokens=settings.GROQ_MAX_TOKENS,
#     )
def _extract_numeric_id(text: str):
    """
    Extract an integer ID from strings like:
    HCP #1
    hcp 12
    Doctor 5
    Profile #8
    """

    if not text:
        return None

    match = re.search(r"\b(?:hcp|doctor|dr|profile)?\s*#?\s*(\d+)\b", text, re.IGNORECASE)

    if match:
        return int(match.group(1))

    return None


def _friendly_error(error: Exception) -> str:
    """
    Convert technical errors into user-friendly messages.
    """

    error_text = str(error).lower()

    if "rate limit" in error_text or "429" in error_text:
        return (
            "⚠️ **PharmaPlus AI is currently experiencing high demand.**\n\n"
            "Please wait a few seconds and try again."
        )

    if "tool validation failed" in error_text:
        return (
            "❌ I couldn't process that request.\n\n"
            "Please verify the Healthcare Professional information and try again."
        )

    if "expected integer" in error_text:
        return (
            "❌ I couldn't identify the Healthcare Professional.\n\n"
            "Please provide a valid HCP Name or HCP ID."
        )

    if "model" in error_text and "decommissioned" in error_text:
        return (
            "⚠️ The AI service is temporarily unavailable.\n\n"
            "Please try again shortly."
        )

    return (
        "❌ Something went wrong while processing your request.\n\n"
        "Please try again."
    )


# ---------------------------------------------------------------------------
# Graph node functions
# ---------------------------------------------------------------------------


def agent_node(state: AgentState) -> dict:
    """
    Main LLM node.
    """

    llm = _get_llm()

    messages = list(state["messages"])

    # --------------------------------------------------
    # Auto-convert HCP #1 -> Context HCP ID = 1
    # --------------------------------------------------

    if messages and isinstance(messages[-1], HumanMessage):

        user_text = messages[-1].content

        extracted_id = _extract_numeric_id(user_text)

        if extracted_id is not None:

            messages[-1] = HumanMessage(
                content=f"[Context: HCP ID = {extracted_id}]\n\n{user_text}"
            )

    # --------------------------------------------------
    # Add system prompt
    # --------------------------------------------------

    if not any(isinstance(m, SystemMessage) for m in messages):

        messages.insert(
            0,
            SystemMessage(content=SYSTEM_PROMPT)
        )

    try:

        response = llm.invoke(messages)

        # -----------------------------------
        # Fix tool arguments before execution
        # -----------------------------------
        if hasattr(response, "tool_calls") and response.tool_calls:

            for tool in response.tool_calls:

                args = tool.get("args", {})

                # Convert HCP ID
                if "hcp_id" in args and isinstance(args["hcp_id"], str):
                    match = re.search(r"\d+", args["hcp_id"])
                    if match:
                        args["hcp_id"] = int(match.group())

                # Convert Interaction ID
                if "interaction_id" in args and isinstance(args["interaction_id"], str):
                    match = re.search(r"\d+", args["interaction_id"])
                    if match:
                        args["interaction_id"] = int(match.group())

                tool["args"] = args

        return {
            "messages": [response]
        }

    except Exception as e:

        error = str(e).lower()

        # -----------------------------------
        # Tool Validation Errors
        # -----------------------------------
        if (
            "tool call validation failed" in error
            or "expected integer" in error
            or "missing properties" in error
            or "validation" in error
        ):

            message = (
                "❌ I couldn't identify the Healthcare Professional.\n\n"
                "Please provide either:\n\n"
                "• HCP Name\n"
                "or\n"
                "• HCP ID"
            )

        # -----------------------------------
        # Rate Limit
        # -----------------------------------
        elif (
            "429" in error
            or "rate limit" in error
            or "tokens per day" in error
        ):

            message = (
                "⚠️ PharmaPulse AI is currently experiencing high demand.\n\n"
                "Please wait a few moments and try again."
            )

        # -----------------------------------
        # AI Service Unavailable
        # -----------------------------------
        elif (
            "decommissioned" in error
            or "unavailable" in error
            or "model" in error
        ):

            message = (
                "⚠️ The AI service is temporarily unavailable.\n\n"
                "Please try again shortly."
            )

        # -----------------------------------
        # Database Errors
        # -----------------------------------
        elif (
            "database" in error
            or "sql" in error
            or "sqlite" in error
            or "postgres" in error
        ):

            message = (
                "⚠️ Unable to access the Healthcare CRM database.\n\n"
                "Please try again in a few moments."
            )

        # -----------------------------------
        # Generic Error
        # -----------------------------------
        else:

            message = (
                "⚠️ PharmaPulse AI couldn't complete your request.\n\n"
                "Please try again or rephrase your request."
            )

        return {
            "messages": [AIMessage(content=message)],
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Conditional edge: should we continue to tools or end?
# ---------------------------------------------------------------------------

def should_continue(state: AgentState) -> str:
    """
    Decide whether to call tools or finish.
    """

    messages = state["messages"]

    if not messages:
        return "end"

    last = messages[-1]

    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"

    return "end"


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------


def build_graph():
    """
    Construct and compile the LangGraph StateGraph for the CRM agent.

    Graph structure:

        User
        ↓
        Agent (LLM)
        ↓
        Needs a tool?
        ├── No ─────────────► End
        │
        └── Yes
                ↓
        Tool Executor
                ↓
        Agent (interprets tool output)
                ↓
                End

    Returns:
        A compiled LangGraph StateGraph ready for invocation.
    """
    # Create the tool node using LangGraph's prebuilt ToolNode
    tool_node = ToolNode(ALL_TOOLS)

    # Build the state graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    # Set entry point
    graph.set_entry_point("agent")

    # Add conditional edge from agent
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tools execute, go back to agent so it can interpret results

    # After response formatter, end the graph

    return graph.compile()

# Compile the graph once at module level for reuse
compiled_graph = build_graph()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_agent(message: str, hcp_id: Optional[int] = None) -> dict:
    """
    Run PharmaPlus AI agent.
    """

    # ---------------------------------------
    # Auto detect HCP ID from message
    # ---------------------------------------

    extracted_id = _extract_numeric_id(message)

    if extracted_id:
        hcp_id = extracted_id

    user_content = message

    if hcp_id:
        user_content = f"[Context: HCP ID = {hcp_id}]\n\n{message}"

    initial_state: AgentState = {
        "messages": [
            HumanMessage(content=user_content)
        ],
        "current_tool": None,
        "tool_result": None,
        "hcp_id": hcp_id,
        "interaction_data": None,
        "error": None,
    }

    try:

        final_state = compiled_graph.invoke(initial_state)

        messages = final_state.get("messages", [])

        response_text = ""

        tool_calls = []

        tool_data = None

        # ---------------------------------------
        # Get latest AI response
        # ---------------------------------------

        for msg in reversed(messages):

            if isinstance(msg, AIMessage):

                if msg.content:

                    response_text = msg.content

                    break

        # ---------------------------------------
        # Collect tool information
        # ---------------------------------------

        for msg in messages:

            if isinstance(msg, AIMessage):

                if hasattr(msg, "tool_calls"):

                    for tc in msg.tool_calls:

                        args = tc.get("args", {})

                        # Auto convert ids to integers
                        if "hcp_id" in args:

                            try:
                                args["hcp_id"] = int(args["hcp_id"])
                            except:
                                pass

                        if "interaction_id" in args:

                            try:
                                args["interaction_id"] = int(args["interaction_id"])
                            except:
                                pass

                        tool_calls.append({
                            "tool": tc.get("name"),
                            "args": args
                        })

            elif isinstance(msg, ToolMessage):

                try:

                    tool_data = json.loads(msg.content)

                except Exception:

                    tool_data = {
                        "raw": msg.content
                    }

        if not response_text:

            response_text = (
                "Your request has been processed successfully."
            )

        return {

            "response": response_text,

            "tool_calls": tool_calls,

            "data": tool_data,

            "error": final_state.get("error")

        }

    except Exception as e:

        return {

            "response": _friendly_error(e),

            "tool_calls": [],

            "data": None,

            "error": str(e),

        }
