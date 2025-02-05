"""Util that calls BNB Chain."""

import inspect
from collections.abc import Callable, Coroutine
from typing import Any

from langchain_core.utils import get_from_dict_or_env
from pydantic import BaseModel, model_validator

from bnb_chain_agentkit.provider.bnb_chain_provider import BnbChainProvider


class BnbChainAPIWrapper(BaseModel):
    """Wrapper for BNB Chain API."""

    provider: Any = None  #: :meta private:

    @model_validator(mode='before')
    @classmethod
    def validate_environment(cls, values: dict) -> Any:
        """Validate that the required env variables and python package exists in the environment and configure the Web3 provider."""
        private_key = get_from_dict_or_env(values, 'private_key', 'PRIVATE_KEY')
        bsc_provider_url = get_from_dict_or_env(values, 'bsc_provider_url', 'BSC_PROVIDER_URL')
        opbnb_provider_url = get_from_dict_or_env(values, 'opbnb_provider_url', 'OPBNB_PROVIDER_URL')

        try:
            import bnb_chain_agentkit
        except Exception:
            raise ImportError(
                "BNB Chain toolkits is not installed. " "Please install it with `pip install bnb-chain-agentkit`"
            ) from None

        provider = BnbChainProvider(private_key, bsc_provider_url, opbnb_provider_url)

        values['provider'] = provider

        return values

    def run_action(self, func: Callable[..., str], **kwargs) -> str:
        """Run a BNB Chain Action."""
        func_signature = inspect.signature(func)

        first_kwarg = next(iter(func_signature.parameters.values()), None)

        if first_kwarg and first_kwarg.annotation is BnbChainProvider:
            return func(self.provider, **kwargs)
        else:
            return func(**kwargs)

    async def async_run_action(self, async_func: Callable[..., Coroutine[Any, Any, str]], **kwargs) -> str:
        """Run a BNB Chain Action."""
        func_signature = inspect.signature(async_func)

        first_kwarg = next(iter(func_signature.parameters.values()), None)

        if first_kwarg and first_kwarg.annotation is BnbChainProvider:
            return await async_func(self.provider, **kwargs)
        else:
            return await async_func(**kwargs)
