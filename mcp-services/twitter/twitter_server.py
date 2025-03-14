"""
Twitter (X.com) MCP Server Implementation
---------------------------------------
This server provides MCP-compatible tools for Twitter/X.com integration.
"""

import os
import json
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import tweepy
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("twitter_mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("twitter_mcp")

# Define API models
class TweetData(BaseModel):
    text: str = Field(..., description="Tweet text content")
    media_ids: Optional[List[str]] = Field(None, description="Media IDs to attach to the tweet")
    reply_to: Optional[str] = Field(None, description="Tweet ID to reply to")
    quote_tweet: Optional[str] = Field(None, description="Tweet ID to quote")

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query")
    count: int = Field(10, description="Number of results to return")
    result_type: str = Field("mixed", description="Type of results (mixed, recent, popular)")

class UserLookup(BaseModel):
    username: str = Field(..., description="Twitter username (without @)")

# Create FastAPI app
app = FastAPI(title="Twitter MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twitter client setup
TOKEN_FILE = 'twitter_tokens.json'

def get_twitter_client():
    """Get the Twitter API client."""
    if not os.path.exists(TOKEN_FILE):
        logger.error("Twitter tokens file not found")
        raise HTTPException(
            status_code=500,
            detail="Twitter tokens file not found. Please create a twitter_tokens.json file with your API credentials."
        )
    
    with open(TOKEN_FILE, 'r') as f:
        tokens = json.load(f)
    
    required_keys = ['consumer_key', 'consumer_secret', 'access_token', 'access_token_secret']
    missing_keys = [key for key in required_keys if key not in tokens]
    
    if missing_keys:
        logger.error(f"Missing Twitter API keys: {', '.join(missing_keys)}")
        raise HTTPException(
            status_code=500,
            detail=f"Missing Twitter API keys: {', '.join(missing_keys)}"
        )
    
    auth = tweepy.OAuth1UserHandler(
        tokens['consumer_key'],
        tokens['consumer_secret'],
        tokens['access_token'],
        tokens['access_token_secret']
    )
    
    return tweepy.API(auth)

# MCP Tool Registration
@app.get("/mcp/tools")
async def get_tools():
    """Return the list of tools provided by this MCP server."""
    return {
        "tools": [
            {
                "name": "twitter_post_tweet",
                "description": "Post a new tweet",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Tweet text content"},
                        "media_ids": {"type": "array", "items": {"type": "string"}, "description": "Media IDs to attach to the tweet"},
                        "reply_to": {"type": "string", "description": "Tweet ID to reply to"},
                        "quote_tweet": {"type": "string", "description": "Tweet ID to quote"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "twitter_search",
                "description": "Search for tweets",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "count": {"type": "integer", "description": "Number of results to return"},
                        "result_type": {"type": "string", "description": "Type of results (mixed, recent, popular)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "twitter_get_user_timeline",
                "description": "Get a user's timeline",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Twitter username (without @)"},
                        "count": {"type": "integer", "description": "Number of tweets to return"}
                    },
                    "required": ["username"]
                }
            },
            {
                "name": "twitter_get_user_info",
                "description": "Get information about a Twitter user",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string", "description": "Twitter username (without @)"}
                    },
                    "required": ["username"]
                }
            }
        ]
    }

# Tool implementations
@app.post("/mcp/tools/twitter_post_tweet")
async def post_tweet(tweet_data: TweetData):
    """Post a new tweet."""
    try:
        client = get_twitter_client()
        
        # Prepare tweet parameters
        params = {"status": tweet_data.text}
        
        # Add media IDs if provided
        if tweet_data.media_ids:
            params["media_ids"] = tweet_data.media_ids
        
        # Add in_reply_to_status_id if provided
        if tweet_data.reply_to:
            params["in_reply_to_status_id"] = tweet_data.reply_to
        
        # Handle quote tweet by appending the URL
        if tweet_data.quote_tweet:
            # Get the tweet to quote
            quoted_tweet = client.get_status(tweet_data.quote_tweet)
            quoted_url = f"https://twitter.com/{quoted_tweet.user.screen_name}/status/{quoted_tweet.id}"
            
            # Append the URL to the tweet text
            if len(params["status"] + " " + quoted_url) <= 280:
                params["status"] = params["status"] + " " + quoted_url
            else:
                # Truncate the tweet text to fit the URL
                max_length = 280 - len(" " + quoted_url) - 3  # 3 for "..."
                params["status"] = params["status"][:max_length] + "... " + quoted_url
        
        # Post the tweet
        tweet = client.update_status(**params)
        
        logger.info(f"Tweet posted with ID: {tweet.id}")
        return {
            "status": "success",
            "tweet_id": tweet.id,
            "text": tweet.text,
            "created_at": tweet.created_at.isoformat()
        }
    
    except tweepy.TweepyException as e:
        logger.error(f"Error posting tweet: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error posting tweet: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error posting tweet: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error posting tweet: {str(e)}")

