"""Example 08 — Microsoft Agent Framework on Foundry.

The Microsoft Agent Framework (open-source, unifies Semantic Kernel + AutoGen) runs your
orchestration in-process while using Foundry models. Same agent code can later be lifted
into Foundry Hosted Agents as a container (see ../hosted_agent/).

    python demos/08_agent_framework.py

Needs: agent-framework-foundry, aiohttp, azure-identity
Env:   FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL  (keep FOUNDRY_MODEL = MODEL_DEPLOYMENT_NAME)
Verify tool-helper names (HostedMCPTool) against your installed agent-framework version.
"""
import asyncio
from typing import Annotated

from dotenv import load_dotenv

load_dotenv()

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


# A plain Python function becomes a tool (type hints + docstring = schema).
def check_staff_availability(department: Annotated[str, "Department name (e.g., 'Emergency', 'Surgery', 'Admin')"], shift: Annotated[str, "Shift type (morning/afternoon/night)"]) -> str:
    """Check staff availability for a given department and shift. Returns staffing level."""
    key = (department.lower(), shift.lower())
    staffing = {
        ("emergency", "morning"): "adequate",
        ("emergency", "afternoon"): "low",
        ("surgery", "night"): "critical",
        ("admin", "morning"): "adequate",
    }
    return staffing.get(key, "unavailable")


async def main() -> None:
    credential = AzureCliCredential()
    tools = [check_staff_availability]

    agent = Agent(
        client=FoundryChatClient(credential=credential),  # reads FOUNDRY_PROJECT_ENDPOINT / FOUNDRY_MODEL
        instructions="You are a healthcare operations assistant. Help with staff scheduling and resource planning using available tools.",
        tools=tools,
    )
    result = await agent.run(
        "We need to schedule extra nurses for Emergency and Surgery departments tomorrow. "
        "Check the current staffing levels for morning and night shifts, then recommend "
        "where additional staff would be most critical."
    )
    print("\nAssistant:", result.text)


if __name__ == "__main__":
    asyncio.run(main())
