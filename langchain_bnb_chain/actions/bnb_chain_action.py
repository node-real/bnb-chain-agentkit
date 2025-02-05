from collections.abc import Callable, Coroutine
from typing import Any, Optional

from pydantic import BaseModel


class BnbChainAction(BaseModel):
    """BNB Chain Action Base Class."""

    name: str
    description: str
    args_schema: Optional[type[BaseModel]] = None
    func: Optional[Callable[..., str]] = None
    async_func: Optional[Callable[..., Coroutine[Any, Any, str]]] = None
