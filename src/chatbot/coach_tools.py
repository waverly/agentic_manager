from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path
from openai import OpenAI

client = OpenAI()
MODEL = "gpt-4o"


# Data retrieval
def get_team_updates() -> dict:
    """Use this to get the user's competency matrix."""
    json_path = Path(__file__).parent.parent / "mocks" / "coach_updates.json"
    with open(json_path) as f:
        return json.load(f)


# structured output models
class Point(BaseModel):
    text: str
    citations: List[int]


class Card(BaseModel):
    title: str
    description: str
    actions: List[str]


class CardPoint(BaseModel):
    card: Card


class Section(BaseModel):
    heading: str
    points: List[Point]


class UpdatesSynthesisContent(BaseModel):
    title: str
    sections: List[Section]
    insights: List[Card]


class StructuredResponse(BaseModel):
    type: str = "structured_response"
    content: UpdatesSynthesisContent


# Data processing
example_structured_output = """
{
  "type": "structured_response",
  "content": {
    "title": "Summary of Reports' Updates for the Last Four Weeks",
    "sections": [
      {
        "heading": "1. Increasing Meeting Overload",
        "points": [
          {
            "text": "Both Jenny and Luna have consistently mentioned spending over 15 hours in meetings weekly, leaving little time for deep work.",
            "citations": [2]
          },
          {
            "text": "Their updates express frustration over a lack of progress on their key deliverables due to the constant context-switching.",
            "citations": [2]
          }
        ]
      },
      {
        "heading": "2. Low Morale Due to Overwork",
        "points": [
          {
            "text": "Luna and Jeremy mentioned feeling burned out, particularly in Weeks 3 and 4, citing deadlines that felt overly ambitious.",
            "citations": [2]
          },
          {
            "text": "Jenny shared that she worked late multiple nights to \"stay afloat\" and felt under appreciated for her effort.",
            "citations": [1]
          }
        ]
      },
      {
        "heading": "3. Decreasing Psychological Safety",
        "points": [
          {
            "text": "Multiple team members (Adam and Luna) have indicated they feel less comfortable bringing up tough issues during team meetings.",
            "citations": [2]
          },
          {
            "text": "One report explicitly wrote in Week 4 that team discussions feel \"dominated by a few voices,\" making it difficult for others to contribute.",
            "citations": [1]
          }
        ]
      },
      {
        "heading": "Insights and Suggestions",
        "points": [
          {
            "card": {
              "title": "Meeting overload",
              "description": "Meeting overload is affecting productivity and morale",
              "actions": [
                "Add as 1:1 topic with Jenny and Luna",
                "Analyze your team's Meetings"
              ]
            }
          },
          {
            "card": {
              "title": "Workload imbalance",
              "description": "Workload imbalance and unclear priorities are leading to burnout",
              "actions": [
                "Review team's work summaries",
                "Adjust workloads based on strengths"
              ]
            }
          }
        ]
      }
    ]
  }
}"""

general_system_template = """
You are an AI assistant specializing in supporting HR professionals and managers by analyzing team updates, sentiment trends, and workplace dynamics. Your goal is to provide clear, concise, and actionable insights based on team feedback, updates, and behaviors. Respond to user questions by synthesizing information into summaries or recommendations, ensuring empathy, professionalism, and relevance.

When responding:

- Identify key themes, trends, or patterns from team updates or data.
- Provide actionable suggestions to improve team morale, productivity, or alignment.
- Use concise and accessible language.
- Tailor responses to the user's request, whether they need summaries, insights, or strategies.
"""

# prior to adopting structured output, i tried this approach
unused_format_instructions = """
    ALWAYS generate a title for your response and include it in the "title" field. For example, if the user asks "Summarize my team’s recent updates so I can understand why their sentiment is trending down", 
    the title should be "Summary of Reports' Updates for the Last Four Weeks".
    
    ALWAYS respond with valid JSON that matches this structure:

    {example_structured_output}
"""


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
        You are an AI assistant specializing in supporting HR professionals and managers by 
        analyzing team updates, 
        sentiment trends, and workplace dynamics.
        
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
        print("completion sut wus tsut", completion)
        response = completion.choices[0].message.parsed

        print("get_team_updates response is ", response)
        return response
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON response from OpenAI")
