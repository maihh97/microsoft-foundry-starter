"""Example 11 — Foundry hosted Workflow (declarative multi-agent orchestration). NEW API.

Foundry **Workflows** let you orchestrate multiple agents declaratively (sequential, loops,
conditions, group chat, human-in-the-loop) and host the orchestration *inside* Foundry —
versioned, visualized, and traceable in the portal. This is different from `demos/09`
(code-orchestrated) and from the Agent Framework's in-process orchestration (`demos/10`).

This script:
  1. Creates the two agents the workflow references (Drafter, Reviewer).
  2. Registers `workflow_ops_review.yaml` as a WorkflowAgentDefinition (makes it hosted).
  3. (Optional) Runs the hosted workflow via the Responses API.

    python demos/11_workflow_hosted.py

"""
import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, WorkflowAgentDefinition
from azure.identity import DefaultAzureCredential

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")

yaml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    Path(__file__).parent / "workflow_ops_review.yaml")

project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential(), allow_preview=True)
openai = project.get_openai_client()

# 1. Create the agents the workflow invokes by name (must match the YAML).
print("Creating DrafterAgent and ReviewerAgent...")
drafter = project.agents.create_version(
    agent_name="DrafterAgent",
    definition=PromptAgentDefinition(
        model=model,
        instructions="You draft concise weekly outpatient operations reports. Revise on feedback."),
)
reviewer = project.agents.create_version(
    agent_name="ReviewerAgent",
    definition=PromptAgentDefinition(
        model=model,
        instructions=("You review operations reports for clarity and completeness. "
                      "If acceptable, reply starting with the word 'approved'. Otherwise list "
                      "specific changes.")),
)

# 2. Register the workflow itself (this makes it a *hosted* workflow in Foundry).
print(f"Registering workflow from {yaml_path.name}...")
workflow_yaml = yaml_path.read_text()
wf = yaml.safe_load(workflow_yaml)
workflow_agent = project.agents.create_version(
    agent_name=wf["name"],
    definition=WorkflowAgentDefinition(workflow=workflow_yaml),
    description=wf.get("description", ""),
)
print(f"Hosted workflow registered: {workflow_agent.name} v{workflow_agent.version}")
print("Open the Foundry portal → Workflows to see the visual graph + traces.")

# 3. Optional: run the hosted workflow like any agent (comment out to only deploy).
print("\nRunning the workflow...\n")
conversation = openai.conversations.create()
response = openai.responses.create(
    conversation=conversation.id,
    input="Draft this week's operations report for the North outpatient clinic.",
    extra_body={"agent_reference": {"name": workflow_agent.name, "type": "agent_reference"}},
)
print("Workflow result:\n", response.output_text)
