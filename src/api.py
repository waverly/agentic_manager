from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional, List
from . import config
from fastapi.responses import JSONResponse
import json
import os
import sqlite3
import logging
from fastapi.middleware.cors import CORSMiddleware
from .chatbot.coach_tools import (
    get_first_message,
    get_team_updates,
    intent_classification,
    synthesize_updates,
)
from pydantic import BaseModel

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


class PrettyJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            separators=(", ", ": "),
        ).encode("utf-8")


@app.get("/", tags=["General"])
async def root():
    """
    Welcome endpoint with basic API information.
    """
    return {
        "message": "Welcome to the Lattice Manager Agent API. Visit /docs for documentation."
    }


@app.post("/first_message", tags=["FirstMessage"])
async def first_message():
    """
    Handle chat messages and return responses.
    """
    try:
        response = get_first_message()
        print("response", response)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ChatRequest(BaseModel):
    message: str


@app.post("/chat", tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Handle chat messages and return responses.
    """
    try:
        response = intent_classification(request.message)
        print("response", response)
        return response
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/pages", response_class=PrettyJSONResponse, tags=["Pages"])
# def get_pages(db: database.Database = Depends(get_db)):
#     """Get all crawled pages with their link counts."""
#     try:
#         with db.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(
#                 """
#                 SELECT p.id, p.url,
#                     COUNT(l.id) as link_count,
#                     SUM(CASE WHEN l.relevancy >= 0.7 THEN 1 ELSE 0 END) as high_priority_count,
#                     SUM(CASE WHEN l.relevancy >= 0.3 AND l.relevancy < 0.7 THEN 1 ELSE 0 END) as medium_priority_count
#                 FROM pages p
#                 LEFT JOIN links l ON l.source_page_id = p.id
#                 GROUP BY p.id, p.url
#                 ORDER BY p.id DESC
#                 """
#             )
#             rows = cursor.fetchall()
#             pages = []
#             for row in rows:
#                 pages.append(
#                     {
#                         "id": row[0],
#                         "url": row[1],
#                         "total_links": row[2],
#                         "high_priority_links": row[3],
#                         "medium_priority_links": row[4],
#                     }
#                 )
#             return {"pages": pages}
#     except Exception as e:
#         logger.error(f"Error reading database: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")


# @app.get("/pages/{page_id}/links", response_model=List[LinkResponse], tags=["Links"])
# def get_page_links(
#     page_id: int,
#     min_priority: float = Query(
#         0.0, ge=0.0, le=1.0, description="Minimum priority threshold"
#     ),
#     db: database.Database = Depends(get_db),
# ):
#     """Get links found on a specific page."""
#     try:
#         with db.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(
#                 """
#                 SELECT id FROM links
#                 WHERE source_page_id = ? AND relevancy >= ?
#                 ORDER BY relevancy DESC
#                 """,
#                 (page_id, min_priority),
#             )
#             link_ids = [row[0] for row in cursor.fetchall()]

#             # Use get_link to fetch each link with properly formatted keywords
#             results = []
#             for link_id in link_ids:
#                 link = db.get_link(link_id)
#                 if link:
#                     results.append(link)
#             return results
#     except Exception as e:
#         logger.error(f"Error retrieving links for page {page_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")


# # Uncomment and update other endpoints following the same pattern
# # Example: /search endpoint
# @app.get("/search", response_class=PrettyJSONResponse, tags=["Search"])
# def search_links(
#     query: str,
#     min_priority: Optional[float] = Query(
#         None, ge=0.0, le=1.0, description="Minimum relevancy score"
#     ),
#     limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
#     db: database.Database = Depends(get_db),
# ):
#     """Search for links containing the query string."""
#     try:
#         with db.get_connection() as conn:
#             cursor = conn.cursor()

#             sql = """
#                 SELECT
#                     l.id,
#                     l.source_page_id,
#                     p.url as source_url,
#                     l.url,
#                     l.relevancy,
#                     l.relevancy_explanation,
#                     l.high_priority_keywords,
#                     l.medium_priority_keywords,
#                     l.context
#                 FROM links l
#                 JOIN pages p ON p.id = l.source_page_id
#                 WHERE (
#                     l.url LIKE ? OR
#                     l.high_priority_keywords LIKE ? OR
#                     l.medium_priority_keywords LIKE ? OR
#                     l.context LIKE ?
#                 )
#             """

#             parameters = [f"%{query}%" for _ in range(4)]

#             if min_priority is not None:
#                 sql += " AND l.relevancy >= ?"
#                 parameters.append(min_priority)

#             sql += " ORDER BY l.relevancy DESC LIMIT ?"
#             parameters.append(limit)

#             cursor.execute(sql, parameters)

#             rows = cursor.fetchall()
#             links = []
#             for row in rows:
#                 links.append(
#                     {
#                         "id": row[0],
#                         "source_page_id": row[1],
#                         "source_url": row[2],
#                         "url": row[3],
#                         "relevancy": row[4],
#                         "relevancy_explanation": row[5],
#                         "high_priority_keywords": row[6].split(",") if row[6] else [],
#                         "medium_priority_keywords": row[7].split(",") if row[7] else [],
#                         "context": row[8] if row[8] else "(no context)",
#                     }
#                 )

#             return {
#                 "query": query,
#                 "min_priority": min_priority,
#                 "count": len(links),
#                 "links": links,
#             }
#     except Exception as e:
#         logger.error(f"Error searching links with query '{query}': {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")


# @app.get("/links", response_class=PrettyJSONResponse, tags=["Links"])
# def get_links(
#     page: int = Query(1, description="Page number", ge=1),
#     per_page: int = Query(10, description="Items per page", ge=1, le=100),
#     min_relevancy: float = Query(
#         0.0, description="Minimum relevancy score", ge=0.0, le=1.0
#     ),
#     db: database.Database = Depends(get_db),
# ):
#     """Retrieve a paginated list of links."""
#     try:
#         offset = (page - 1) * per_page
#         with db.get_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute(
#                 """
#                 SELECT id, source_page_id, url, link_text, relevancy, relevancy_explanation,
#                        high_priority_keywords, medium_priority_keywords, context
#                 FROM links
#                 WHERE relevancy >= ?
#                 ORDER BY relevancy DESC
#                 LIMIT ? OFFSET ?
#                 """,
#                 (min_relevancy, per_page, offset),
#             )
#             rows = cursor.fetchall()
#             links = []
#             for row in rows:
#                 links.append(
#                     {
#                         "id": row[0],
#                         "source_page_id": row[1],
#                         "url": row[2],
#                         "link_text": row[3],
#                         "relevancy": row[4],
#                         "relevancy_explanation": row[5],
#                         "high_priority_keywords": row[6].split(",") if row[6] else [],
#                         "medium_priority_keywords": row[7].split(",") if row[7] else [],
#                         "context": row[8] if row[8] else "(no context)",
#                     }
#                 )
#             return {
#                 "page": page,
#                 "per_page": per_page,
#                 "min_relevancy": min_relevancy,
#                 "count": len(links),
#                 "links": links,
#             }
#     except Exception as e:
#         logger.error(f"Error retrieving links: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
