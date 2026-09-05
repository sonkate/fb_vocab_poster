"""Settings, read once from the environment and then passed around explicitly.

Nothing outside this module reads `os.environ`, so tests construct a `Settings`
directly instead of mutating global state.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    facebook_page_access_token: str = ""
    facebook_page_id: str = ""
    facebook_graph_version: str = "v20.0"
    ttsmaker_api_key: str = ""
    tiengdong_php_session_id: str = ""
    tiengdong_cookie_id: str = ""
    tiengdong_voice: str = "en-US-Standard-E"
    drafts_dir: str = "drafts"
    output_dir: str = "output"

    @property
    def can_auto_draft(self) -> bool:
        """Without a key we still work — we just write a blank template for the
        user to fill in from a free Claude chat."""
        return bool(self.anthropic_api_key)

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        defaults = cls()
        return cls(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", defaults.anthropic_model),
            facebook_page_access_token=os.getenv("FB_PAGE_ACCESS_TOKEN", ""),
            facebook_page_id=os.getenv("FB_PAGE_ID", ""),
            facebook_graph_version=os.getenv(
                "FB_GRAPH_VERSION", defaults.facebook_graph_version
            ),
            ttsmaker_api_key=os.getenv("TTSMAKER_API_KEY", ""),
            tiengdong_php_session_id=os.getenv("TIENGDONG_PHPSESSID", ""),
            tiengdong_cookie_id=os.getenv("TIENGDONG_COOKIE_ID", ""),
            tiengdong_voice=os.getenv("TIENGDONG_VOICE", defaults.tiengdong_voice),
            drafts_dir=os.getenv("DRAFTS_DIR", defaults.drafts_dir),
            output_dir=os.getenv("OUTPUT_DIR", defaults.output_dir),
        )
