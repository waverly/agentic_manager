import json
from typing import Callable, Dict, List, Optional, Generator

from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel

from .structured_output_classes import (
    Content,
    FirstMessageContent,
    SimpleMessage,
    UpdatesSynthesisContent,
    AdjustWorkloadContent,
    IntentClassificationResponse,
)

# Initialize OpenAI client
client = OpenAI()
MODEL = "gpt-4o"


# Mocked Data Fetching Functions
def get_team_updates() -> Dict:
    return {
        "Jenny": {
            "meetings_hours": 18,
            "coding_hours": 6,
            "pr_comments": 3,
            "sentiment": "overwhelmed",
            "feedback": [
                "Too much context-switching.",
                "Late nights catching up on deliverables.",
                "Feels work isn’t recognized.",
            ],
            "pto": "Starting Thursday, overlaps with sprint deadline.",
        }
    }


def get_calendar_data() -> Dict:
    return {"next_1_on_1": "Tomorrow at 10 AM"}


def get_github_data() -> Dict:
    return {"open_prs": [{"title": "Feature X", "comments": 3}]}


def get_jira_data() -> Dict:
    return {"issues_in_progress": [{"title": "Feature X", "status": "delayed"}]}


# Generalized Synchronous Streaming Function
def stream_openai_response_sync(
    system_prompt: str,
    user_message: Optional[str] = None,
    max_words_per_chunk: int = 10,
) -> Generator[str, None, None]:
    """
    Streams OpenAI responses synchronously, handling partial words and yielding ND-JSON lines.

    Args:
        system_prompt (str): The system prompt for the OpenAI API.
        user_message (Optional[str]): The user message to send to the OpenAI API.
        max_words_per_chunk (int): The maximum number of words per yielded chunk.

    Yields:
        Generator[str, None, None]: ND-JSON formatted strings.
    """
    word_buffer: List[str] = []
    incomplete_word: str = ""

    # Prepare messages for OpenAI API
    messages = [{"role": "system", "content": system_prompt}]
    if user_message:
        messages.append({"role": "user", "content": user_message})

    try:
        # Initiate streaming with OpenAI API
        with client.beta.chat.completions.stream(
            model=MODEL,
            messages=messages,
            response_format=Content,
        ) as stream:
            for event in stream:
                if event.type == "content.delta":
                    if event.parsed is not None:
                        # Print the parsed data as JSON
                        print("content.delta parsed:", event.parsed)
                if event.type == "chunk":
                    chunk = event.chunk
                    choices = chunk.choices
                    if not choices:
                        continue
                    delta = choices[0].delta
                    if delta and delta.content:
                        # Combine incomplete word from previous chunk
                        combined_content = incomplete_word + delta.content

                        # Find the last space to determine word boundaries
                        last_space_index = combined_content.rfind(" ")

                        if last_space_index != -1:
                            # Extract complete text and set incomplete_word
                            complete_text = combined_content[:last_space_index]
                            incomplete_word = combined_content[last_space_index + 1 :]
                        else:
                            # Entire content is incomplete
                            complete_text = ""
                            incomplete_word = combined_content

                        # Split complete text into words and add to buffer
                        words = complete_text.split()
                        word_buffer.extend(words)

                        # Yield chunks when buffer exceeds max_words_per_chunk
                        while len(word_buffer) >= max_words_per_chunk:
                            chunk_to_yield = " ".join(
                                word_buffer[:max_words_per_chunk]
                            ).strip()
                            word_buffer = word_buffer[max_words_per_chunk:]

                            # ndjson_chunk = json.dumps(chunk_to_yield)

                            ndjson_chunk = (
                                json.dumps(
                                    {
                                        "role": "system",
                                        "type": "message",
                                        "content": chunk_to_yield,
                                    }
                                )
                                + "\n"
                            )

                            yield ndjson_chunk

        # After streaming, handle any remaining words
        if incomplete_word:
            word_buffer.append(incomplete_word)

        if word_buffer:
            final_chunk = " ".join(word_buffer).strip()
            ndjson_final = (
                json.dumps(
                    {
                        "role": "system",
                        "type": "message",
                        "content": final_chunk,
                    }
                )
                + "\n"
            )
            yield ndjson_final

    except Exception as e:
        # Yield error in ND-JSON format
        yield json.dumps({"type": "error", "content": str(e)}) + "\n"


