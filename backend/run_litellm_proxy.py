"""Start LiteLLM without inheriting the application's database configuration."""

import os
from dotenv import load_dotenv

load_dotenv()
# Pop the clinic app's database URL so LiteLLM doesn't try to use it for internal tracking
os.environ.pop("DATABASE_URL", None)

from litellm.proxy.proxy_cli import run_server


if __name__ == "__main__":
    run_server()
