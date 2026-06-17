"""EXAMPLE 03 — Code Interpreter. NEW Foundry Agent Service API (azure-ai-projects 2.x).

Upload a CSV via the OpenAI client, attach CodeInterpreterTool to a PromptAgentDefinition,
run via the Responses API. Defaults to the bundled clinical dataset.

    python demos/03_code_interpreter.py                   # bundled sample
    python demos/03_code_interpreter.py path/to/data.csv  # your file

Docs: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/code-interpreter
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    AutoCodeInterpreterToolParam,
    CodeInterpreterTool,
    PromptAgentDefinition,
)
from azure.identity import DefaultAzureCredential

DEFAULT_FILE = Path(__file__).resolve().parents[1] / "sample_data" / "clinic_encounters.csv"
data = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_FILE)

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")

project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
openai = project.get_openai_client()

print(f"Uploading: {data}")

# 1. Upload the data file for the sandbox (purpose="assistants").
with open(data, "rb") as fh:
    file = openai.files.create(purpose="assistants", file=fh)

# 2. Create an agent with Code Interpreter, seeded with the uploaded file.
agent = project.agents.create_version(
    agent_name="analyst-agent",
    definition=PromptAgentDefinition(
        model=model,
        instructions="You are a data analyst. Write and run Python to answer questions.",
        tools=[CodeInterpreterTool(container=AutoCodeInterpreterToolParam(file_ids=[file.id]))],
    ),
)
print(f"Created agent: {agent.name} v{agent.version}")

try:
    conversation = openai.conversations.create()
    response = openai.responses.create(
        conversation=conversation.id,
        input=("Load the uploaded clinic CSV. Which service_line + site grew fastest by "
               "percentage in patient_encounters from January to June 2025, and how did its "
               "average wait time change? Show the figures you used."),
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    print("\nAssistant:", response.output_text)
finally:
    project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    openai.files.delete(file.id)
    print("Deleted agent + file.")
