"""End-to-end happy-path for TicketImpl using respx mocks."""

from uuid import UUID

import httpx
import pytest
import respx

from ticket_api import TicketPriority, TicketStatus
from ticket_impl import TicketImpl

BASE = "https://api.atlassian.com/ex/jira/00000000-0000-0000-0000-000000000000/rest/api/3"
EXPECTED_GET_CALLS = 3  # replace magic number '3'


@pytest.mark.asyncio
@respx.mock  # type: ignore[misc]
async def test_create_get_list_update_comment_delete(seed_token: None) -> None:
    """End-to-end happy-path for TicketImpl using respx mocks."""
    # user lookup
    respx.get(f"{BASE}/user/search").mock(
        return_value=httpx.Response(200, json=[{"accountId": "acc-1", "displayName": "Terra"}]),
    )
    # create issue
    respx.post(f"{BASE}/issue").mock(
        return_value=httpx.Response(201, json={"id": "10001", "key": "OSDP-101"}),
    )

    def issue_payload(  # noqa: PLR0913
        summary: str = "Hello HW2",
        status: str = "Open",
        priority: str = "High",
        description: str = "Created from impl",
        assignee: str = "Terra",
        reporter: str = "Terra",
    ) -> dict[str, object]:
        return {
            "id": "10001",
            "key": "OSDP-101",
            "fields": {
                "summary": summary,
                "status": {"name": status},
                "priority": {"name": priority},
                "description": description,
                "assignee": {"displayName": assignee} if assignee else None,
                "reporter": {"displayName": reporter} if reporter else None,
            },
        }

    # SINGLE GET route with THREE sequential responses (create -> get -> after update)
    route_issue = respx.get(f"{BASE}/issue/OSDP-101")
    route_issue.mock(
        side_effect=[
            httpx.Response(200, json=issue_payload()),  # 1) after create_ticket()
            httpx.Response(200, json=issue_payload()),  # 2) get_ticket() in the test
            httpx.Response(200, json=issue_payload(summary="Renamed", status="In Progress", priority="High")),  # 3) after update
        ],
    )

    # update & transitions
    respx.put(f"{BASE}/issue/OSDP-101").mock(return_value=httpx.Response(200, json={}))
    respx.get(f"{BASE}/issue/OSDP-101/transitions").mock(
        return_value=httpx.Response(
            200,
            json={
                "transitions": [{"id": "3", "name": "In Progress"}, {"id": "31", "name": "Done"}],
            },
        ),
    )
    respx.post(f"{BASE}/issue/OSDP-101/transitions").mock(return_value=httpx.Response(204))

    # search/list
    respx.post(f"{BASE}/search").mock(
        return_value=httpx.Response(200, json={"issues": [issue_payload()]}),
    )

    # comments
    respx.post(f"{BASE}/issue/OSDP-101/comment").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "c-1",
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Ship it."}]}],
                },
                "author": {"displayName": "Terra"},
            },
        ),
    )
    respx.get(f"{BASE}/issue/OSDP-101/comment").mock(
        return_value=httpx.Response(
            200,
            json={
                "comments": [
                    {
                        "id": "c-1",
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Ship it."}]}],
                        },
                        "author": {"displayName": "Terra"},
                    },
                ],
            },
        ),
    )

    # delete
    respx.delete(f"{BASE}/issue/OSDP-101").mock(return_value=httpx.Response(204))

    # exercise
    svc = TicketImpl(user_id="u1", project_key="OSDP")

    t = await svc.create_ticket(
        title="Hello HW2",
        description="Created from impl",
        reporter="terra@nyu.edu",
        priority=TicketPriority.HIGH,
        assignee="teammate@nyu.edu",
    )
    assert t.title == "Hello HW2"
    assert t.priority == TicketPriority.HIGH
    assert isinstance(t.id, UUID)

    one = await svc.get_ticket(t.id)
    assert one is not None
    assert one.title == "Hello HW2"
    assert one.status == TicketStatus.OPEN

    lst = await svc.list_tickets(limit=5)
    assert len(lst) >= 1

    upd = await svc.update_ticket(t.id, title="Renamed", status=TicketStatus.IN_PROGRESS)
    assert upd is not None
    assert upd.title == "Renamed"
    assert upd.status == TicketStatus.IN_PROGRESS
    assert upd.priority == TicketPriority.HIGH

    c = await svc.add_comment(t.id, author="terra@nyu.edu", content="Ship it.")
    assert c is not None
    assert "Ship it." in c.content
    cl = await svc.get_ticket_comments(t.id)
    assert cl
    assert "Ship it." in cl[0].content

    ok = await svc.delete_ticket(t.id)
    assert ok is True

    assert route_issue.call_count == EXPECTED_GET_CALLS
