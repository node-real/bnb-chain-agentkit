"""BNB Chain Toolkit."""

from langchain_core.tools import BaseTool
from langchain_core.tools.base import BaseToolkit

from langchain_bnb_chain.actions import BNB_CHAIN_ACTIONS
from langchain_bnb_chain.tools import BnbChainTool
from langchain_bnb_chain.utils import BnbChainAPIWrapper


class BnbChainToolkit(BaseToolkit):
    """BNB Chain Toolkit.

    *Security Note*: This toolkit contains tools that can read and modify
        the state of a service; e.g., by creating, deleting, or updating,
        reading underlying data.

        For example, this toolkit can be used to create wallets, transactions,
        and smart contract invocations on BNB Chain.

    Setup:
        See detailed installation instructions here:
        https://python.langchain.com/docs/integrations/tools/bnb_chain/#installation

        You will need to set the following environment
        variables:

        .. code-block:: bash

            export PRIVATE_KEY="private-key"
            export PROVIDER_URL="provider-url"

    Instantiate:
        .. code-block:: python

            from bnb_chain.agent_toolkits import BnbChainToolkit
            from bnb_chain.utils import BnbChainAPIWrapper

            bnb_chain = BnbChainAPIWrapper()
            bnb_chain_toolkit = BnbChainToolkit.from_bnb_chain_api_wrapper(bnb_chain)

    Tools:
        .. code-block:: python

            tools = bnb_chain_toolkit.get_tools()
            for tool in tools:
                print(tool.name)

        .. code-block:: none

            get_balance
            transfer
    Use within an agent:
        .. code-block:: python

            from langchain_openai import ChatOpenAI
            from langgraph.prebuilt import create_react_agent

            # Select example tool
            tools = [tool for tool in toolkit.get_tools() if tool.name == "get_balance"]
            assert len(tools) == 1

            llm = ChatOpenAI(model="gpt-4o-mini")
            agent_executor = create_react_agent(llm, tools)

            example_query = "Check my BNB balance"

            events = agent_executor.stream(
                {"messages": [("user", example_query)]},
                stream_mode="values",
            )
            for event in events:
                event["messages"][-1].pretty_print()

        .. code-block:: none

            ================================ Human Message =================================

            Check my BNB balance
            ================================== Ai Message ==================================
            Tool Calls:
            get_balance (call_w4HfhOLX9d5lH7emf1QKQCF4)
            Call ID: call_w4HfhOLX9d5lH7emf1QKQCF4
            Args:
                account: None
                token: None
            ================================= Tool Message =================================
            Name: get_balance

            Balances for account 0x1234 of BNB:
            6145615640500000000 (decimals: 18)
            ================================== Ai Message ==================================

            Your BNB balance is 6.1456156405 BNB.

    Parameters
    ----------
        tools: List[BaseTool]. The tools in the toolkit. Default is an empty list.

    """

    tools: list[BaseTool] = []

    @classmethod
    def from_bnb_chain_api_wrapper(cls, bnb_chain_api_wrapper: BnbChainAPIWrapper) -> 'BnbChainToolkit':
        """Create a BnbChainToolkit from a BnbChainAPIWrapper.

        Args:
            bnb_chain_api_wrapper: BnbChainAPIWrapper. The BNB Chain API wrapper.

        Returns:
            BnbChainToolkit. The BNB Chain toolkit.

        """
        actions = BNB_CHAIN_ACTIONS

        tools = [
            BnbChainTool(
                name=action.name,
                description=action.description,
                bnb_chain_api_wrapper=bnb_chain_api_wrapper,
                args_schema=action.args_schema,
                func=action.func,
                async_func=action.async_func,
            )
            for action in actions
        ]

        return cls(tools=tools)  # type: ignore[arg-type]

    def get_tools(self) -> list[BaseTool]:
        """Get the tools in the toolkit."""
        return self.tools
