"""
Agent API routes for the AI-CRM HCP Module.

Provides endpoints for the conversational AI agent, raw-notes
processing, and listing available agent tools.
"""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage

from config import settings
from schemas import ChatMessage, ProcessNotesRequest, AgentResponse, ToolInfo
from agent.graph import run_agent
from agent.tools import ALL_TOOLS
from database import get_db_session
from models import HCP, Product

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/chat", response_model=AgentResponse)
def agent_chat(payload: ChatMessage):
    """
    Send a natural-language message to the AI agent.

    The agent will interpret the user's intent, optionally invoke
    tools (log interaction, search, suggest actions, etc.), and
    return a conversational response.

    Args:
        payload: ChatMessage with the user's message and optional HCP context.

    Returns:
        AgentResponse with the agent's reply, any tool calls made,
        structured data, and potential errors.

    Raises:
        HTTPException 500: If the agent encounters an unrecoverable error.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured. Please set it in your .env file.",
        )

    try:
        result = run_agent(
            message=payload.message,
            hcp_id=payload.hcp_id,
        )

        return AgentResponse(
            response=result.get("response", "No response generated."),
            tool_calls=result.get("tool_calls", []),
            data=result.get("data"),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent processing failed: {str(e)}",
        )


@router.post("/process-notes", response_model=AgentResponse)
def process_notes(payload: ProcessNotesRequest):
    """
    Process raw interaction notes through the AI agent.

    Takes unstructured notes from a sales representative and uses
    the agent to extract structured information: key topics,
    products discussed, sentiment, and a clean summary.

    If an hcp_id is provided, the notes are automatically logged
    as a new interaction via the agent.

    Args:
        payload: ProcessNotesRequest with raw notes and optional context.

    Returns:
        AgentResponse with the processed summary and extracted data.

    Raises:
        HTTPException 500: If processing fails.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not configured. Please set it in your .env file.",
        )

    try:
        # Build a targeted prompt for the agent
        prompt_parts = ["Please process the following raw interaction notes and extract key information."]

        if payload.hcp_id:
            # Look up the HCP name for better context
            db = get_db_session()
            try:
                hcp = db.query(HCP).filter(HCP.id == payload.hcp_id).first()
                if hcp:
                    prompt_parts.append(f"These notes are about an interaction with {hcp.name} (HCP ID: {payload.hcp_id}).")
                else:
                    prompt_parts.append(f"These notes are about an interaction with HCP ID: {payload.hcp_id}.")
            finally:
                db.close()

            if payload.interaction_type:
                prompt_parts.append(f"The interaction type was: {payload.interaction_type}.")

            prompt_parts.append(
                f"Please log this interaction using the log_interaction tool. "
                f"Raw notes: {payload.raw_notes}"
            )
        else:
            prompt_parts.append(
                f"Extract the key topics, products discussed, sentiment, and provide a clean summary. "
                f"Do NOT log this interaction — just analyse the notes.\n\n"
                f"Raw notes: {payload.raw_notes}"
            )

        message = " ".join(prompt_parts)

        result = run_agent(
            message=message,
            hcp_id=payload.hcp_id,
        )

        return AgentResponse(
            response=result.get("response", "Notes processed."),
            tool_calls=result.get("tool_calls", []),
            data=result.get("data"),
            error=result.get("error"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Notes processing failed: {str(e)}",
        )


@router.get("/tools", response_model=list[ToolInfo])
def list_tools():
    """
    List all available agent tools and their descriptions.

    Returns a catalogue of tools that the AI agent can invoke,
    useful for documentation and UI rendering.

    Returns:
        List of ToolInfo objects with name and description.
    """
    tools_info = []
    for tool in ALL_TOOLS:
        tools_info.append(
            ToolInfo(
                name=tool.name,
                description=tool.description,
            )
        )
    return tools_info
