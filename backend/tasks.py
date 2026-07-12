"""
FastAPI Task Endpoints — Tasks Management App
Fixes all bugs from the starter code and adds production-ready patterns.
"""

from __future__ import annotations

import mimetypes
import os
import uuid
from typing import Annotated

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from anthropic import Anthropic
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from auth import CurrentUser, get_current_user   # re-use the auth module

# ---------------------------------------------------------------------------
# App & clients
# ---------------------------------------------------------------------------

app = FastAPI(title="Tasks Management API — Tasks Module")

anthropic = Anthropic()  # reads ANTHROPIC_API_KEY from env automatically

S3_BUCKET: str = os.environ.get("S3_BUCKET", "")
AWS_REGION: str = os.environ.get("AWS_REGION", "us-east-1")
if not S3_BUCKET:
    raise RuntimeError("S3_BUCKET environment variable is not set")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class TaskCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    priority: str = Field("normal", pattern="^(urgent|normal|low)$")
    deadline: str | None = None   # ISO-8601 string; parse to datetime in the DB layer


class TaskResponse(BaseModel):
    id: str
    user_id: str
    text: str
    priority: str
    ai_extracted: bool
    photo_url: str | None = None


# ---------------------------------------------------------------------------
# S3 helper
# ---------------------------------------------------------------------------

def upload_to_s3(image_bytes: bytes, filename: str) -> str:
    """
    Upload *image_bytes* to S3 and return the public HTTPS URL.

    BUGS FIXED:
    - `s3.upload_object` does not exist → correct method is `put_object`
    - filename collisions: prefix with a UUID so two users can upload
      "photo.jpg" without overwriting each other
    - Credentials come from the environment / IAM role, not hardcoded
    """
    safe_name = f"{uuid.uuid4()}/{filename}"
    content_type, _ = mimetypes.guess_type(filename)
    content_type = content_type or "application/octet-stream"

    s3 = boto3.client("s3", region_name=AWS_REGION)
    try:
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=safe_name,
            Body=image_bytes,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"S3 upload failed: {exc}",
        )

    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{safe_name}"


# ---------------------------------------------------------------------------
# AI helpers — Claude instead of GPT-4, with vision support
# ---------------------------------------------------------------------------

def extract_text_from_image(image_bytes: bytes, media_type: str) -> str:
    """
    Send the raw image bytes to Claude's vision API and return extracted
    to-do text.

    BUGS FIXED (original):
    - Passed a URL string in the text content instead of using the vision API;
      GPT-4 (and Claude) vision requires the image sent as base64 or a URL in
      an image content block — a plain string URL is treated as text and the
      model just reads the URL, not the image.
    - response.choices.message.content → wrong attribute chain;
      correct path is response.choices[0].message.content (OpenAI) or
      response.content[0].text (Anthropic).

    SWITCHED TO CLAUDE:
    - Uses claude-sonnet-4-6 with a base64 image block (no public URL needed,
      works for private S3 objects too).
    """
    import base64
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    response = anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extract all to-do items or task text visible in this image. "
                            "Return only the extracted task text, no commentary."
                        ),
                    },
                ],
            }
        ],
    )
    # BUG FIXED: response.choices.message.content (OpenAI misuse)
    # Correct Anthropic path:
    return response.content[0].text.strip()


def categorize_priority(text: str) -> str:
    """
    Ask Claude to classify task urgency.

    BUG FIXED: response.choices.message.content — wrong attribute chain.
    Also added an explicit system prompt so the model returns exactly one
    word instead of a sentence like "The priority is urgent."
    """
    response = anthropic.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10,
        system=(
            "You are a task prioritization assistant. "
            "Respond with exactly one word: urgent, normal, or low."
        ),
        messages=[
            {
                "role": "user",
                "content": f"What is the priority of this task?\n\n{text}",
            }
        ],
    )
    # BUG FIXED: response.choices.message.content
    priority = response.content[0].text.strip().lower()
    return priority if priority in {"urgent", "normal", "low"} else "normal"


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------

@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task manually",
)
async def create_task(
    body: TaskCreateRequest,
    current_user: CurrentUser,
) -> TaskResponse:
    """
    BUG FIXED: credentials were taken as a raw `token: str` query parameter
    (exposes JWT in server logs). Re-uses the `CurrentUser` dependency from
    auth.py which reads the Bearer header and validates the JWT.

    BUG FIXED: `text` and `priority` were query params — task content belongs
    in the request body.
    """
    task = database.create_task(
        user_id=current_user["sub"],
        text=body.text,
        priority=body.priority,
        deadline=body.deadline,
    )
    return TaskResponse(**task)


@app.post(
    "/tasks/upload",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task by uploading an image (AI extracts text)",
)
async def upload_task(
    current_user: CurrentUser,
    image: UploadFile = File(...),  # BUG FIXED: File() → File(...) marks it required
) -> TaskResponse:
    """
    Full pipeline: validate → S3 → Claude vision → priority → DB.
    """
    # --- Validate MIME type ---
    mime = image.content_type or ""
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{mime}'. Allowed: {ALLOWED_MIME_TYPES}",
        )

    # --- Read & size-check ---
    image_bytes = await image.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {MAX_IMAGE_BYTES // (1024*1024)} MB limit",
        )

    # --- S3 upload ---
    photo_url = upload_to_s3(image_bytes, image.filename or "upload.jpg")

    # --- AI pipeline ---
    # Pass raw bytes to Claude — no need for a public URL
    ai_text   = extract_text_from_image(image_bytes, mime)
    priority  = categorize_priority(ai_text)

    # --- Persist ---
    task = database.create_task(
        user_id=current_user["sub"],
        text=ai_text,
        priority=priority,
        photo_url=photo_url,
        ai_extracted=True,
    )
    return TaskResponse(**task)
# Add to the imports at the top of tasks.py
from database import SessionLocal
from models import Task