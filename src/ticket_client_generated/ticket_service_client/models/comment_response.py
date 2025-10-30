from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="CommentResponse")


@_attrs_define
class CommentResponse:
    """Schema for a comment in API responses.

    Attributes:
        id (UUID): Unique identifier for the comment
        ticket_id (UUID): ID of the ticket this comment belongs to
        author (str): Author of the comment
        content (str): Comment text content
        created_at (datetime.datetime): When the comment was created
    """

    id: UUID
    ticket_id: UUID
    author: str
    content: str
    created_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        ticket_id = str(self.ticket_id)

        author = self.author

        content = self.content

        created_at = self.created_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "ticket_id": ticket_id,
                "author": author,
                "content": content,
                "created_at": created_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        ticket_id = UUID(d.pop("ticket_id"))

        author = d.pop("author")

        content = d.pop("content")

        created_at = isoparse(d.pop("created_at"))

        comment_response = cls(
            id=id,
            ticket_id=ticket_id,
            author=author,
            content=content,
            created_at=created_at,
        )

        comment_response.additional_properties = d
        return comment_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
