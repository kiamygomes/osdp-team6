from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.ticket_priority import TicketPriority
from ..models.ticket_status import TicketStatus

T = TypeVar("T", bound="TicketResponse")


@_attrs_define
class TicketResponse:
    """Schema for a ticket in API responses.

    Attributes:
        id (UUID): Unique identifier for the ticket
        title (str): Ticket title
        description (str): Ticket description
        status (TicketStatus): Enumeration of possible ticket statuses.
        priority (TicketPriority): Enumeration of ticket priority levels.
        reporter (str): Person who created the ticket
        assignee (None | str): Person assigned to the ticket
        created_at (datetime.datetime): When the ticket was created
        updated_at (datetime.datetime): When the ticket was last updated
    """

    id: UUID
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    reporter: str
    assignee: None | str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        title = self.title

        description = self.description

        status = self.status.value

        priority = self.priority.value

        reporter = self.reporter

        assignee: None | str
        assignee = self.assignee

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "description": description,
                "status": status,
                "priority": priority,
                "reporter": reporter,
                "assignee": assignee,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        title = d.pop("title")

        description = d.pop("description")

        status = TicketStatus(d.pop("status"))

        priority = TicketPriority(d.pop("priority"))

        reporter = d.pop("reporter")

        def _parse_assignee(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        assignee = _parse_assignee(d.pop("assignee"))

        created_at = isoparse(d.pop("created_at"))

        updated_at = isoparse(d.pop("updated_at"))

        ticket_response = cls(
            id=id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            reporter=reporter,
            assignee=assignee,
            created_at=created_at,
            updated_at=updated_at,
        )

        ticket_response.additional_properties = d
        return ticket_response

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
