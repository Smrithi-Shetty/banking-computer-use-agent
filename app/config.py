import os
from urllib.parse import urlparse

from dotenv import load_dotenv


load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}"
        )

    return value


# Microsoft Foundry

AZURE_OPENAI_ENDPOINT = require_env(
    "AZURE_OPENAI_ENDPOINT"
)

AZURE_OPENAI_API_KEY = require_env(
    "AZURE_OPENAI_API_KEY"
)

AZURE_OPENAI_DEPLOYMENT = require_env(
    "AZURE_OPENAI_DEPLOYMENT"
)


# ParaBank

PARABANK_BASE_URL = require_env(
    "PARABANK_BASE_URL"
)

PARABANK_HOST = urlparse(
    PARABANK_BASE_URL
).hostname


# Agent controls

MAX_AGENT_STEPS = int(
    os.getenv(
        "MAX_AGENT_STEPS",
        "25",
    )
)

AGENT_TIMEOUT_SECONDS = int(
    os.getenv(
        "AGENT_TIMEOUT_SECONDS",
        "300",
    )
)

HEADLESS = (
    os.getenv(
        "HEADLESS",
        "false",
    ).strip().lower()
    == "true"
)