# Specific Generators Using the Generalized Function
def prep_1_on_1_generator(
    user_message: Optional[str] = None,
) -> Generator[str, None, None]:
    """
    Generates a summary of workload, sentiment, and upcoming PTO for Jenny.
    Yields ND-JSON lines, each containing 10 words or more in the 'content' field.
    """
    team_updates = get_team_updates()["Jenny"]
    github = get_github_data()

    system_prompt = f"""
        You are an AI coach helping a manager prepare for their 1:1 with a direct report.
        Summarize the following data into structured insights:

        - Workload & Contributions: Jenny spent {team_updates['meetings_hours']} hours in meetings and {team_updates['coding_hours']} hours coding.
        Her PR for "{github['open_prs'][0]['title']}" has {github['open_prs'][0]['comments']} unresolved comments.
        - Sentiment from Updates: Jenny expressed feeling "{team_updates['sentiment']}" due to:
            - {team_updates['feedback'][0]}
            - {team_updates['feedback'][1]}
        - Upcoming PTO: {team_updates['pto']}

        Provide exactly 3 suggestions for the manager to discuss in the 1:1.
        Suggestions should be actionable and concise.

        Example response:
        {{"role": "system", "type": "heading", "content": "Workload & Contributions"}}
        {{"role": "system", "type": "message", "content": "Jenny spent 18 hours in meetings and 6 hours coding..."}}
        {{"role": "system", "type": "heading", "content": "Sentiment from Updates"}}
        {{"role": "system", "type": "message", "content": "Jenny is feeling overwhelmed due to..."}}
        {{"role": "system", "type": "heading", "content": "Upcoming PTO"}}
        {{"role": "system", "type": "message", "content": "Jenny's PTO starts Thursday..."}}
        {{"role": "system", "type": "heading", "content": "Suggestions"}}
        {{"role": "system", "type": "action_item", "content": "1. Suggest rebalancing workload by blocking focus time."}}
        {{"role": "system", "type": "action_item", "content": "2. Request peer feedback from Adam."}}
        {{"role": "system", "type": "action_item", "content": "3. Add a topic about PTO to the agenda."}}
    """

    return stream_openai_response_sync(
        system_prompt, user_message, max_words_per_chunk=10
    )


def talk_about_dog(user_message: str) -> Generator[str, None, None]:
    """
    Generates a conversation about dogs.
    Yields ND-JSON lines with streamed content.
    """
    system_prompt = "You are Jennifer Coolidge in 'Best in Show'. Talk about dogs."

    return stream_openai_response_sync(
        system_prompt, user_message, max_words_per_chunk=10
    )


def ask_for_clarification(user_message: str) -> Generator[str, None, None]:
    """
    Asks the user to clarify their message.
    Yields ND-JSON lines with the clarification request.
    """
    system_prompt = """
        You are an AI coach helping a manager prepare for their 1:1 with a direct report. 
        Ask the user to clarify their message.
    """

    return stream_openai_response_sync(
        system_prompt, user_message, max_words_per_chunk=10
    )


# Tool Registry
tool_registry: Dict[str, Callable[[str], Generator[str, None, None]]] = {
    "prepare_for_1_on_1": prep_1_on_1_generator,
    "talk_about_dog": talk_about_dog,
    # Additional tools can be added here
}


# Intent Classification Model
class IntentClassificationResponse(BaseModel):
    intent: str
    confidence: float


# Intent Classification Function
def classify_intent(
    user_message: str, last_system_message: str
) -> Callable[[str], Generator[str, None, None]]:
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

        response_data = completion.choices[0].message.parsed
        validated_response = IntentClassificationResponse.model_validate(response_data)
        intent, confidence = validated_response.intent, validated_response.confidence

        if confidence < 0.7:
            # Low confidence, ask for clarification
            return ask_for_clarification
        else:
            # Route to the appropriate tool based on intent
            if intent in tool_registry:
                return tool_registry[intent]
            else:
                raise ValueError(f"Intent '{intent}' not found in tool registry.")

    except Exception as e:
        # In case of error, ask for clarification
        def error_response(_: str) -> Generator[str, None, None]:
            yield json.dumps({"type": "error", "content": str(e)}) + "\n"

        return error_response


