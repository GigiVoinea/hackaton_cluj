# orchestrator.py
"""
Boilerplate orchestrator for agentic workflows using LangGraph and Pydantic.
"""
import os
from typing import Any
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from mcp_client import MCPClientWrapper
import asyncio

load_dotenv()

class Orchestrator:
    def __init__(self):
        # Check for OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your environment or create a .env file with OPENAI_API_KEY=your_key_here"
            )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0,
            openai_api_key=SecretStr(openai_api_key)
        )
        # Initialize tools as None - will be loaded lazily
        self.tools = None
        self.llm_with_tools = self.llm
        self._tools_loaded = False

    async def _load_tools_if_needed(self):
        """Lazy load MCP tools if not already loaded."""
        if self._tools_loaded:
            return
            
        try:
            client = MCPClientWrapper()
            self.tools = await client.list_tools()
            if self.tools:
                # Bind tools to the LLM
                self.llm_with_tools = self.llm.bind_tools(self.tools)
                print(f"Loaded {len(self.tools)} MCP tools: {[tool.name for tool in self.tools]}")
            else:
                print("No MCP tools available")
        except Exception as e:
            print(f"Could not fetch MCP tools: {e}")
            self.tools = []
        
        self._tools_loaded = True

    async def run(self, user_message: str) -> Any:
        """
        Run the agentic workflow with tool calling capabilities.
        """
        # Load tools if not already loaded
        await self._load_tools_if_needed()
        
        graph = self.build_agent_workflow()
        compiled = graph.compile()
        compiled.get_graph().print_ascii()
        
        # Use MessagesState format
        initial_state = {"messages": [HumanMessage(content=user_message)]}
        return await compiled.ainvoke(initial_state)

    async def call_model(self, state: MessagesState):
        """Node that calls the LLM, potentially with tools."""
        response = self.llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def build_agent_workflow(self):
        """Build a LangGraph workflow where the LLM can call tools."""
        graph = StateGraph(MessagesState)
        
        # Add the model node
        graph.add_node("agent", self.call_model)
        
        # Add tool node if we have tools
        if self.tools:
            graph.add_node("tools", ToolNode(self.tools))
        
        # Set entry point
        graph.set_entry_point("agent")
        
        if self.tools:
            # Add conditional edges for tool calling
            graph.add_conditional_edges(
                "agent",
                tools_condition,
            )
            # After tools, go back to agent
            graph.add_edge("tools", "agent")
        else:
            # No tools, just end after agent
            graph.add_edge("agent", END)
        
        return graph