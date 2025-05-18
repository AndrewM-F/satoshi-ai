from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
from loguru import logger

app = FastAPI(
    title="Meet Service",
    description="Handles Google Meet and tl;dv integration",
    version="0.1.0",
)


class Meeting(BaseModel):
    id: str
    title: str
    participants: List[str]
    start_time: str
    end_time: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None


# In-memory storage for demo (replace with database in production)
meetings_db: dict[str, Meeting] = {}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/meetings/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str) -> Meeting:
    if meeting_id not in meetings_db:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meetings_db[meeting_id]


@app.post("/meetings/", response_model=Meeting)
async def create_meeting(meeting: Meeting) -> Meeting:
    meetings_db[meeting.id] = meeting
    logger.info(f"Created meeting: {meeting.id}")
    return meeting


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("meet:app", host="0.0.0.0", port=port, reload=True)
