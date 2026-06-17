"""Example 05 — MCP tool. NEW Foundry API via the Responses API.

Connect the agent to a remote MCP server (Microsoft's public Learn server) using the
Responses API's native `mcp` tool. Foundry executes the MCP calls server-side; set
require_approval="never" to run them without prompting.

    python demos/05_mcp_learn_server.py

Docs: https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol
"""
import os

from dotenv import load_dotenv

load_dotenv()

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")

project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
openai = project.get_openai_client()

# Remote MCP tool, declared in the Responses API's tool format.
# For an authenticated MCP server, add "headers": {...} or a project connection.
tools = [{
    "type": "mcp",
    "server_label": "microsoft_learn",
    "server_url": "https://learn.microsoft.com/api/mcp",
    "require_approval": "never",
}]

response = openai.responses.create(
    model=model,
    input="Using Microsoft Learn, explain how MCP tool approval modes work in Foundry agents.",
    tools=tools,
)

print("Assistant:", response.output_text)