@app.post("/mcp/tools/twitter_search")
async def search_tweets(search_data: SearchQuery):
    """Search for tweets."""
    try:
        client = get_twitter_client()
        
        # Execute search
        tweets = client.search_tweets(
            q=search_data.query,
            count=search_data.count,
            result_type=search_data.result_type,
            tweet_mode="extended"
        )
        
        # Format the response
        results = []
        for tweet in tweets:
            results.append({
                "id": tweet.id,
                "text": tweet.full_text,
                "created_at": tweet.created_at.isoformat(),
                "user": {
                    "id": tweet.user.id,
                    "name": tweet.user.name,
                    "screen_name": tweet.user.screen_name,
                    "profile_image_url": tweet.user.profile_image_url_https
                },
                "retweet_count": tweet.retweet_count,
                "favorite_count": tweet.favorite_count,
                "is_retweet": hasattr(tweet, "retweeted_status"),
                "media": [
                    {
                        "type": media.type,
                        "url": media.media_url_https
                    }
                    for media in tweet.entities.get("media", [])
                ] if hasattr(tweet, "entities") and "media" in tweet.entities else []
            })
        
        logger.info(f"Found {len(results)} tweets matching query: {search_data.query}")
        return {"tweets": results}
    
    except tweepy.TweepyException as e:
        logger.error(f"Error searching tweets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching tweets: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error searching tweets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching tweets: {str(e)}")

@app.post("/mcp/tools/twitter_get_user_timeline")
async def get_user_timeline(user_data: Dict[str, Any]):
    """Get a user's timeline."""
    try:
        username = user_data.get("username")
        count = user_data.get("count", 10)
        
        if not username:
            raise HTTPException(status_code=400, detail="username is required")
        
        client = get_twitter_client()
        
        # Get user timeline
        tweets = client.user_timeline(
            screen_name=username,
            count=count,
            tweet_mode="extended"
        )
        
        # Format the response
        results = []
        for tweet in tweets:
            results.append({
                "id": tweet.id,
                "text": tweet.full_text,
                "created_at": tweet.created_at.isoformat(),
                "retweet_count": tweet.retweet_count,
                "favorite_count": tweet.favorite_count,
                "is_retweet": hasattr(tweet, "retweeted_status"),
                "media": [
                    {
                        "type": media.type,
                        "url": media.media_url_https
                    }
                    for media in tweet.entities.get("media", [])
                ] if hasattr(tweet, "entities") and "media" in tweet.entities else []
            })
        
        logger.info(f"Retrieved {len(results)} tweets from user: {username}")
        return {"tweets": results}
    
    except tweepy.TweepyException as e:
        logger.error(f"Error getting user timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user timeline: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error getting user timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user timeline: {str(e)}")

@app.post("/mcp/tools/twitter_get_user_info")
async def get_user_info(user_data: UserLookup):
    """Get information about a Twitter user."""
    try:
        client = get_twitter_client()
        
        # Get user info
        user = client.get_user(screen_name=user_data.username)
        
        # Format the response
        result = {
            "id": user.id,
            "name": user.name,
            "screen_name": user.screen_name,
            "description": user.description,
            "location": user.location,
            "url": user.url,
            "followers_count": user.followers_count,
            "friends_count": user.friends_count,
            "listed_count": user.listed_count,
            "statuses_count": user.statuses_count,
            "created_at": user.created_at.isoformat(),
            "profile_image_url": user.profile_image_url_https,
            "verified": user.verified
        }
        
        logger.info(f"Retrieved user info for: {user_data.username}")
        return result
    
    except tweepy.TweepyException as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user info: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user info: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
