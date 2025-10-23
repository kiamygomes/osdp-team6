"""Pydantic models for the mail client service API.

This module defines message summary and detail models plus standard response
models (list, success, and error) used throughout the mail client service.
"""

from pydantic import BaseModel, Field


class MessageSummary(BaseModel):
    """Summary information for a message."""

    id: str = Field(..., description="Unique message identifier")
    from_: str = Field(..., alias="from", description="Sender email address")
    to: str | None = Field(None, description="Recipient email address")
    date: str = Field(..., description="Message date")
    subject: str = Field(..., description="Message subject")

    class Config:
        """Pydantic model config to allow population by field names (enables using 'from' alias)."""

        populate_by_name = True


class MessageDetail(BaseModel):
    """Full message details including body content."""

    id: str = Field(..., description="Unique message identifier")
    from_: str = Field(..., alias="from", description="Sender email address")
    to: str = Field(..., description="Recipient email address")
    date: str = Field(..., description="Message date")
    subject: str = Field(..., description="Message subject")
    body: str = Field(..., description="Message body content")

    class Config:
        """Pydantic model config to allow population by field names (enables using 'from' alias)."""

        populate_by_name = True


class MessageListResponse(BaseModel):
    """Response model for message list endpoint."""

    messages: list[MessageSummary] = Field(..., description="List of message summaries")
    count: int = Field(..., description="Number of messages returned")


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Additional error details")
