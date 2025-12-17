from pathlib import Path
from typing import Any

def load_dotenv(
    dotenv_path: str | Path | None = None,
    **kwargs: Any,
) -> bool: ...
def find_dotenv(filename: str = ".env", **kwargs: Any) -> str: ...
def dotenv_values(
    dotenv_path: str | Path | None = None,
    **kwargs: Any,
) -> dict[str, str | None]: ...
