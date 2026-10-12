import json

from app.foundry_client import get_client

from app.config import (
    AZURE_OPENAI_DEPLOYMENT
)

client = get_client()

response = client.responses.create(
    model=AZURE_OPENAI_DEPLOYMENT,
    input="""
You are a JSON API.

Return exactly:

{
    "status": "SUCCESS"
}

No markdown.
No explanations.
"""
)

result = json.loads(
    response.output_text
)

print(
    json.dumps(
        result,
        indent=4
    )
)