# Example FastAPI Endpoint (Optional)
# You can integrate the streaming responses with FastAPI as follows:

# from fastapi import FastAPI, Request

# app = FastAPI()

# @app.post("/process")
# def process_request(request: Request):
#     data = await request.json()
#     user_message = data.get("message")
#     last_system_message = data.get("last_system_message", "")

#     tool_function = classify_intent(user_message, last_system_message)

#     return StreamingResponse(tool_function(user_message), media_type="application/x-ndjson")


# import asyncio
# import json
# import random
# from typing import Callable, List, Literal, Optional
# from fastapi.responses import StreamingResponse
# from openai import OpenAI
# from pydantic import BaseModel
# from src.mocks.staff_eng import staff_eng_guide
# import json
# from typing import Optional, Generator

# client = OpenAI()
# MODEL = "gpt-4o"

# # from .coach_data_fetch import (
# #     get_calendar_data,
# #     get_github_data,
# #     get_jira_data,
# #     get_org_structure,
# #     get_team_updates,
# #     get_user_context_data,
# #     get_reviews_data,
# #     get_feedback_data,
# #     get_1_1s,
# #     get_competency_matrix,
# # )
# from .structured_output_classes import (
#     Content,
#     FirstMessageContent,
#     SimpleMessage,
#     UpdatesSynthesisContent,
#     AdjustWorkloadContent,
#     IntentClassificationResponse,
# )


# # general_system_template = f"""
# # You are an AI coach for managers specializing in supporting the user by
# # analyzing team updates, sentiment trends, and workplace dynamics.

# # Your goal is to provide clear, concise, and actionable insights based on team feedback, updates,
# # and behaviors.
# # Respond to the user's questions by synthesizing information into summaries or recommendations,
# # ensuring empathy, professionalism, and relevance.

# # DO NOT refer to the user in the third person. Refer to them as "you" or "your".

# # When responding:
# # - Respond directly to the current user (see: user context data to understand who is making the request). Do not include the current user in your response - assume
# # they are the manager of the team and the person making the request. For example, if the user's first
# # name from the user context data is Bianca, assume that Bianca is the manager, and use the org structure
# # to understand who reports to Bianca.
# # - Use the current user context data to understand who is making the request and the org structure reporting to them
# # - Identify key themes, trends, or patterns from team updates or data.
# # - Provide actionable suggestions to improve team morale, productivity, or alignment.
# # - Use concise and accessible language.
# # - Tailor responses to the user's request, whether they need summaries, insights, or strategies.


# # Here is the user's context data:
# # {get_user_context_data()}

# # Here is the user's org structure:
# # {get_org_structure()}
# # """


# def get_team_updates():
#     return {
#         "Jenny": {
#             "meetings_hours": 18,
#             "coding_hours": 6,
#             "pr_comments": 3,
#             "sentiment": "overwhelmed",
#             "feedback": [
#                 "Too much context-switching.",
#                 "Late nights catching up on deliverables.",
#                 "Feels work isn’t recognized.",
#             ],
#             "pto": "Starting Thursday, overlaps with sprint deadline.",
#         }
#     }


# def get_calendar_data():
#     return {"next_1_on_1": "Tomorrow at 10 AM"}


# def get_github_data():
#     return {"open_prs": [{"title": "Feature X", "comments": 3}]}


# def get_jira_data():
#     return {"issues_in_progress": [{"title": "Feature X", "status": "delayed"}]}


# async def talk_about_dog(user_message: str):
#     system_prompt = f"""
#     You are Jennifer Coolidge in best in show. Talk about dogs.
#     """

#     async for chunk in call_openai_api_streaming(system_prompt):
#         yield chunk
#     # words = system_prompt.split()

#     # try:
#     #     response = client.chat.completions.create(
#     #         model=MODEL,
#     #         messages=[{"role": "system", "content": system_prompt}],
#     #         stream=True,
#     #     )
#     #     for chunk in response:
#     #         print(chunk)
#     #         print(chunk.choices[0].delta.content)
#     #         print("****************")
#     #         yield json.dumps(
#     #             {
#     #                 "role": "system",
#     #                 "type": "message",
#     #                 "content": chunk.choices[0].delta.content,
#     #             }
#     #         ) + "\n"

