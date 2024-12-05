import json
from typing import Callable, Literal
from openai import OpenAI

client = OpenAI()
MODEL = "gpt-4o"

from .coach_data_fetch import (
    get_team_updates,
    get_user_context_data,
    get_reviews_data,
    get_feedback_data,
)
from .structured_output_classes import (
    Content,
    UpdatesSynthesisContent,
    AdjustWorkloadContent,
    IntentClassificationResponse,
)


general_system_template = f"""
You are an AI coach for managers specializing in supporting the user by 
analyzing team updates, sentiment trends, and workplace dynamics. 
Your goal is to provide clear, concise, and actionable insights based on team feedback, updates, 
and behaviors. 
Respond to user questions by synthesizing information into summaries or recommendations, 
ensuring empathy, professionalism, and relevance.

When responding:
- Respond directly to the current user. Do not include the current user in your response - assume
they are the manager of the team and the person making the request.
- Use the current user context data to understand who is making the request and the org structure reporting to them
- Identify key themes, trends, or patterns from team updates or data.
- Provide actionable suggestions to improve team morale, productivity, or alignment.
- Use concise and accessible language.
- Tailor responses to the user's request, whether they need summaries, insights, or strategies.


Here is the user's context data:
{get_user_context_data()}
"""


# TOOLS
# MAKE SURE TO ADD EACH TOOL TO THE TOOL REGISTRY


def synthesize_updates(message: str) -> dict:

    updates = get_team_updates()
    json_updates = json.dumps(updates, indent=2)

    section_format_instructions = """
    When summarizing the team updates, make sure to have a numbered list of points, where each point has a heading
    that summarizes the point. For example, if the user asks "Summarize my team’s recent updates so I can understand why their sentiment is trending down", 
    the response should have a point with a header that says "1. Increasing Meeting Overload:"  
    and the point's content should say: "Both Jenny and Luna have consistently mentioned spending over 15 
    hours in meetings weekly, leaving little time for deep work. 
    Their updates express frustration over a lack of progress on their key 
    deliverables due to the constant context-switching."
    
    When analyzing team updates:
    1. Number each section heading (except Insights and Suggestions)
    2. Include citation numbers for each point
    3. Structure insights as cards with title, description, and actions
    4. Ensure all points include their source citations
    """

    insight_format_instructions = """
    When structuring insights:
    1. Structure insights as cards with title, description, and actions
    """

    system_template = f"""
        {general_system_template}
        
        Please follow these instructions for sections:
        {section_format_instructions}
        
        Please follow these instructions for insights:
        {insight_format_instructions}

    """

    user_message = f"""Here are the team updates: 
            {json_updates}. 
          Here is the user's message: 
            {message}
        Focus on:
        - Meeting loads and time management
        - Team morale and workload distribution
        - Psychological safety and team dynamics
        """

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_template,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        response_format=UpdatesSynthesisContent,
    )

    try:
        response = completion.choices[0].message.parsed
        print("get_team_updates response is ", response)
        return response
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from OpenAI")


def synthesize_adjust_workload(message: str) -> dict:
    """Use this to adjust the workloads of the team to be more efficient and balanced."""
    updates = get_team_updates()
    json_updates = json.dumps(updates, indent=2)

    reviews = get_reviews_data()
    json_reviews = json.dumps(reviews, indent=2)

    feedback = get_feedback_data()
    json_feedback = json.dumps(feedback, indent=2)

    section_format_instructions = """
    When summarizing the workload adjustments, each heading should be the name of one of the user's reports.
    """

    expected_outcome_format_instructions = """
    The expected outcome section should have a single heading that says "Expected Outcome" and a list of points
    that describe the expected outcome if all suggestions are implemented.
    """

    system_template = f"""
        {general_system_template}
        
        There should be a section for each report, 
        and a section for the expected outcome if all suggestions are implemented.
        
        Please follow these instructions for sections:
        {section_format_instructions}
        
        Please follow these instructions for the expected outcome:
        {expected_outcome_format_instructions}
    """

    user_message = f"""
    
    Here is the user's message: 
        {message}
    
    Here is the relevant data:
        - team updates: 
            {json_updates}. 
        - reviews:
            {json_reviews}
        - feedback:
            {json_feedback}
            

        Focus on:
        - Meeting loads and time management
        - Team morale and workload distribution
        - Psychological safety and team dynamics
    """

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_template,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        response_format=AdjustWorkloadContent,
    )

    try:
        response = completion.choices[0].message.parsed

        print("get_team_updates response is ", response)
        return response
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from OpenAI")


def ask_for_clarification(message: str) -> dict:
    return {
        "role": "assistant",
        "type": "SimpleMessage",
        "simpleMessage": f"I'm not quite sure what you're asking when you say {message}. Could you please clarify if you want to understand team updates or get help with workload adjustment?",
    }


# INTENT CLASSIFICATION
tool_registry: dict[str, dict[str, Callable]] = {
    "synthesize_updates": {
        "description": "User wants to understand team updates or trends",
        "function": synthesize_updates,
    },
    "synthesize_adjust_workload": {
        "description": "User wants help with workload adjustment",
        "function": synthesize_adjust_workload,
    },
}


# This intent classification is used to route the user's message to the appropriate function.
def intent_classification(
    message: str,
) -> UpdatesSynthesisContent | AdjustWorkloadContent | Content:
    """Use this to classify the user's intent."""
    system_template = """
                Classify the user's intent into ONLY one of these categories:
                - synthesize_updates: User wants to understand team updates or trends
                - synthesize_adjust_workload: User wants help with workload adjustment
                
                If the message doesn't clearly fit either category, choose the closest match but include a clarifying message.
                """

    user_message = f"""
        Here is the user's message:
            {message}
    """

    completion = client.beta.chat.completions.parse(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_template,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        response_format=IntentClassificationResponse,
    )

    response_data = completion.choices[0].message.parsed
    validated_response = IntentClassificationResponse.model_validate(response_data)
    intent, confidence = validated_response.intent, validated_response.confidence

    print("INTENT", validated_response.intent)

    # TODO: add retry logic to only allow to ask for clarification 3 times or so
    if confidence < 0.7:
        #     intent.type = "SimpleMessage"
        #     intent.string = "I'm not quite sure what you're asking. Could you please clarify if you want to understand team updates or get help with workload adjustment?"
        #     return intent

        print("confidence is less than 0.7")
        return ask_for_clarification(message)
    else:
        print("confidence is greater than 0.7", confidence)
        print("intent", intent)
        print(f"from intent classification, {tool_registry[intent]['description']}")
        return tool_registry[intent]["function"](message)
