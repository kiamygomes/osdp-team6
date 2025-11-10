"""End-to-end happy-path for TicketImpl using respx mocks."""

from uuid import UUID

import httpx
import pytest
import respx
from ticket_api.models import TicketPriority, TicketStatus

from ticket_impl import TicketImpl

BASE = "https://api.atlassian.com/ex/jira/00000000-0000-0000-0000-000000000000/rest/api/3"
EXPECTED_GET_CALLS = 3  # after create, explicit get, and after status transition


@pytest.mark.asyncio
@respx.mock
async def test_create_get_list_transition_comment_delete(seed_token: None) -> None:
    """End-to-end happy-path for TicketImpl using respx mocks."""
    # user lookup (used for reporter/assignee mapping)
    respx.get(f"{BASE}/user/search").mock(
        return_value=httpx.Response(200, json=[{"accountId": "acc-1", "displayName": "Terra"}]),
    )
    # create issue
    respx.post(f"{BASE}/issue").mock(
        return_value=httpx.Response(201, json={"id": "10001", "key": "OSDP-101"}),
    )

    def issue_payload(
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

    # SINGLE GET route with THREE sequential responses:
    # 1) after create_ticket()  2) explicit get_ticket()  3) after transition_status()
    route_issue = respx.get(f"{BASE}/issue/OSDP-101")
    route_issue.mock(
        side_effect=[
            httpx.Response(200, json=issue_payload()),  # 1) after create_ticket()
            httpx.Response(200, json=issue_payload()),  # 2) get_ticket() in the test
            httpx.Response(200, json=issue_payload(status="In Progress", priority="High")),  # 3) after transition
        ],
    )

    # update fields & transitions
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
    assert one.title == "Hello HW2"
    assert one.status == TicketStatus.OPEN

    lst = await svc.list_tickets(limit=5)
    assert len(lst) >= 1

    # NEW granular update: transition status (no title change in the new API)
    upd = await svc.transition_status(t.id, TicketStatus.IN_PROGRESS)
    assert upd.title == "Hello HW2"  # unchanged title
    assert upd.status == TicketStatus.IN_PROGRESS
    assert upd.priority == TicketPriority.HIGH

    c = await svc.add_comment(t.id, author="terra@nyu.edu", content="Ship it.")
    assert "Ship it." in c.content
    cl = await svc.get_ticket_comments(t.id)
    assert cl
    assert "Ship it." in cl[0].content

    ok = await svc.delete_ticket(t.id)
    assert ok is True

    # ensure we hit GET three times as planned
    assert route_issue.call_count == EXPECTED_GET_CALLS
