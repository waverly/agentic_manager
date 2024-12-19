from fastapi import FastAPI, HTTPException, Query, Depends
import asyncio
from typing import Optional, List
from . import config
from fastapi.responses import JSONResponse, StreamingResponse
import json
import os
import sqlite3
import logging
from fastapi.middleware.cors import CORSMiddleware

# from .chatbot.coach_tools import (
#     get_first_message,
#     get_team_updates,
#     intent_classification,
#     synthesize_updates,
# )
from pydantic import BaseModel
import openai

from .chatbot.one_one_prep_tools import classify_intent

app = FastAPI(
    title="Lattice Manager Agent API",
    description="""
    API for accessing llm agent data.
    
    ## Usage
    All endpoints return JSON responses and support query parameters for filtering.
    """,
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging for api.py
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root Endpoint
@app.get("/", tags=["General"])
async def root():
    """
    Welcome endpoint with basic API information.
    """
    return {
        "message": "Welcome to the Lattice Manager Agent API. Visit /docs for documentation."
    }


# First Message Stream Endpoint
@app.get("/first_message_stream", tags=["FirstMessage"])
async def first_message_stream():
    """
    Stream the first structured message for the 1:1 preparation demo.
    """

    async def message_generator():
        # Initial message to stream
        initial_message = "Hi there! 👋 I noticed you have a 1:1 with Jenny tomorrow at 10 AM. Want me to prep you with a quick summary of her recent updates, workload, and anything else worth discussing?"
        words = initial_message.split()  # Split message into words

        for word in words:
            # Stream each word as JSON
            yield json.dumps(
                {"role": "assistant", "type": "body", "content": word}
            ) + "\n"
            await asyncio.sleep(0.1)  # Add a delay to simulate typing

    response = StreamingResponse(message_generator(), media_type="application/x-ndjson")
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


class ChatRequest(BaseModel):
    message: str
    last_system_message: str


# Chat Endpoint
@app.post("/chat", tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Handle chat messages and stream responses incrementally.
    """
    try:
        # Get the appropriate tool from the registry based on intent
        tool = classify_intent(request.message, request.last_system_message)

        print(f"Tool: {tool}")

        # If the tool is callable, call it and stream the results
        if callable(tool):
            return StreamingResponse(
                content=tool(request.message), media_type="application/x-ndjson"
            )
        else:
            raise ValueError("Tool must be callable and return an iterable")
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
