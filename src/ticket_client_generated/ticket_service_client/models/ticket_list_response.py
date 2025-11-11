from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.ticket_response import TicketResponse


T = TypeVar("T", bound="TicketListResponse")


@_attrs_define
class TicketListResponse:
    """Schema for paginated list of tickets.

    Attributes:
        tickets (list[TicketResponse]): List of tickets
        total (int): Total number of tickets returned
        limit (int): Maximum number of tickets requested
        offset (int): Number of tickets skipped
    """

    tickets: list[TicketResponse]
    total: int
    limit: int
    offset: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        tickets = []
        for tickets_item_data in self.tickets:
            tickets_item = tickets_item_data.to_dict()
            tickets.append(tickets_item)

        total = self.total

        limit = self.limit

        offset = self.offset

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tickets": tickets,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ticket_response import TicketResponse

        d = dict(src_dict)
        tickets = []
        _tickets = d.pop("tickets")
        for tickets_item_data in _tickets:
            tickets_item = TicketResponse.from_dict(tickets_item_data)

            tickets.append(tickets_item)

        total = d.pop("total")

        limit = d.pop("limit")

        offset = d.pop("offset")

        ticket_list_response = cls(
            tickets=tickets,
            total=total,
            limit=limit,
            offset=offset,
        )

        ticket_list_response.additional_properties = d
        return ticket_list_response

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
