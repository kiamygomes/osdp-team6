from enum import Enum


class TicketStatus(str, Enum):
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"
    OPEN = "open"
    RESOLVED = "resolved"

    def __str__(self) -> str:
        return str(self.value)
