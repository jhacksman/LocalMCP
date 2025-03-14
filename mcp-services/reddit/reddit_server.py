"""
Reddit MCP Server Implementation
------------------------------
This server provides MCP-compatible tools for Reddit integration.
"""

import os
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import praw
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("reddit_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("reddit_mcp")

# Define API models
class SubredditData(BaseModel):
    subreddit: str = Field(..., description="Subreddit name (without r/)")
    limit: int = Field(10, description="Number of posts to retrieve")
    time_filter: str = Field("day", description="Time filter for top posts (hour, day, week, month, year, all)")

class PostData(BaseModel):
    subreddit: str = Field(..., description="Subreddit name (without r/)")
    title: str = Field(..., description="Post title")
    content: str = Field(..., description="Post content")
    kind: str = Field("self", description="Post type (self, link, image)")
    url: Optional[str] = Field(None, description="URL for link posts")
    image_path: Optional[str] = Field(None, description="Path to image for image posts")

class CommentData(BaseModel):
    post_id: str = Field(..., description="Reddit post ID")
    body: str = Field(..., description="Comment body")
    parent_id: Optional[str] = Field(None, description="Parent comment ID for replies")

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query")
    subreddit: Optional[str] = Field(None, description="Limit search to a specific subreddit")
    sort: str = Field("relevance", description="Sort method (relevance, hot, top, new, comments)")
    time_filter: str = Field("all", description="Time filter (hour, day, week, month, year, all)")
    limit: int = Field(10, description="Number of results to return")

# Create FastAPI app
app = FastAPI(title="Reddit MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Reddit client setup
CREDENTIALS_FILE = 'reddit_credentials.json'

def get_reddit_client():
    """Get the Reddit API client."""
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error("Reddit credentials file not found")
        raise HTTPException(
            status_code=500,
            detail="Reddit credentials file not found. Please create a reddit_credentials.json file with your API credentials."
        )
    
    with open(CREDENTIALS_FILE, 'r') as f:
        creds = json.load(f)
    
    required_keys = ['client_id', 'client_secret', 'user_agent', 'username', 'password']
    missing_keys = [key for key in required_keys if key not in creds]
    
    if missing_keys:
        logger.error(f"Missing Reddit API credentials: {', '.join(missing_keys)}")
        raise HTTPException(
            status_code=500,
            detail=f"Missing Reddit API credentials: {', '.join(missing_keys)}"
        )
    
    return praw.Reddit(
        client_id=creds['client_id'],
        client_secret=creds['client_secret'],
        user_agent=creds['user_agent'],
        username=creds['username'],
        password=creds['password']
    )

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "reddit_get_hot_posts",
                "description": "Get hot posts from a subreddit",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subreddit": {"type": "string", "description": "Subreddit name (without r/)"},
                        "limit": {"type": "integer", "description": "Number of posts to retrieve"}
                    },
                    "required": ["subreddit"]
                }
            },
            {
                "name": "reddit_get_top_posts",
                "description": "Get top posts from a subreddit",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subreddit": {"type": "string", "description": "Subreddit name (without r/)"},
                        "limit": {"type": "integer", "description": "Number of posts to retrieve"},
                        "time_filter": {"type": "string", "description": "Time filter (hour, day, week, month, year, all)"}
                    },
                    "required": ["subreddit"]
                }
            },
            {
                "name": "reddit_get_post_details",
                "description": "Get details of a specific Reddit post",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "Reddit post ID"}
                    },
                    "required": ["post_id"]
                }
            },
            {
                "name": "reddit_get_post_comments",
                "description": "Get comments from a Reddit post",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "Reddit post ID"},
                        "limit": {"type": "integer", "description": "Number of comments to retrieve"},
                        "sort": {"type": "string", "description": "Sort method (top, new, controversial, old, qa)"}
                    },
                    "required": ["post_id"]
                }
            },
            {
                "name": "reddit_submit_post",
                "description": "Submit a new post to a subreddit",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "subreddit": {"type": "string", "description": "Subreddit name (without r/)"},
                        "title": {"type": "string", "description": "Post title"},
                        "content": {"type": "string", "description": "Post content"},
                        "kind": {"type": "string", "description": "Post type (self, link, image)"},
                        "url": {"type": "string", "description": "URL for link posts"},
                        "image_path": {"type": "string", "description": "Path to image for image posts"}
                    },
                    "required": ["subreddit", "title", "content", "kind"]
                }
            },
            {
                "name": "reddit_submit_comment",
                "description": "Submit a comment on a post or reply to another comment",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "post_id": {"type": "string", "description": "Reddit post ID"},
                        "body": {"type": "string", "description": "Comment body"},
                        "parent_id": {"type": "string", "description": "Parent comment ID for replies"}
                    },
                    "required": ["post_id", "body"]
                }
            },
            {
                "name": "reddit_search",
                "description": "Search Reddit for posts",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "subreddit": {"type": "string", "description": "Limit search to a specific subreddit"},
                        "sort": {"type": "string", "description": "Sort method (relevance, hot, top, new, comments)"},
                        "time_filter": {"type": "string", "description": "Time filter (hour, day, week, month, year, all)"},
                        "limit": {"type": "integer", "description": "Number of results to return"}
                    },
                    "required": ["query"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/reddit_get_hot_posts")
async def get_hot_posts(subreddit_data: Dict[str, Any]):
    """Get hot posts from a subreddit."""
    try:
        subreddit_name = subreddit_data.get("subreddit")
        limit = subreddit_data.get("limit", 10)
        
        if not subreddit_name:
            raise HTTPException(status_code=400, detail="subreddit is required")
        
        reddit = get_reddit_client()
        
        # Get the subreddit
        subreddit = reddit.subreddit(subreddit_name)
        
        # Get hot posts
        posts = []
        for post in subreddit.hot(limit=limit):
            posts.append({
                "id": post.id,
                "title": post.title,
                "author": post.author.name if post.author else "[deleted]",
                "created_utc": post.created_utc,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "permalink": post.permalink,
                "url": post.url,
                "is_self": post.is_self,
                "selftext": post.selftext if post.is_self else None,
                "subreddit": post.subreddit.display_name
            })
        
        logger.info(f"Retrieved {len(posts)} hot posts from r/{subreddit_name}")
        return {"posts": posts}
    
    except Exception as e:
        logger.error(f"Error getting hot posts: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error getting hot posts: {str(e)}")

@app.post("/mcp/tools/reddit_get_top_posts")
async def get_top_posts(subreddit_data: SubredditData):
    """Get top posts from a subreddit."""
    try:
        reddit = get_reddit_client()
        
        # Get the subreddit
        subreddit = reddit.subreddit(subreddit_data.subreddit)
        
        # Get top posts
        posts = []
        for post in subreddit.top(time_filter=subreddit_data.time_filter, limit=subreddit_data.limit):
            posts.append({
                "id": post.id,
                "title": post.title,
                "author": post.author.name if post.author else "[deleted]",
                "created_utc": post.created_utc,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "permalink": post.permalink,
                "url": post.url,
                "is_self": post.is_self,
                "selftext": post.selftext if post.is_self else None,
                "subreddit": post.subreddit.display_name
            })
        
        logger.info(f"Retrieved {len(posts)} top posts from r/{subreddit_data.subreddit}")
        return {"posts": posts}
    
    except Exception as e:
        logger.error(f"Error getting top posts: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error getting top posts: {str(e)}")

@app.post("/mcp/tools/reddit_get_post_details")
async def get_post_details(post_data: Dict[str, str]):
    """Get details of a specific Reddit post."""
    try:
        post_id = post_data.get("post_id")
        
        if not post_id:
            raise HTTPException(status_code=400, detail="post_id is required")
        
        reddit = get_reddit_client()
        
        # Get the post
        post = reddit.submission(id=post_id)
        
        # Format the response
        post_details = {
            "id": post.id,
            "title": post.title,
            "author": post.author.name if post.author else "[deleted]",
            "created_utc": post.created_utc,
            "score": post.score,
            "upvote_ratio": post.upvote_ratio,
            "num_comments": post.num_comments,
            "permalink": post.permalink,
            "url": post.url,
            "is_self": post.is_self,
            "selftext": post.selftext if post.is_self else None,
            "subreddit": post.subreddit.display_name
        }
        
        logger.info(f"Retrieved details for post {post_id}")
        return post_details
    
    except Exception as e:
        logger.error(f"Error getting post details: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error getting post details: {str(e)}")

@app.post("/mcp/tools/reddit_get_post_comments")
async def get_post_comments(comment_data: Dict[str, Any]):
    """Get comments from a Reddit post."""
    try:
        post_id = comment_data.get("post_id")
        limit = comment_data.get("limit", 10)
        sort = comment_data.get("sort", "top")
        
        if not post_id:
            raise HTTPException(status_code=400, detail="post_id is required")
        
        reddit = get_reddit_client()
        
        # Get the post
        post = reddit.submission(id=post_id)
        
        # Set comment sort
        post.comment_sort = sort
        
        # Replace MoreComments objects with actual comments
        post.comments.replace_more(limit=0)
        
        # Get comments
        comments = []
        for comment in post.comments.list()[:limit]:
            comments.append({
                "id": comment.id,
                "author": comment.author.name if comment.author else "[deleted]",
                "body": comment.body,
                "created_utc": comment.created_utc,
                "score": comment.score,
                "permalink": comment.permalink,
                "is_submitter": comment.is_submitter,
                "parent_id": comment.parent_id,
                "depth": comment.depth
            })
        
        logger.info(f"Retrieved {len(comments)} comments from post {post_id}")
        return {"comments": comments}
    
    except Exception as e:
        logger.error(f"Error getting post comments: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error getting post comments: {str(e)}")

@app.post("/mcp/tools/reddit_submit_post")
async def submit_post(post_data: PostData):
    """Submit a new post to a subreddit."""
    try:
        reddit = get_reddit_client()
        
        # Get the subreddit
        subreddit = reddit.subreddit(post_data.subreddit)
        
        # Submit the post based on its kind
        if post_data.kind == "self":
            # Text post
            submission = subreddit.submit(
                title=post_data.title,
                selftext=post_data.content
            )
        elif post_data.kind == "link":
            # Link post
            if not post_data.url:
                raise HTTPException(status_code=400, detail="url is required for link posts")
            
            submission = subreddit.submit(
                title=post_data.title,
                url=post_data.url
            )
        elif post_data.kind == "image":
            # Image post
            if not post_data.image_path:
                raise HTTPException(status_code=400, detail="image_path is required for image posts")
            
            if not os.path.exists(post_data.image_path):
                raise HTTPException(status_code=400, detail=f"Image file not found: {post_data.image_path}")
            
            submission = subreddit.submit_image(
                title=post_data.title,
                image_path=post_data.image_path
            )
        else:
            raise HTTPException(status_code=400, detail=f"Invalid post kind: {post_data.kind}")
        
        logger.info(f"Submitted post to r/{post_data.subreddit}: {submission.id}")
        return {
            "status": "success",
            "post_id": submission.id,
            "permalink": submission.permalink,
            "url": submission.url
        }
    
    except Exception as e:
        logger.error(f"Error submitting post: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error submitting post: {str(e)}")

@app.post("/mcp/tools/reddit_submit_comment")
async def submit_comment(comment_data: CommentData):
    """Submit a comment on a post or reply to another comment."""
    try:
        reddit = get_reddit_client()
        
        # Determine if this is a top-level comment or a reply
        if comment_data.parent_id:
            # Reply to a comment
            parent = reddit.comment(id=comment_data.parent_id)
            comment = parent.reply(body=comment_data.body)
        else:
            # Top-level comment on a post
            post = reddit.submission(id=comment_data.post_id)
            comment = post.reply(body=comment_data.body)
        
        logger.info(f"Submitted comment: {comment.id}")
        return {
            "status": "success",
            "comment_id": comment.id,
            "permalink": comment.permalink
        }
    
    except Exception as e:
        logger.error(f"Error submitting comment: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error submitting comment: {str(e)}")

@app.post("/mcp/tools/reddit_search")
async def search_reddit(search_data: SearchQuery):
    """Search Reddit for posts."""
    try:
        reddit = get_reddit_client()
        
        # Determine search scope
        if search_data.subreddit:
            # Search within a specific subreddit
            subreddit = reddit.subreddit(search_data.subreddit)
            search_results = subreddit.search(
                query=search_data.query,
                sort=search_data.sort,
                time_filter=search_data.time_filter,
                limit=search_data.limit
            )
        else:
            # Search all of Reddit
            search_results = reddit.subreddit("all").search(
                query=search_data.query,
                sort=search_data.sort,
                time_filter=search_data.time_filter,
                limit=search_data.limit
            )
        
        # Format the results
        results = []
        for post in search_results:
            results.append({
                "id": post.id,
                "title": post.title,
                "author": post.author.name if post.author else "[deleted]",
                "created_utc": post.created_utc,
                "score": post.score,
                "upvote_ratio": post.upvote_ratio,
                "num_comments": post.num_comments,
                "permalink": post.permalink,
                "url": post.url,
                "is_self": post.is_self,
                "selftext": post.selftext if post.is_self else None,
                "subreddit": post.subreddit.display_name
            })
        
        logger.info(f"Found {len(results)} posts matching query: {search_data.query}")
        return {"posts": results}
    
    except Exception as e:
        logger.error(f"Error searching Reddit: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error searching Reddit: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
