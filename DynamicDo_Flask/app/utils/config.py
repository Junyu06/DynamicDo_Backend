from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    env: str
    ai_provider: str
    openai_api_key: Optional[str]
    mongodb_uri: str
    mongodb_db: str


def load_config() -> AppConfig:
    load_dotenv(override=False)

    return AppConfig(
        env=os.getenv("FLASK_ENV", "development"),
        ai_provider=os.getenv("AI_PROVIDER", "local"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        mongodb_uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        mongodb_db=os.getenv("MONGODB_DB", "dynamicdo"),
    )


