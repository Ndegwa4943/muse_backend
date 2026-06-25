import httrtpx
import json
import re
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

# Rate limiting: 1 request per 3 seconds per domain
REQUEST_DELAY_SECONDS = 3
MAX_RETRIES = 2
TIMEOUT_SECONDS = 10

# Track last request time to enforce rate limiting
_last_request_time: Dict[str, datetime] = {}


async def _enforce_rate_limit(domain: str = "pinterest.com") -> None:
    """
    Polite rate limiting: ensure we don't hammer Pinterest's servers.
    Single-request per 3 seconds per domain.
    """
    global _last_request_time
    
    if domain in _last_request_time:
        elapsed = (datetime.now() - _last_request_time[domain]).total_seconds()
        if elapsed < REQUEST_DELAY_SECONDS:
            await asyncio.sleep(REQUEST_DELAY_SECONDS - elapsed)
    
    _last_request_time[domain] = datetime.now()


def _build_headers() -> Dict[str, str]:
    """
    Realistic browser headers to avoid immediate blocking.
    Identify as a user agent, not a bot.
    """
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://www.pinterest.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }


def _extract_pws_data(html: str) -> Optional[Dict[str, Any]]:
    """
    Surgically extract the __PWS_DATA__ JSON payload from raw HTML.
    Returns None if not found or malformed.
    """
    match = re.search(
        r'<script id="__PWS_DATA__" type="application/json">(.*?)</script>',
        html,
        re.DOTALL
    )
    
    if not match:
        return None
    
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _parse_metadata(pws_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Pinterest's __PWS_DATA__ structure to standard metadata fields.
    Gracefully handles missing fields.
    """
    try:
        # Navigate the nested structure—adjust based on actual Pinterest schema
        data = pws_data.get("initialReduxState", {})
        
        # Example navigation (adjust to match real Pinterest structure)
        pin_data = data.get("pins", {})
        user_data = data.get("users", {})
        
        # Extract what we can, fallback to None if missing
        return {
            "title": pin_data.get("title", "Untitled"),
            "description": pin_data.get("description", ""),
            "author": user_data.get("username", "Unknown"),
            "image_url": pin_data.get("images", {}).get("orig", {}).get("url", None),
            "created_at": pin_data.get("created_at", None),
            "url": pin_data.get("link", ""),
        }
    except (KeyError, TypeError) as e:
        # If schema doesn't match, return what we can
        return {
            "title": "Unable to parse metadata",
            "description": str(e),
            "author": None,
            "image_url": None,
        }


async def extract_pinterest_metadata(
    url: str,
    timeout: int = TIMEOUT_SECONDS,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    Politely fetch and extract Pinterest metadata for a single URL.
    
    Args:
        url: The Pinterest URL to extract metadata from
        timeout: Request timeout in seconds
        retry_count: Internal retry counter (don't set manually)
    
    Returns:
        Dictionary with extracted metadata or error info
    """
    
    # Enforce rate limiting
    await _enforce_rate_limit("pinterest.com")
    
    headers = _build_headers()
    
    try:
        # Use httpx with reasonable defaults
        async with httpx.AsyncClient(
            http2=True,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        ) as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            
            # Extract the React hydration payload
            pws_data = _extract_pws_data(response.text)
            
            if not pws_data:
                return {
                    "error": "Hydration script not found",
                    "status": "not_found",
                    "message": "Pinterest may have blocked the request, changed their DOM structure, or this URL is not publicly accessible."
                }
            
            # Parse into standard metadata format
            metadata = _parse_metadata(pws_data)
            metadata["status"] = "success"
            metadata["fetched_at"] = datetime.now().isoformat()
            
            return metadata
    
    except httpx.HTTPStatusError as e:
        # Handle specific HTTP errors gracefully
        if e.response.status_code == 429:
            # Rate limited
            if retry_count < MAX_RETRIES:
                # Back off and retry
                await asyncio.sleep(10 * (retry_count + 1))
                return await extract_pinterest_metadata(url, timeout, retry_count + 1)
            return {
                "error": "Rate limited",
                "status": "rate_limited",
                "message": "Pinterest rate-limited this request. Please try again later."
            }
        
        elif e.response.status_code == 403:
            return {
                "error": "Access forbidden",
                "status": "forbidden",
                "message": "Pinterest blocked this request. Your IP or session may be flagged."
            }
        
        elif e.response.status_code == 404:
            return {
                "error": "URL not found",
                "status": "not_found",
                "message": "This Pinterest URL does not exist or is not publicly accessible."
            }
        
        else:
            return {
                "error": f"HTTP {e.response.status_code}",
                "status": "http_error",
                "message": str(e)
            }
    
    except httpx.TimeoutException:
        return {
            "error": "Request timeout",
            "status": "timeout",
            "message": f"Pinterest took longer than {timeout} seconds to respond."
        }
    
    except httpx.NetworkError as e:
        return {
            "error": "Network error",
            "status": "network_error",
            "message": str(e)
        }
    
    except Exception as e:
        return {
            "error": "Unknown error",
            "status": "unknown",
            "message": str(e)
        }


# Example usage for FastAPI
async def fetch_bookmark_preview(user_url: str) -> Dict[str, Any]:
    """
    Called from your FastAPI endpoint when a user pastes a URL.
    """
    result = await extract_pinterest_metadata(user_url)
    return result