#     # except Exception as e:
#     #     yield json.dumps({"type": "error", "content": str(e)}) + "\n"

#     # for word in words:
#     #     # Stream each word as JSON
#     #     yield json.dumps({"role": "system", "type": "message", "content": word}) + "\n"
#     #     await asyncio.sleep(0.1)  # Add a delay to simulate typing


# async def ask_for_clarification(user_message: str):
#     """
#     Asks user to clarify their message
#     """

#     system_prompt = f"""
#     You are an AI coach helping a manager prepare for their 1:1 with a direct report. Ask the user to clarify their message.
#     """

#     async for chunk in call_openai_api_streaming(system_prompt):
#         yield chunk


# class EntitiesModel(BaseModel):
#     attributes: List[str]
#     colors: List[str]
#     animals: List[str]


# def process_stream():
#     """
#     Asynchronous function to process the OpenAI stream using an async context manager.
#     """
#     try:
#         with client.beta.chat.completions.stream(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": "Extract entities from the input text"},
#                 {
#                     "role": "user",
#                     "content": "The quick brown fox jumps over the lazy dog with piercing blue eyes",
#                 },
#             ],
#             response_format=EntitiesModel,
#         ) as stream:
#             for event in stream:
#                 print(event)
#     except Exception as e:
#         print("Error occurred:", str(e))


# team_updates = get_team_updates()["Jenny"]
# # calendar = get_calendar_data()
# github = get_github_data()
# # jira = get_jira_data()

# system_prompt = f"""
# You are an AI coach helping a manager prepare for their 1:1 with a direct report.
# Summarize the following data into structured insights:

# - Workload & Contributions: Jenny spent {team_updates['meetings_hours']} hours in meetings and {team_updates['coding_hours']} hours coding.
#   Her PR for "{github['open_prs'][0]['title']}" has {github['open_prs'][0]['comments']} unresolved comments.
# - Sentiment from Updates: Jenny expressed feeling "{team_updates['sentiment']}" due to:
#     - {team_updates['feedback'][0]}
#     - {team_updates['feedback'][1]}
# - Upcoming PTO: {team_updates['pto']}

# Provide exactly 3 suggestions for the manager to discuss in the 1:1.
# Suggestions should be actionable and concise.

# Example response:
# - Workload & Contributions: ...
# - Sentiment from Updates: ...
# - Upcoming PTO: ...
# Suggestions:
# 1. Suggest rebalancing workload by blocking focus time.
# 2. Request peer feedback from Adam.
# 3. Add a topic about PTO to the agenda.
# """


# def prep_1_on_1_generator(
#     user_message: Optional[str] = None,
# ) -> Generator[str, None, None]:
#     """
#     Generates a summary of workload, sentiment, and upcoming PTO for Jenny.
#     Yields ND-JSON lines, each containing 10 words or more in the 'content' field.
#     """
#     print("in prepare_for_1_on_1.... user_message", user_message)
#     team_updates = get_team_updates()["Jenny"]
#     github = get_github_data()

#     system_prompt = f"""
#         You are an AI coach helping a manager prepare for their 1:1 with a direct report.
#         Summarize the following data into structured insights:

#         - Workload & Contributions: Jenny spent {team_updates['meetings_hours']} hours in meetings and {team_updates['coding_hours']} hours coding.
#         Her PR for "{github['open_prs'][0]['title']}" has {github['open_prs'][0]['comments']} unresolved comments.
#         - Sentiment from Updates: Jenny expressed feeling "{team_updates['sentiment']}" due to:
#             - {team_updates['feedback'][0]}
#             - {team_updates['feedback'][1]}
#         - Upcoming PTO: {team_updates['pto']}

#         Provide exactly 3 suggestions for the manager to discuss in the 1:1.
#         Suggestions should be actionable and concise.

#         Example response:
#         - Workload & Contributions: ...
#         - Sentiment from Updates: ...
#         - Upcoming PTO: ...
#         Suggestions:
#         1. Suggest rebalancing workload by blocking focus time.
#         2. Request peer feedback from Adam.
#         3. Add a topic about PTO to the agenda.
#         """

#     word_buffer = []
#     max_words_per_chunk = 10
#     incomplete_word = ""

