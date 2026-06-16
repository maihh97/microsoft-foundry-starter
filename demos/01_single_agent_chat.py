"""EXAMPLE 01 — Single agent chat. Foundry Agent Service API (azure-ai-projects 2.x).

The new lifecycle: create_version (a PromptAgentDefinition) -> run via the Responses API
with an agent_reference -> delete_version. 

python demos/01_single_agent_chat.py
"""
import os

from dotenv import load_dotenv

load_dotenv()

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4.1")

# AIProjectClient is the front door; get_openai_client() gives an OpenAI client wired to
# your project (Entra ID auth, no key) for the Responses API.
project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
openai = project.get_openai_client()

# 1. Create a versioned, server-side agent.
agent = project.agents.create_version(
    agent_name="my-agent",
    definition=PromptAgentDefinition(
        model=model,
        instructions="You are a friendly assistant. Keep answers to one or two sentences.",
    ),
)
print(f"Created agent: {agent.name} v{agent.version}")

try:
    # 2. A conversation holds state (the new equivalent of a thread).
    conversation = openai.conversations.create()

    # 3. Run the agent via the Responses API. agent_reference points the run at your agent.
    response = openai.responses.create(
        conversation=conversation.id,
        input="Give me a one-sentence pitch for the Foundry Agent Service.",
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    print("\nAssistant:", response.output_text)
finally:
    # 4. Clean up the agent version.
    project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("Deleted agent version.")
