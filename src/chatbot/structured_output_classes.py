from pydantic import BaseModel
from typing import List, Literal, Optional


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


class Content(BaseModel):
    title: str
    sections: List[Section]
    type: Literal["StructuredResponse"]
    simpleMessage: Optional[str] = None


class UpdatesSynthesisContent(Content):
    insights: List[Card]


class AdjustWorkloadContent(Content):
    conclusion: List[Section]


class IntentClassificationResponse(BaseModel):
    intent: Literal["synthesize_updates", "synthesize_adjust_workload"]
    confidence: float
    string: Optional[str] = None
    content: Optional[Content] = None
    type: Literal["SimpleMessage", "StructuredResponse"]
