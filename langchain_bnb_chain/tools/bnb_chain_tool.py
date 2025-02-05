"""Tool allows agents to interact with the BNB Chain API.

To use this tool, you must first set environment variables:
    PRIVATE_KEY
    BSC_PROVIDER_URL    
    OPBNB_PROVIDER_URL
"""

from collections.abc import Callable, Coroutine
from typing import Any, Optional

from langchain_core.callbacks import AsyncCallbackManagerForToolRun, CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from langchain_bnb_chain.utils.bnb_chain_api_wrapper import BnbChainAPIWrapper


class BnbChainTool(BaseTool):  # type: ignore[override]
    """Tool for interacting with the BNB Chain."""

    bnb_chain_api_wrapper: BnbChainAPIWrapper
    name: str = ''
    description: str = ''
    args_schema: Optional[type[BaseModel]] = None
    func: Optional[Callable[..., str]] = None
    async_func: Optional[Callable[..., Coroutine[Any, Any, str]]] = None

    def _run(
        self,
        instructions: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        if self.func is None:
            raise RuntimeError(f'Can not run {self.name} tool without a synchronous way')

        """Use the BNB Chain API to run an operation."""
        if not instructions or instructions == '{}':
            # Catch other forms of empty input that GPT-4 likes to send.
            instructions = ''
        if self.args_schema is not None:
            validated_input_data = self.args_schema(**kwargs)
            parsed_input_args = validated_input_data.model_dump()
        else:
            parsed_input_args = {'instructions': instructions}
        return self.bnb_chain_api_wrapper.run_action(self.func, **parsed_input_args)

    async def _arun(
        self,
        instructions: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        if self.async_func is None:
            return self._run(instructions, run_manager=run_manager.get_sync(), **kwargs)  # type: ignore

        """Use the BNB Chain API to run an operation."""
        if not instructions or instructions == '{}':
            # Catch other forms of empty input that GPT-4 likes to send.
            instructions = ''
        if self.args_schema is not None:
            validated_input_data = self.args_schema(**kwargs)
            parsed_input_args = validated_input_data.model_dump()
        else:
            parsed_input_args = {'instructions': instructions}
        return await self.bnb_chain_api_wrapper.async_run_action(self.async_func, **parsed_input_args)
