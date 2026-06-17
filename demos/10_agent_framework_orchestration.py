"""STEP 10 — Multi-agent orchestration with the Microsoft Agent Framework. NEW API.

The Agent Framework has built-in orchestration patterns that run **in your process**
(vs. Foundry-hosted Workflows in demos/10):

    Sequential | Concurrent | Handoff | Group Chat | Magentic

This demo runs a **Sequential** pipeline (drafter → reviewer) over Foundry-backed agents.
Swap the builder to show the other patterns.

    python demos/11_agent_framework_orchestration.py

Install:  pip install agent-framework aiohttp     (orchestrations ship with agent-framework)
Env:      FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL ;  Auth: az login
Docs:     https://learn.microsoft.com/agent-framework/workflows/orchestrations/
          https://github.com/microsoft/agent-framework/tree/main/python/samples/03-workflows/orchestrations

"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


async def main() -> None:
    client = FoundryChatClient(credential=AzureCliCredential())  # reads FOUNDRY_PROJECT_ENDPOINT/MODEL

    # Create agents with the Agent(client=...) constructor (verified pattern).
    # NOTE: FoundryChatClient has no `.create_agent()` — use Agent(client=...) instead.
    drafter = Agent(
        client=client,
        instructions="You draft a concise weekly outpatient operations report (appointment "
                     "volumes, wait times, staffing) from the user's request.",
    )
    reviewer = Agent(
        client=client,
        instructions="You review the draft report for clarity and completeness and return a "
                     "final, polished version.",
    )

    task = ("Draft a weekly operations report for the North outpatient clinic: appointments "
            "up ~12%, average wait down to 9 days, two locum staff covering leave.")

    # --- Primary: the framework's built-in Sequential orchestration. ---
    try:
        from agent_framework import SequentialBuilder  # name per agent-framework v1.0

        workflow = SequentialBuilder().participants([drafter, reviewer]).build()
        last = None
        async for event in workflow.run_stream(task):
            text = getattr(event, "text", None) or getattr(event, "data", None)
            if text:
                last = text
        print("\n[sequential orchestration result]\n", last)
        return
    except Exception as exc:  # noqa: BLE001
        print(f"[note] built-in SequentialBuilder unavailable ({exc}); using a plain chain.\n")

    # --- Fallback: chain the agents manually (same effect, no orchestration package). ---
    draft = (await drafter.run(task)).text
    print("[draft]\n", draft, "\n")
    final = (await reviewer.run(f"Review and finalize this draft:\n{draft}")).text
    print("[final]\n", final)


if __name__ == "__main__":
    asyncio.run(main())
