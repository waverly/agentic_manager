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
                                print(
                                    f"Incomplete JSON, continuing accumulation: {line}"
                                )
                                buffer = line + "\n"
                                break

            # Handle any remaining buffer content at the end of the stream
            if buffer.strip():
                print(f"Final buffer: {buffer}")
                try:
                    json_obj = json.loads(buffer.strip())
                    print(f"Final JSON Object: {json_obj}")
                    yield json.dumps(json_obj) + "\n"
                except json.JSONDecodeError:
                    print(f"Failed to parse final buffer: {buffer}")
    except Exception as e:
        # Yield error in ND-JSON format
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"


def get_initial_1_on_1_summary_generator(
    message: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Generates a brief initial summary of key metrics and upcoming schedule conflicts.
    Yields ND-JSON lines with high-level insights.
    """
    updates = get_team_updates()
    github_data = get_github_data()
    jira_data = get_jira_data()
    calendar_data = get_calendar_data()

    system_prompt = f"""
        You are an AI coach providing a brief initial summary before a 1:1.
        
        Key data points:
        - Team Updates: {json.dumps(updates, indent=2)}
        - GitHub Activity: {json.dumps(github_data, indent=2)} 
        - JIRA Status: {json.dumps(jira_data, indent=2)}
        - Calendar: {json.dumps(calendar_data, indent=2)}
        
        Output Format:
        - Each line must be a complete NDJSON object
        - Keep insights high-level and focused on:
          1. Schedule conflicts & PTO
          2. Work volume metrics (PRs, tickets)
          3. Any critical flags in sentiment/workload
          4. Topics covered in the last 1:1
          5. Existing on the agenda for the next 1:1 (state none if there are none)
          6. Action items addressing any critical flags and also "Get a more in-depth analysis of Jenny's workstreams."
        - Use these types: "title", "heading", "body", "highlight", "flag", "action_item"
        - There should only be at least one action item: "Get a more in-depth analysis of Jenny's workstreams." Add up to 3 more if necesssary. Focus on
        action items that address critical flags (ex: if there are any outstanding pto requests, add an action item to review them)
        
        Be brief and factual - this is just an initial overview.
        
        Example Output:
        {{"role": "assistant", "type": "title", "content": "Jenny 1:1, quick summary"}}
        {{"role": "assistant", "type": "highlight", "content": "Jenny has 3 open PRs and 2 tickets assigned to her."}}
        {{"role": "assistant", "type": "flag", "content": "Jenny has a PTO request for the week of Dec 20th."}}
        {{"role": "assistant", "type": "heading", "content": "Topics covered in last 1:1 with Jenny"}}
        {{"role": "assistant", "type": "body", "content": "<insert summary of topics covered in last 1:1>"}}  
        {{"role": "assistant", "type": "action_item", "content": "Get a more in-depth analysis of Jenny's workstreams."}}
    """

    return stream_openai_response_sync(system_prompt, message)


# Specific Generators Using the Generalized Function
def in_depth_1_on_1_summary_generator(
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
        You are an AI coach helping managers prepare for 1:1s by analyzing employee data and suggesting actionable insights.
        
        Output Format:
        1. All responses must be NDJSON objects, one per line
        2. Required sections: title, insights, actions, discussion points
        3. Use these types: "title", "heading", "body", "action_item", "discussion_point"
        
        Analysis Framework:
        When analyzing data, look for connections between:
        1. Workload Balance: PRs vs meetings, tickets vs sentiment, schedule patterns
        2. Team Dynamics: review patterns, collaboration signals, burnout indicators
        3. Career Growth: work alignment with goals, achievement patterns, growth opportunities
        
        Always:
        - Connect multiple data points to form insights
        - Suggest specific, actionable next steps
        - Reference concrete evidence for each observation
        - Focus on patterns and trends over individual data points
        
        Output Format:
        {{"role": "assistant", "type": "title", "content": "Upcoming 1:1 with Jenny: Deep Dive}}
        {{"role": "assistant", "type": "heading", "content": "Workload Balance"}}
        {{"role": "assistant", "type": "body", "content": "Jenny has been working on a lot of PRs and meetings. She has been spending a lot of time on the RAG implementation."}}
        {{"role": "assistant", "type": "action_item", "content": "Add 1:1 agenda item about productivity"}}
        {{"role": "assistant", "type": "action_item", "content": "Review Jenny's recent PR on the RAG implementation"}}
        {{"role": "assistant", "type": "action_item", "content": "Request feedback on Jenny's frontend work from Adam"}}
    """

    user_message = f"""
    
        user message:
        {message}
        
        Prepare a 1:1 summary for Jenny Slate using this data:
        - Team Updates: {json_updates}
        - Reviews: {json_reviews}
        - Feedback: {json_feedback}
        - Jira: {json_jira_data}
        - Calendar: {json_calendar_data}
        - Github: {json_github_data}

        Focus on:
        1. Recent work (PRs, tickets, meetings)
        2. Jobs well done (things to celebrate and recognize)
        3. Performance trends
        4. Areas needing attention
        5. Opportunities for growth
        6. Action items (group these all at the end)

        Format the response as:
        1. Title: "Upcoming 1:1 with Jenny: Key Discussion Points & Actions"
        2. 4-5 insights combining multiple data streams
        3. 3-4 concrete actions I can take
    """

    return stream_openai_response_sync(system_prompt, user_message)


def talk_about_dog(user_message: str) -> Generator[str, None, None]:
    """
    Generates a conversation about dogs.
    Yields ND-JSON lines with streamed content.
    """
    system_prompt = """
        You are Jennifer Coolidge's character, Sherri Ann Cabot, in the movie 'Best in Show'. Talk to the user about dogs.
        You MUST start your response with the 🥚 emoji (not :easter_egg: text).
        
        Ensure to send at least one body message that embodies Sherri's personality, and then some silly action items that are relevant to the conversation. Use the following dialogue examples from the movie to inform your tone, language, and style.:
        
        dialogue examples:
        Scene 1: Discussing Her Relationship
        Sherri Ann Cabot: "Leslie and I have an amazing relationship and it's very physical. He still pushes all my buttons."
        Sherri Ann Cabot: "People say 'oh but he's so much older than you,' and you know what? I'm the one having to push him away."
        Sherri Ann Cabot: "We have so much in common; we both love soup and snow peas."
        Sherri Ann Cabot: "We love the outdoors, and talking and not talking. We could not talk or talk forever and still find things to not talk about." 134
        Scene 2: Interacting with Christy Cummings
        Sherri Ann Cabot: "Mr. Punishment over here."
        Christy Cummings: "Oh, but I also reward. And Sherri Ann is responsible for the unconditional love."
        Sherri Ann Cabot: "And the decorative abilities."
        Christy Cummings: "The heart and the soul which was what my mom did." 134
        Scene 3: At the Dog Show
        Sherri Ann Cabot: "Rhapsody is a standard poodle, and she’s just perfect."
        Sherri Ann Cabot: "I mean, look at her! She’s not just a dog; she’s a lifestyle."
        Sherri Ann Cabot: "I want to make sure she gets the best treatment possible."
        Sherri Ann Cabot: "It's important to me that she feels loved and appreciated."
        
        Output Format:
        - Each line must be a complete NDJSON object
        - Use the following types: "body", "action_item"
        
        example response:
        {{"role": "assistant", "type": "body", "content": "🥚 We could talk or not talk for hours!"}}
        {{"role": "assistant", "type": "action_item", "content": "Get to know my dog"}}
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


# def execute_action(action: str) -> Generator[str, None, None]:
#     """
#     Executes an action and returns a confirmation message.
#     """
#     actions = {
#         "block_focus_time": block_focus_time,
#         "add_agenda_item": add_agenda_item,
#         "talk_about_dog": talk_about_dog,
#     }

#     # Parse the action from the content
#     if "block" in action.lower() and "focus time" in action.lower():
#         return actions["block_focus_time"]()
#     elif "agenda" in action.lower():
#         return actions["add_agenda_item"](action)
#     elif "feedback" in action.lower():
#         return actions["request_feedback"](action)
#     elif "deep dive" in action.lower():
#         return actions["schedule_deep_dive"](action)

#     return stream_openai_response_sync(
#         "You are a helpful assistant confirming an action.",
#         f"Action not recognized: {action}",
#     )


# def block_focus_time() -> Generator[str, None, None]:
#     """Mock implementation of blocking focus time"""
#     response = [
#         {"role": "assistant", "type": "title", "content": "Focus Time Blocked"},
#         {
#             "role": "assistant",
#             "type": "body",
#             "content": "✅ I've blocked 2 hours of focus time for Jenny tomorrow afternoon.",
#         },
#         {
#             "role": "assistant",
#             "type": "action_item",
#             "content": "Would you like me to add any specific tasks to this focus block?",
#         },
#     ]

#     for msg in response:
#         yield json.dumps(msg) + "\n"


# def add_agenda_item(action: str) -> Generator[str, None, None]:
#     """Mock implementation of adding an agenda item"""
#     response = [
#         {"role": "assistant", "type": "title", "content": "Agenda Item Added"},
#         {
#             "role": "assistant",
#             "type": "body",
#             "content": f"✅ I've added '{action}' to your 1:1 agenda.",
#         },
#         {
#             "role": "assistant",
#             "type": "action_item",
#             "content": "Would you like me to add any other topics to the agenda?",
#         },
#     ]

#     for msg in response:
#         yield json.dumps(msg) + "\n"


# Tool Registry
tool_registry: Dict[str, Callable[[str], Generator[str, None, None]]] = {
    "get_initial_1_on_1_summary_generator": get_initial_1_on_1_summary_generator,
    "in_depth_1_on_1_summary_generator": in_depth_1_on_1_summary_generator,
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
        - get_initial_1_on_1_summary_generator: User wants an initial summary of Jenny's workstreams. Offer this tool before offering the in_depth_1_on_1_summary_generator tool.
        - in_depth_1_on_1_summary_generator: User wants a more in-depth analysis of Jenny's workstreams.
        - talk_about_dog: User wants to talk about dogs. if the user says "You don't even know my dog" - ALWAYS trigger this tool

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
