from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MessageSummary")


@_attrs_define
class MessageSummary:
    """A summary of a message containing only essential information.

    Attributes:
        id (str):
        from_ (Union[None, Unset, str]):
        subject (Union[None, Unset, str]):
        date (Union[None, Unset, str]):
    """

    id: str
    from_: Union[None, Unset, str] = UNSET
    subject: Union[None, Unset, str] = UNSET
    date: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        from_: Union[None, Unset, str]
        if isinstance(self.from_, Unset):
            from_ = UNSET
        else:
            from_ = self.from_

        subject: Union[None, Unset, str]
        if isinstance(self.subject, Unset):
            subject = UNSET
        else:
            subject = self.subject

        date: Union[None, Unset, str]
        if isinstance(self.date, Unset):
            date = UNSET
        else:
            date = self.date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if from_ is not UNSET:
            field_dict["from_"] = from_
        if subject is not UNSET:
            field_dict["subject"] = subject
        if date is not UNSET:
            field_dict["date"] = date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        def _parse_from_(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        from_ = _parse_from_(d.pop("from_", UNSET))

        def _parse_subject(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        subject = _parse_subject(d.pop("subject", UNSET))

        def _parse_date(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        date = _parse_date(d.pop("date", UNSET))

        message_summary = cls(
            id=id,
            from_=from_,
            subject=subject,
            date=date,
        )

        message_summary.additional_properties = d
        return message_summary

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
