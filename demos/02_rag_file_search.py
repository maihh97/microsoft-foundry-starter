"""EXAMPLE 02 — RAG with File Search. NEW Foundry Agent Service API (azure-ai-projects 2.x).

Create a vector store + upload a file via the OpenAI client, attach FileSearchTool to a
PromptAgentDefinition, run via the Responses API. Defaults to the bundled clinical brief.

    python demos/02_rag_file_search.py                       # bundled sample
    python demos/02_rag_file_search.py path/to/document.pdf  # your file

Docs: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/file-search
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential

DEFAULT_FILE = Path(__file__).resolve().parents[1] / "sample_data" / "foundry_overview.md"
doc = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_FILE)

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")

project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
openai = project.get_openai_client()

print(f"Indexing: {doc}")

# 1. Create a vector store and upload the file into it (OpenAI client handles both).
vector_store = openai.vector_stores.create(name="rag-demo-store")
with open(doc, "rb") as file_handle:
    openai.vector_stores.files.upload_and_poll(
        vector_store_id=vector_store.id, file=file_handle
    )

# 2. Create an agent with the File Search tool bound to that vector store.
agent = project.agents.create_version(
    agent_name="rag-agent",
    definition=PromptAgentDefinition(
        model=model,
        instructions="Answer using only the uploaded documents. Cite what you used.",
        tools=[FileSearchTool(vector_store_ids=[vector_store.id])],
    ),
)
print(f"Created agent: {agent.name} v{agent.version}")

try:
    conversation = openai.conversations.create()
    response = openai.responses.create(
        conversation=conversation.id,
        input=("What are the governance rules for agents, and which service line/site grew "
               "fastest in the pilot? Answer only from the document and cite it."),
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    print("\nAssistant:", response.output_text)
finally:
    project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    openai.vector_stores.delete(vector_store.id)
    print("Deleted agent + vector store.")
