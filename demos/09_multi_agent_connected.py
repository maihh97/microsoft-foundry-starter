"""Example 09 — Multi-agent, code-orchestrated, use example 10 for the built-in orchestration patterns of agent-framework.

Here a "researcher" agent produces notes, then a "writer" agent turns them into a brief.

    python demos/09_multi_agent_connected.py
"""
import os

from dotenv import load_dotenv

load_dotenv()

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")

project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
openai = project.get_openai_client()


def run_agent(agent, prompt: str) -> str:
    """Run one prompt agent via the Responses API and return its text."""
    conversation = openai.conversations.create()
    response = openai.responses.create(
        conversation=conversation.id,
        input=prompt,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    return response.output_text


researcher = project.agents.create_version(
    agent_name="researcher",
    definition=PromptAgentDefinition(
        model=model, instructions="You research topics and return concise, sourced notes."),
)
writer = project.agents.create_version(
    agent_name="writer",
    definition=PromptAgentDefinition(
        model=model, instructions="You turn rough notes into a clear, structured brief."),
)

try:
    topic = "Why managed agent services reduce time-to-demo."
    notes = run_agent(researcher, f"Research this topic in 4-5 bullet points: {topic}")
    print("\n[researcher notes]\n", notes)

    brief = run_agent(writer, f"Notes:\n{notes}\n\nWrite a 3-paragraph brief from these.")
    print("\n[final brief]\n", brief)
finally:
    for a in (researcher, writer):
        project.agents.delete_version(agent_name=a.name, agent_version=a.version)
    print("\nDeleted both agent versions.")
