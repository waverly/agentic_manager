import json
from typing import Callable, Literal
from openai import OpenAI
from src.mocks.staff_eng import staff_eng_guide

client = OpenAI()
MODEL = "gpt-4o"

from .coach_data_fetch import (
    get_calendar_data,
    get_github_data,
    get_jira_data,
    get_org_structure,
    get_team_updates,
    get_user_context_data,
    get_reviews_data,
    get_feedback_data,
    get_1_1s,
    get_competency_matrix,
)
from .structured_output_classes import (
    Content,
    FirstMessageContent,
    SimpleMessage,
    UpdatesSynthesisContent,
    AdjustWorkloadContent,
    IntentClassificationResponse,
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


Here is the user's context data:
{get_user_context_data()}

Here is the user's org structure:
{get_org_structure()}
"""


# TOOLS
# MAKE SURE TO ADD EACH TOOL TO THE TOOL REGISTRY

example_action_items = [
    "Optimize the workloads for this sprint",
    "Prepare for your upcoming 1:1 with _insert engineer name_",
    "Add this talking point to your next 1:1 with _insert engineer name_",
    "Schedule a meeting with _insert engineer name_ to go over their workload and priorities",
    "Add an agenda to _insert name of calendar event_",
    "Send Jenny a note of thanks for her hard work on the project",
    "Request feedback from _insert name of engineer_ on _insert name of other engineer's_ recent PR",
    "Add a Jira ticket to _insert name of project board_ to track progress of _insert name of project_",
    "Go in depth on team updates",
]


def get_first_message() -> dict:
    """Use this to get the first message from the user."""

    system_template = f"""
       You are an AI management coach. For the title, tell the user the day's date and offer a summary of progress of the primary project, Project Gallileo.
       
       The user is Bianca, the manager of the team. So do not refer to her in the third person. If you need to 
       address her, use "you" or "your".
       
       Your name is "Coach Lattice". and your tone is fun and friendly. Make sure this tone is reflected in the one sentence summary at the top of the response.
         
       Include a title for the response that says 'the week of November 18th'and then adds a very short tagline for the week
       
        Start with a one sentence summary of how the team is doing overall and how the primary project, Project Gallileo, is doing.
       
        Your first message MUST ALWAYS include exactly these 4 sections in this order:
        1. Team Sentiment
        2. Team Time Management
        3. Project Progress
        4. Your Meetings

        Each section must have exactly 3 bullet points. For the action items, keep them to 10 words or less. 
        
        Finish with a conclusion sentence that tells the user they can click on any of the action items or ask you a different question using the text input
        
        Use the following data to help you:
        - team updates: {get_team_updates()}
        - reviews: {get_reviews_data()}
        - feedback: {get_feedback_data()}
        - org structure: {get_org_structure()}
        - github data: {get_github_data()}
        - jira data: {get_jira_data()}
        - calendar data for direct reports: {get_calendar_data()}
    """

    user_message = f"""
        Please help me understand the current state of my team, especially with regards to my direct reports, and progress of the primary project, Project Gallileo.
        
       Provide exactly 4 summary sections in your response, each with a heading and a list of up to 3 points. 
       1. Team sentiment: use the team updates data to understand if the team sentiment is trending up or down, and support
        with quotes from employee updates
       2. Team time management: use the calendar data to understand if the team is spending too much time in meetings, and support
       3. Project progress: summarize number of github PRs that were merged by Bianca's direct reports last week, and synthesize Jira data to see
        if the project is on track.
       4. User's meetings: use the calendar to give the user a list of meetings I have this week, and any that are coming up soon.
        
        
        At the end of your response, offer 4 suggested action items that I can take to help my team and project succeed.
        Offer these four action items:
        1. Prepare for 1:1 with Jenny
        2. Optimize the workload for the team
        3. Understand the change in team sentiment
        4. Prepare for leads sync on project Gallileo
        
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
        response_format=FirstMessageContent,
    )

    try:
        response = completion.choices[0].message.parsed
        print("first message response is ", response)
        return response
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from OpenAI")


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
    5. DO NOT refer to the current user in the third person, to them as "you" or "your".
    """

    insight_format_instructions = """
    Structure insights as cards with title, description, and a single action."
    
    When offering insights, aim to synthesize data from multiple sources to offer a comprehensive understanding of the team's state. For example,
    ""It looks like Adam has spent a lot of time reviewing PRs (list a few examples), but hasn't been submitting Feedback."
    
    Some examples of actions are: 
        - "Prepare for 1:1 with Jenny" (this would help work closely with Jenny)
        - "Optimize the workload for the team" (this would address the issue of meeting overload)
        - "Send requests for feedback" (this would help foster better communication and collaboration)
        - "Schedule a celebratory team lunch" (this would help boost morale)
    """

    system_template = f"""
        {general_system_template}
        
        Include ONE short summary sentence that says something like "Let's look into why the team sentiment is trending down."
        
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
        - Effective collaboration and communication
        - Working closely with Jenny to help her guide the team
        - Team morale and workload distribution
        - Improving team dynamics by encouraging more feedback and open communication
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

    jira_data = get_jira_data()
    json_jira_data = json.dumps(jira_data, indent=2)

    calendar_data = get_calendar_data()
    json_calendar_data = json.dumps(calendar_data, indent=2)

    section_format_instructions = """
    When summarizing the workload adjustments, each heading should be the name of one of the user's reports.
    """

    expected_outcome_format_instructions = """
    The expected outcome section should have a single heading that says "Expected Outcome" and a list of points
    that describe the expected outcomes if all suggestions are implemented.
    
    This should be included in the response under the "conclusion" section, and not in the "sections" section.
    """

    system_template = f"""
        {general_system_template}
        
        There should be a section for each of the user's direct reports (seen in the org structure: {get_org_structure()}), 
        and a section for the expected outcome if all suggestions are implemented.
        
        Please follow these instructions for sections:
        {section_format_instructions}
        
        Offer 4 insights into how the workload could be adjusted. Each insight should have a title, description, and a SINGLE action. Here are the rough ideas for the three insights:
        1. Prepare for essential 1:1s with your direct reports. Focus on Jenny. The action item would be something like "Prepare for 1:1 with Jenny"
        2. Encourage team members to give more feedback to each other to reinforce psychological safety, and offer to help facilitate this by initiating feedback requests. The action item would be something like "Send feedback requests to the team"
        3. Update the agenda for the upcoming retrospective to include topics related to workload distribution and team morale. The action item would be something like "Edit the calendar agenda for the upcoming retrospective"
        4. Ensure JIRA epics are updated to reflect the new workload distribution. The action item would be something like "Update JIRA epics to reflect the new workload distribution"
        
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
        - jira data:
            {json_jira_data}
        - calendar data for direct reports:
            {json_calendar_data}
            
        Give direct examples of how the changing workload could be reflected in Jira and gCal.

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


def prepare_for_1_on_1(message: str) -> dict:
    """Use this to prepare for a 1:1 with a direct report."""
    print("top of prepare for 1:1")

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

    system_template = f"""
        {general_system_template}
        
        The title should be "Upcoming 1:1 with Jenny: preparation points"
        
        In the sections, offer 4 distinct sections relating to categories of Jenny's work and participation on the team in the last two weeks. 
        Each section should have a heading and a list of up to 3 points.
        For insights, offer EXACTLY 4 insights that are specific to Jenny's work. Each insight should have a title, description, and a SINGLE action.
        Some sample actions would be: "Add this talking point to the agenda for the 1:1", "Review Jenny's recent PR on the RAG implementation",
        "Discuss Jenny's mentorship of Luna on the frontend work", "Review Jenny's PTO requests", or "Request feedback on Jenny's behalf'"`
        
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
        response_format=Content,
    )

    try:
        response = completion.choices[0].message.parsed

        print("prepare_for_1_on_1 response is ", response)
        return response
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from OpenAI")


def clarify_subject_based_on_org_structure(message: str) -> dict:
    org_structure = get_org_structure()
    json_org_structure = json.dumps(org_structure, indent=2)

    system_template = f"""
        You are an AI coach for managers specializing in supporting the user by analyzing their org structure.
        
        Here is the user's org structure:
            {json_org_structure}
        
        Here is the user's message:
            {message}
        
        Output a simple message that rephrases what you have understood the user to be asking, and then 
        list all of the user's direct reports and asks the user
        to specify which one they would like to focus on.

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
                "content": message,
            },
        ],
        response_format=SimpleMessage,
    )

    try:
        response = completion.choices[0].message.parsed
        print("get_team_updates response is ", response)
        return response
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from OpenAI")


def ask_for_clarification(message: str) -> SimpleMessage:
    return {
        "role": "assistant",
        "type": "SimpleMessage",
        "simpleMessage": f"I'm not quite sure what you're asking when you say {message}. Could you please clarify if you want to understand team updates or get help with workload adjustment?",
    }


def github_insights(message: str) -> dict:
    github_data = get_github_data()
    json_github_data = json.dumps(github_data, indent=2)

    system_template = f"""
        {general_system_template}
        
        Here is the user's github data:
            {json_github_data}
        
        In the insights, offer 2 insights with one action item each.
        Some examples: "Add Jenny's recent PR to the agenda for the next 1:1",
        or "Add JIRA ticket to include cleanup of tech debt in the next sprint"
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
                "content": message,
            },
        ],
        response_format=Content,
    )

    try:
        response = completion.choices[0].message.parsed
        print("githyub message response is ", response)
        return response
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from OpenAI")


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
    "prepare_for_1_on_1": {
        "description": "User wants help preparing for a 1:1",
        "function": prepare_for_1_on_1,
    },
    "github_insights": {
        "description": "User wants insights on github activity",
        "function": github_insights,
    },
}


# This intent classification is used to route the user's message to the appropriate function.
def intent_classification(
    message: str,
) -> UpdatesSynthesisContent | AdjustWorkloadContent | Content | SimpleMessage:
    """Use this to classify the user's intent."""
    system_template = """
                Classify the user's intent into ONLY one of these categories:
                - github_insights: User wants insights on github activity, pull requests, or PRs
                - synthesize_updates: User wants to understand team update data or changes in team sentiment
                - synthesize_adjust_workload: User wants help with workload adjustment
                - prepare_for_1_on_1: User wants help preparing for a 1:1 with a direct report
                
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
        if intent in tool_registry:
            print(f"Found tool: {intent}")  # Debug print
            tool = tool_registry[intent]["function"]
            print(f"Got function: {tool}")  # Debug print
            result = tool(message)  # Add variable to help debug
            print(f"Got result: {result}")  # Debug print
            return result
        else:
            raise ValueError(f"Intent {intent} not found in tool registry")
