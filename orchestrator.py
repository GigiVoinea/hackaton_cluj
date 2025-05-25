# orchestrator.py
"""
Boilerplate orchestrator for agentic workflows using LangGraph and Pydantic.
"""
import os
from typing import Any, List
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from mcp_client import MCPClientWrapper
import asyncio

load_dotenv()

class Orchestrator:
    def __init__(self):
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4.1-mini", 
            temperature=0,
            openai_api_key=SecretStr(os.getenv("OPENAI_API_KEY"))
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

    def _convert_chat_messages_to_langchain(self, chat_messages: List[Any]) -> List[Any]:
        """Convert chat messages to LangChain message format."""
        langchain_messages = []
        
        for msg in chat_messages:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                if msg.role == "user":
                    langchain_messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    langchain_messages.append(AIMessage(content=msg.content))
        
        return langchain_messages

    async def run_with_history(self, user_message: str, chat_history: List[Any]) -> Any:
        """
        Run the agentic workflow with conversation history.
        """
        print(f"run_with_history called with message: {user_message}")
        print(f"Chat history length: {len(chat_history)}")
        
        # Load tools if not already loaded
        await self._load_tools_if_needed()
        
        graph = self.build_agent_workflow()
        compiled = graph.compile()
        
        # Start with system message
        langchain_messages = [SystemMessage(content="""
Your name is Finn and you are a financial assistant with access to the user's full transaction and revenue history.
You help users understand the impact of major life events and spending changes on their financial health.

You also have access to the user's email inbox and can help manage emails. You can:
- List emails in different folders (inbox, sent, drafts, trash, spam, archive)
- Read email content and mark emails as read
- Search emails by subject, sender, or content
- Send new emails
- Move emails between folders
- Delete emails
- Get folder summaries with email counts

When helping with emails, be proactive in organizing and managing the inbox. You can suggest actions like:
- Archiving old emails
- Moving important emails to appropriate folders
- Highlighting urgent or high-priority emails
- Summarizing email content for quick review
- Helping compose professional email responses

Always ask for confirmation before taking destructive actions like deleting emails.""")]
        # Convert chat history to LangChain messages (excluding the current user message to avoid duplication)
        # The current user message is the last one in the history, so we exclude it
        history_without_current = chat_history[:-1] if len(chat_history) > 0 else []
        print(f"History without current: {len(history_without_current)} messages")
        langchain_messages.extend(self._convert_chat_messages_to_langchain(history_without_current))
        
        # Add the current user message
        langchain_messages.append(HumanMessage(content=user_message))
        print(f"Total langchain messages: {len(langchain_messages)}")
        
        # Use MessagesState format with output key
        initial_state = {
            "messages": langchain_messages,
            "output": None
        }
        print(f"Calling compiled graph...")
        result = await compiled.ainvoke(initial_state)
        print(f"Graph result: {result}")
        return result

    async def run(self, user_message: str) -> Any:
        """
        Run the agentic workflow with tool calling capabilities.
        """
        # Load tools if not already loaded
        await self._load_tools_if_needed()
        
        graph = self.build_agent_workflow()
        compiled = graph.compile()
        compiled.get_graph().print_ascii()
        
        # Use MessagesState format with output key
        initial_state = {
            "messages": [
                HumanMessage(content=user_message)
            ],
            "output": None
        }
        result = await compiled.ainvoke(initial_state)
        return result

    async def call_model(self, state: MessagesState):
        """Node that calls the LLM, potentially with tools."""
        response = self.llm_with_tools.invoke(state["messages"])
        state["messages"].append(response)
        
        # Update the output key with the last AI message content
        if hasattr(response, 'content'):
            state["output"] = response.content
        
        return state

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