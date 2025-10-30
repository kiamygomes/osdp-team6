from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ticket_priority import TicketPriority
from ..models.ticket_status import TicketStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="TicketUpdateRequest")


@_attrs_define
class TicketUpdateRequest:
    """Schema for updating an existing ticket. All fields are optional.

    Attributes:
        title (None | str | Unset): New title for the ticket
        description (None | str | Unset): New description for the ticket
        status (None | TicketStatus | Unset): New status for the ticket
        priority (None | TicketPriority | Unset): New priority level for the ticket
        assignee (None | str | Unset): New assignee for the ticket
    """

    title: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    status: None | TicketStatus | Unset = UNSET
    priority: None | TicketPriority | Unset = UNSET
    assignee: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, TicketStatus):
            status = self.status.value
        else:
            status = self.status

        priority: None | str | Unset
        if isinstance(self.priority, Unset):
            priority = UNSET
        elif isinstance(self.priority, TicketPriority):
            priority = self.priority.value
        else:
            priority = self.priority

        assignee: None | str | Unset
        if isinstance(self.assignee, Unset):
            assignee = UNSET
        else:
            assignee = self.assignee

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if status is not UNSET:
            field_dict["status"] = status
        if priority is not UNSET:
            field_dict["priority"] = priority
        if assignee is not UNSET:
            field_dict["assignee"] = assignee

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_status(data: object) -> None | TicketStatus | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = TicketStatus(data)

                return status_type_0
            except:  # noqa: E722
                pass
            return cast(None | TicketStatus | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_priority(data: object) -> None | TicketPriority | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                priority_type_0 = TicketPriority(data)

                return priority_type_0
            except:  # noqa: E722
                pass
            return cast(None | TicketPriority | Unset, data)

        priority = _parse_priority(d.pop("priority", UNSET))

        def _parse_assignee(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        assignee = _parse_assignee(d.pop("assignee", UNSET))

        ticket_update_request = cls(
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
        )

        ticket_update_request.additional_properties = d
        return ticket_update_request

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
