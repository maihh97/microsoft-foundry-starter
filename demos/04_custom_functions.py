"""Example 04 — Function calling. NEW Foundry API via the Responses API.

Custom Python functions exposed as tools through the Responses API. The model decides when
to call them; you execute locally and return the result, then the model finishes. This is
the OpenAI-native function-calling loop, run against your Foundry project's OpenAI client.

    python demos/04_custom_functions.py
"""
import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")


# --- Your functions + their JSON schemas (what the model sees).
#     Operational/administrative helpers — not clinical decision-making. ---
def calculate_bed_occupancy(occupied_beds: int, total_beds: int) -> str:
    """Operational capacity metric: bed occupancy percentage and a status band."""
    pct = round(occupied_beds / total_beds * 100, 1)
    status = "at capacity" if pct >= 90 else "high" if pct >= 75 else "normal"
    return json.dumps({"occupancy_pct": pct, "status": status})


def get_current_utc_time() -> str:
    return datetime.now(timezone.utc).isoformat()


IMPL = {"calculate_bed_occupancy": calculate_bed_occupancy,
        "get_current_utc_time": get_current_utc_time}

TOOLS = [
    {
        "type": "function",
        "name": "calculate_bed_occupancy",
        "description": "Compute ward bed-occupancy percentage from occupied and total beds.",
        "parameters": {
            "type": "object",
            "properties": {
                "occupied_beds": {"type": "integer"},
                "total_beds": {"type": "integer"},
            },
            "required": ["occupied_beds", "total_beds"],
        },
    },
    {
        "type": "function",
        "name": "get_current_utc_time",
        "description": "Return the current UTC time as an ISO-8601 string.",
        "parameters": {"type": "object", "properties": {}},
    },
]

project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
openai = project.get_openai_client()

messages = [{"role": "user",
             "content": "A ward has 82 of 100 beds occupied. What's the occupancy and status?"}]
response = openai.responses.create(model=model, input=messages, tools=TOOLS)

# Execute any function calls the model requested, then send the results back.
calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
if calls:
    tool_outputs = []
    for call in calls:
        args = json.loads(call.arguments or "{}")
        result = IMPL[call.name](**args)
        print(f"[tool] {call.name}({args}) -> {result}")
        tool_outputs.append(
            {"type": "function_call_output", "call_id": call.call_id, "output": str(result)}
        )
    response = openai.responses.create(
        model=model, previous_response_id=response.id, input=tool_outputs, tools=TOOLS
    )

print("\nAssistant:", response.output_text)