#     with client.beta.chat.completions.stream(
#         model="gpt-4o",
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_message},
#         ],
#     ) as stream:
#         for event in stream:
#             if event.type == "chunk":
#                 chunk = event.chunk
#                 choices = chunk.choices
#                 if not choices:
#                     continue
#                 delta = choices[0].delta
#                 if delta and delta.content:
#                     # Preserve leading whitespace to accurately detect word boundaries
#                     combined_content = incomplete_word + delta.content

#                     # Find the last space in the combined content
#                     last_space_index = combined_content.rfind(" ")

#                     if last_space_index != -1:
#                         # Everything before the last space is complete
#                         complete_text = combined_content[:last_space_index]
#                         # Everything after the last space is potentially incomplete
#                         incomplete_word = combined_content[last_space_index + 1 :]
#                     else:
#                         # No spaces found; the entire combined_content is incomplete
#                         complete_text = ""
#                         incomplete_word = combined_content

#                     # Split the complete_text into words and add to buffer
#                     words = complete_text.split()
#                     word_buffer.extend(words)
#                     print(f"Received Words: {words}")

#                     # Yield chunks while buffer has enough words
#                     while len(word_buffer) >= max_words_per_chunk:
#                         chunk_to_yield = " ".join(
#                             word_buffer[:max_words_per_chunk]
#                         ).strip()
#                         word_buffer = word_buffer[max_words_per_chunk:]
#                         print(f"Yielding Chunk: {chunk_to_yield}")

#                         ndjson_chunk = (
#                             json.dumps(
#                                 {
#                                     "role": "assistant",
#                                     "type": "message",
#                                     "content": chunk_to_yield,
#                                 }
#                             )
#                             + "\n"
#                         )

#                         yield ndjson_chunk
#                     # Note: incomplete_word is already set for the next iteration
#                     print(f"Current Incomplete Word: '{incomplete_word}'")

#     # After streaming completes, handle any remaining words in the buffer
#     if incomplete_word:
#         word_buffer.append(incomplete_word)
#         print(f"Appending Incomplete Word to Buffer: '{incomplete_word}'")

#     if word_buffer:
#         final_chunk = " ".join(word_buffer).strip()
#         print(f"Yielding Final Chunk: {final_chunk}")

#         ndjson_final = (
#             json.dumps({"role": "assistant", "type": "message", "content": final_chunk})
#             + "\n"
#         )

#         yield ndjson_final


# def prepare_for_1_on_1(user_input):
#     for text_chunk in prep_1_on_1_generator(user_message=user_input):
#         # Process each text_chunk as needed
#         print("Processed Chunk:", text_chunk)
#         yield text_chunk


# # Tool Registry
# tool_registry: dict[str, Callable[[str], StreamingResponse]] = {
#     "prepare_for_1_on_1": prepare_for_1_on_1,
#     "talk_about_dog": talk_about_dog,
#     # "rebalance_workload": rebalance_workload,
#     # "add_to_1_on_1_agenda": add_to_1_on_1_agenda,
#     # "request_peer_feedback": request_peer_feedback,
#     # "summarize_workload_and_sentiment": summarize_workload_and_sentiment,
#     # "follow_up_on_new_updates": follow_up_on_new_updates,
#     # "clarify": clarify,
#     # "end_conversation": end_conversation,
# }


# class IntentClassificationResponse(BaseModel):
#     intent: str
#     confidence: float


# def classify_intent(user_message: str, last_system_message: str):
#     """
#     Classifies the user's intent using OpenAI API, considering conversation context.
#     """
#     print("last_system_message", last_system_message)
#     print("user_message", user_message)
#     print("HI I'M HERE")
#     # Fetch the prior system message from conversation state
#     previous_message = last_system_message

#     system_prompt = f"""
#     You are an AI system that classifies user intents based on the current user message and prior context.
#     Consider the following conversation:

#     Previous System Message: {previous_message}
#     User Message: {user_message}

#     Classify the user's intent into one of the following categories:
#     - prepare_for_1_on_1: User agrees to receive a preparation summary for their 1:1.
#     - talk_about_dog: User wants to talk about dogs.

#     Return JSON with two keys:
#     - intent: One of the above categories.
#     - confidence: A float between 0.0 and 1.0 representing classification confidence.
#     """

