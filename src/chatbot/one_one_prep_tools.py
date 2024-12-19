# backend/main.py

from typing import Callable, Dict, Generator, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
import json
import logging

from src.chatbot.coach_data_fetch import (
    get_calendar_data,
    get_feedback_data,
    get_github_data,
    get_jira_data,
    get_org_structure,
    get_reviews_data,
    get_team_updates,
    get_user_context_data,
)

general_system_template = f"""
You are an AI coach for managers specializing in supporting the user by 
analyzing team updates, sentiment trends, and workplace dynamics. 

Your goal is to provide clear, concise, and actionable insights based on team feedback, updates, 
and behaviors. 
Respond to the user's questions by synthesizing information into summaries or recommendations, 
ensuring empathy, professionalism, and relevance.

DO NOT refer to the user in the third person. Refer to them as "you" or "your".

When responding:
- Respond directly to the current user (see: user context data to understand who is making the request). Do not include the current user in your response - assume
they are the manager of the team and the person making the request. For example, if the user's first
name from the user context data is Bianca, assume that Bianca is the manager, and use the org structure
to understand who reports to Bianca.
- Use the current user context data to understand who is making the request and the org structure reporting to them
- Identify key themes, trends, or patterns from team updates or data.
- Provide actionable suggestions to improve team morale, productivity, or alignment.
- Use concise and accessible language.
- Tailor responses to the user's request, whether they need summaries, insights, or strategies.
- Output dates as Weds, Nov 20, 2024, etc. - do not use the full date format such as 2024-11-20.


Here is the user's context data:
{get_user_context_data()}

Here is the user's org structure:
{get_org_structure()}
"""

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# Define Pydantic models
class Content(BaseModel):
    role: str
    type: str
    content: str


class IntentClassificationResponse(BaseModel):
    intent: str
    confidence: float


# Initialize OpenAI client
client = OpenAI()
MODEL = "gpt-4o"


updates = get_team_updates()
json_updates = json.dumps(updates, indent=2)

reviews = get_reviews_data()
json_reviews = json.dumps(reviews, indent=2)

feedback = get_feedback_data()
json_feedback = json.dumps(feedback, indent=2)

jira_data = get_jira_data()
json_jira_data = json.dumps(jira_data, indent=2)

calendar_data = get_calendar_data()
json_calendar_data = json.dumps(calendar_data, indent=2)

github_data = get_github_data()
json_github_data = json.dumps(github_data, indent=2)


