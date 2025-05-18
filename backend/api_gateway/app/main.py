from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import httpx
import os
import json
from typing import Dict, Any, List, Union

app = FastAPI(
    title="Satoshi AI API Gateway",
    description="API Gateway for Satoshi AI services",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Service discovery - use localhost for testing
SERVICES = {
    "meet": os.getenv("MEET_SERVICE_URL", "http://localhost:8001"),
    "discord": os.getenv("DISCORD_SERVICE_URL", "http://localhost:8002"),
    "twitter": os.getenv("TWITTER_SERVICE_URL", "http://localhost:8003"),
    "ai": os.getenv("AI_SERVICE_URL", "http://localhost:8004"),
}


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}


# Proxy request handler that supports multiple HTTP methods
@app.api_route(
    "/api/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_request(
    request: Request,
    service_name: str,
    path: str,
) -> Union[Dict[str, Any], List[Any], str]:
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")

    service_url = f"{SERVICES[service_name].rstrip('/')}/{path.lstrip('/')}"

    # Get request body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except json.JSONDecodeError:
            body = await request.body()

    # Forward headers, removing hop-by-hop headers
    headers = {}
    for key, value in request.headers.items():
        if key.lower() not in ["host", "content-length"]:
            headers[key] = value

    try:
        logger.info(f"Proxying request to {service_url} with method {request.method}")
        logger.debug(f"Request headers: {headers}")
        logger.debug(f"Request body: {body}")

        async with httpx.AsyncClient() as client:
            # Forward the request to the target service
            response = await client.request(
                method=request.method,
                url=service_url,
                json=body if body else None,
                params=request.query_params,
                headers=headers,
                timeout=30.0,
            )

            logger.info(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")

            # Handle different response types
            content_type = response.headers.get("content-type", "")

            try:
                if "application/json" in content_type:
                    json_response = response.json()
                    logger.debug(f"JSON response: {json_response}")
                    if not isinstance(json_response, (dict, list)):
                        # Return as string if not a dict or list
                        return str(json_response)
                    return json_response
                # For non-JSON responses, return as string
                response_text = response.text
                logger.debug(f"Non-JSON response: {response_text[:200]}...")
                return response_text
            except Exception as parse_error:
                error_msg = f"Error parsing response: {str(parse_error)}"
                logger.error(f"{error_msg}. Response text: {response.text}")
                raise HTTPException(status_code=500, detail=error_msg)

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling {service_url}: {str(e)}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=(
                e.response.json().get("detail", "Service error")
                if e.response.content
                else "Service error"
            ),
        )
    except Exception as e:
        logger.error(f"Error calling {service_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
