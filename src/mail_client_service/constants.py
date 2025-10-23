"""Constants for the mail client service."""

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_204_NO_CONTENT = 204
HTTP_401_UNAUTHORIZED = 401
HTTP_404_NOT_FOUND = 404
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503

# Error Messages
ERROR_SERVICE_INIT_FAILED = "Service initialization failed. Authentication error."
ERROR_FETCH_MESSAGES_FAILED = "Failed to fetch messages."
ERROR_FETCH_MESSAGE_FAILED = "Failed to fetch message."
ERROR_MARK_READ_FAILED = "Failed to mark message as read."
ERROR_DELETE_FAILED = "Failed to delete message."
ERROR_MESSAGE_NOT_FOUND = "Message not found."
ERROR_AUTH_FAILED = "Authentication failed."
ERROR_RATE_LIMIT = "Rate limit exceeded. Please try again later."