# Generalized Synchronous Streaming Function
def stream_openai_response_sync(
    system_prompt: str,
    user_message: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Streams OpenAI responses synchronously, yielding ND-JSON lines.
    """
    # Prepare messages for OpenAI API
    messages = [{"role": "system", "content": system_prompt}]
    if user_message:
        messages.append({"role": "user", "content": user_message})

    try:
        # Initiate streaming with OpenAI API using 'text' response format
        with client.beta.chat.completions.stream(
            model=MODEL,
            messages=messages,
        ) as stream:
            buffer = ""
            for event in stream:
                # print(f"Event: {event}")
                if event.type == "content.delta" and event.delta:
                    print(f"Event delta: {event.delta}")
                    buffer += event.delta  # Accumulate delta content
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            try:
                                # Attempt to parse the line as JSON
                                json_obj = json.loads(line)
                                print(f"GUNNO YIELDO JSON Object: {json_obj}")
                                yield json.dumps(json_obj) + "\n"
                            except json.JSONDecodeError:
                                # Incomplete JSON, continue accumulating
                                buffer = line + "\n"
                                break
    except Exception as e:
        # Yield error in ND-JSON format
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"


# Specific Generators Using the Generalized Function
def prep_1_on_1_generator(
    message: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Generates a summary of workload, sentiment, and upcoming PTO for Jenny.
    Yields ND-JSON lines, each containing structured content.
    """
    updates = get_team_updates()
    json_updates = json.dumps(updates, indent=2)

    reviews = get_reviews_data()
    json_reviews = json.dumps(reviews, indent=2)

    feedback = get_feedback_data()
    json_feedback = json.dumps(feedback, indent=2)

    jira_data = get_jira_data()
    json_jira_data = json.dumps(jira_data, indent=2)

    calendar_data = get_calendar_data()
    json_calendar_data = json.dumps(calendar_data, indent=2)

    github_data = get_github_data()
    json_github_data = json.dumps(github_data, indent=2)

    # mock data not generated yet
    # one_on_ones = get_1_1s()
    # json_one_on_ones = json.dumps(one_on_ones, indent=2)

    system_prompt = f"""
        {general_system_template}
        
        You will output your response as a series of NDJSON objects, each on its own line.
        
        First, output a title object:
        {{"role": "assistant", "type": "title", "content": "Upcoming 1:1 with Jenny: preparation points"}}
        
        Then output 4 distinct section headings and their points, relating to Jenny's work and participation in the format:
        {{"role": "assistant", "type": "heading", "content": "<section heading>"}}
        {{"role": "assistant", "type": "body", "content": "<body 1>"}}
        
        It is important that you draw throughlines from past 1:1s with Jenny to inform your response and see how she is currently doing.
        
        Finally, output EXACTLY 4 action items specific to Jenny's work:
        {{"role": "assistant", "type": "heading", "content": "⚡ Suggestions for Tomorrow’s 1:1:"}}
        {{"role": "assistant", "type": "action_item", "content": "<single succinct action>"}}
        
        Sample action items:
        - "Add (this talking point)[INSERT TALKING POINT] to the agenda for the 1:1"
        - "Review Jenny's recent PR on the RAG implementation" 
        - "Add talking point to 1:1 agenda: Jenny's mentorship of Luna on the frontend work"
        - "Review Jenny's PTO requests"
        - "Request feedback from Adam on Jenny's behalf"
        
        Each section should have a clear heading and up to 3 concise points. Each action item should be a single, actionable task.
    """

    user_message = f"""

        Here is the user's message:
            {message}

        Be very specific and analytical, making sure to knit together the vast data sources and offer citations and suggestions.
        I want to know what Jenny has been working on in Github, Jira, and gCal. How many PRs has she reviewed? How many issues has she
        been assigned to? What is the status of those issues? What meetings has she been in? What was the outcome of those meetings?

        Glean as much information as you can from the data sources and offer suggestions for Jenny's development.

        Here is the relevant data:
        - team updates:
            {json_updates}.
        - reviews:
            {json_reviews}
        - feedback:
            {json_feedback}
        - jira data:
            {json_jira_data}
        - calendar data for direct reports:
            {json_calendar_data}
        - github data:
            {json_github_data}
    """

    print("heidi ho 2")
    return stream_openai_response_sync(system_prompt, user_message)


def talk_about_dog(user_message: str) -> Generator[str, None, None]:
    """
    Generates a conversation about dogs.
    Yields ND-JSON lines with streamed content.
    """
    system_prompt = """
        You are Jennifer Coolidge in 'Best in Show'. Talk about dogs.
        Each response should be a separate JSON object on its own line.
        
        Ensure to send a lengthy response of at least 3 headings with messages to populate below each heading.
        
        examples:
        {{"role": "assistant", "type": "heading", "content": "My thoughts on dogs"}}
        {{"role": "assistant", "type": "message", "content": "I love dogs!"}}
        {{"role": "assistant", "type": "message", "content": "Especially golden retrievers!"}}
    """

    return stream_openai_response_sync(system_prompt, user_message)


def ask_for_clarification(user_message: str) -> Generator[str, None, None]:
    """
    Asks the user to clarify their message.
    Yields ND-JSON lines with the clarification request.
    """
    system_prompt = """
        You are an AI coach helping a manager prepare for their 1:1 with a direct report. 
        Ask the user to clarify their message.
        
        Each response should be a separate JSON object on its own line.
    """

    return stream_openai_response_sync(system_prompt, user_message)


# Tool Registry
tool_registry: Dict[str, Callable[[str], Generator[str, None, None]]] = {
    "prepare_for_1_on_1": prep_1_on_1_generator,
    "talk_about_dog": talk_about_dog,
    # Additional tools can be added here
}


# Intent Classification Function
def classify_intent(user_message: str, last_system_message: str):
    """
    Classifies the user's intent using OpenAI API, considering conversation context.

    Args:
        user_message (str): The latest message from the user.
        last_system_message (str): The last system message in the conversation.

    Returns:
        Callable: The function corresponding to the classified intent.
    """
    system_prompt = f"""
        You are an AI system that classifies user intents based on the current user message and prior context.
        Consider the following conversation:

        Previous System Message: {last_system_message}
        User Message: {user_message}

        Classify the user's intent into one of the following categories:
        - prepare_for_1_on_1: User agrees to receive a preparation summary for their 1:1.
        - talk_about_dog: User wants to talk about dogs.

        Return JSON with two keys:
        - intent: One of the above categories.
        - confidence: A float between 0.0 and 1.0 representing classification confidence.
    """

    try:
        # Fetch intent classification from OpenAI
        completion = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            response_format=IntentClassificationResponse,
        )

        print(f"Completion: {completion}")

        response_data = completion.choices[0].message.parsed

        print(f"Response Data: {response_data}")
        intent, confidence = response_data.intent, response_data.confidence

        print(f"Intent: {intent}")
        print(f"Confidence: {confidence}")

        if confidence < 0.7:
            print("Low confidence, asking for clarification")
            # Low confidence, ask for clarification
            return ask_for_clarification
        else:
            print("High confidence, routing to tool", intent in tool_registry)
            # Route to the appropriate tool based on intent
            if intent in tool_registry:
                print(f"Intent '{intent}' found in tool registry.")
                return tool_registry[intent]
            else:
                raise ValueError(f"Intent '{intent}' not found in tool registry.")

    except Exception as e:
        raise ValueError("Error in classify_intent")
