from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ticket_priority import TicketPriority
from ..types import UNSET, Unset

T = TypeVar("T", bound="TicketCreateRequest")


@_attrs_define
class TicketCreateRequest:
    """Schema for creating a new ticket.

    Attributes:
        title (str): Brief title describing the ticket
        description (str): Detailed description of the ticket
        reporter (str): Username or email of the person creating the ticket
        priority (TicketPriority | Unset): Enumeration of ticket priority levels.
        assignee (None | str | Unset): Optional username or email to assign the ticket to
    """

    title: str
    description: str
    reporter: str
    priority: TicketPriority | Unset = UNSET
    assignee: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title = self.title

        description = self.description

        reporter = self.reporter

        priority: str | Unset = UNSET
        if not isinstance(self.priority, Unset):
            priority = self.priority.value

        assignee: None | str | Unset
        if isinstance(self.assignee, Unset):
            assignee = UNSET
        else:
            assignee = self.assignee

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
                "description": description,
                "reporter": reporter,
            }
        )
        if priority is not UNSET:
            field_dict["priority"] = priority
        if assignee is not UNSET:
            field_dict["assignee"] = assignee

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        title = d.pop("title")

        description = d.pop("description")

        reporter = d.pop("reporter")

        _priority = d.pop("priority", UNSET)
        priority: TicketPriority | Unset
        if isinstance(_priority, Unset):
            priority = UNSET
        else:
            priority = TicketPriority(_priority)

        def _parse_assignee(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assignee = _parse_assignee(d.pop("assignee", UNSET))

        ticket_create_request = cls(
            title=title,
            description=description,
            reporter=reporter,
            priority=priority,
            assignee=assignee,
        )

        ticket_create_request.additional_properties = d
        return ticket_create_request

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
