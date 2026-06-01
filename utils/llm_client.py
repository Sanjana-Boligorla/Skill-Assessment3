import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GATEWAY_BASE_URL = "https://keygateway.arshnivlabs.com/v1"
GATEWAY_API_KEY = "learner052"


def get_client() -> OpenAI:
    """Return an OpenAI client pointed at the key gateway."""
    api_key = os.getenv("OPENAI_API_KEY") or GATEWAY_API_KEY
    base_url = GATEWAY_BASE_URL  # always hardcoded — never rely on env for this
    return OpenAI(api_key=api_key, base_url=base_url)