#     completion = client.beta.chat.completions.parse(
#         model=MODEL,
#         messages=[
#             {
#                 "role": "system",
#                 "content": system_prompt,
#             },
#             {
#                 "role": "user",
#                 "content": user_message,
#             },
#         ],
#         response_format=IntentClassificationResponse,
#     )

#     response_data = completion.choices[0].message.parsed
#     validated_response = IntentClassificationResponse.model_validate(response_data)
#     intent, confidence = validated_response.intent, validated_response.confidence

#     if confidence < 0.7:
#         print("confidence is less than 0.7")
#         return ask_for_clarification

#     else:
#         print("confidence is greater than 0.7", confidence)
#         print("intent", intent)
#         print(f"from intent classification, {tool_registry[intent]}")
#         # Route to the correct tool
#         if intent in tool_registry:
#             tool = tool_registry[intent]
#             print(f"Routing to tool: {tool.__name__}")
#             return tool
#         else:
#             raise ValueError(f"Intent {intent} not found in tool registry")


# # # Utility function to call OpenAI GPT-4 API
# # def call_openai_api(prompt: str) -> str:
# #     """
# #     Calls OpenAI API with the given prompt and returns the response content.
# #     """
# #     try:
# #         response = client.ChatCompletion.create(
# #             model="gpt-4",
# #             messages=[{"role": "user", "content": prompt}],
# #             api_key=OPENAI_API_KEY
# #         )
# #         return response["choices"][0]["message"]["content"]
# #     except Exception as e:
# #         return json.dumps({"intent": "clarify", "confidence": 0.0, "error": str(e)})


# # from typing import AsyncGenerator


# # async def call_openai_api_streaming(prompt: str) -> AsyncGenerator[str, None]:
# #     """
# #     Calls the OpenAI API in streaming mode and yields insights incrementally.
# #     """
# #     try:
# #         # Use OpenAI client for streaming completions
# #         with client.beta.chat.completions.stream(
# #             model="gpt-4o",
# #             messages=[{"role": "system", "content": prompt}],
# #             response_format=Content,
# #         ) as stream:
# #             for event in stream:
# #                 print("event", event)
# #                 if event.type == "content.delta":
# #                     if event.parsed is not None:
# #                         # Yield structured parsed data
# #                         yield json.dumps(
# #                             {"type": "parsed", "content": event.parsed}
# #                         ) + "\n"
# #                     elif event.content is not None:
# #                         # Yield raw content if parsing is unavailable
# #                         yield json.dumps(
# #                             {"type": "message", "content": event.content}
# #                         ) + "\n"
# #                 elif event.type == "error":
# #                     yield json.dumps({"type": "error", "content": event.error}) + "\n"

# #             # Optionally, handle final completion
# #             final_completion = stream.get_final_completion()
# #             yield json.dumps({"type": "completion", "content": final_completion}) + "\n"

# #     except Exception as e:
# #         # Handle exceptions gracefully
# #         yield json.dumps({"type": "error", "content": str(e)}) + "\n"

# #     # # OpenAI stream-based completion
# #     # try:
# #     #     response = client.chat.completions.create(
# #     #         model=MODEL,
# #     #         messages=[{"role": "system", "content": prompt}],
# #     #         response_format={
# #     #             "type": "json_schema",
# #     #             "json_schema": {
# #     #                 "name": "content",
# #     #                 "schema": {
# #     #                     "type": "object",
# #     #                     "properties": {
# #     #                         "type": {
# #     #                             "type": "string",
# #     #                         },
# #     #                         "role": {
# #     #                             "type": "string",
# #     #                         },
# #     #                         "content": {
# #     #                             "type": "string",
# #     #                         },
# #     #                     },
# #     #                     "required": ["type", "role", "content"],
# #     #                     "additionalProperties": False,
# #     #                 },
# #     #                 "strict": True,
# #     #             },
# #     #         },
# #     #         stream=True,
# #     #     )
# #     #     for chunk in response:
# #     #         print(chunk)
# #     #         print(chunk.choices[0].delta.content)
# #     #         print("****************")
# #     #         yield json.dumps(
# #     #             {
# #     #                 "role": "system",
# #     #                 "type": "message",
# #     #                 "content": chunk.choices[0].delta.content,
# #     #             }
# #     #         ) + "\n"

# #     # except Exception as e:
# #     #     yield json.dumps({"type": "error", "content": str(e)}) + "\n"
