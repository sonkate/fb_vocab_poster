"""Uploads a finished video to a Facebook Page via the Graph API.

Implements `application.ports.LessonPublisher`. Adding Instagram or TikTok later
means another class shaped like this one — the render half of the pipeline does
not change.
"""
from dataclasses import dataclass

import requests

from ...application.ports import PublishReceipt

UPLOAD_TIMEOUT_SECONDS = 300


class PublishError(RuntimeError):
    """The platform rejected the upload."""


@dataclass(frozen=True)
class FacebookPagePublisher:
    page_id: str
    access_token: str
    graph_version: str = "v20.0"
    timeout: int = UPLOAD_TIMEOUT_SECONDS

    @property
    def endpoint(self) -> str:
        return (
            f"https://graph-video.facebook.com/{self.graph_version}"
            f"/{self.page_id}/videos"
        )

    def publish(self, video_path: str, message: str) -> PublishReceipt:
        if not self.access_token or not self.page_id:
            raise PublishError("FB_PAGE_ACCESS_TOKEN / FB_PAGE_ID missing from .env")

        with open(video_path, "rb") as handle:
            response = requests.post(
                self.endpoint,
                data={"access_token": self.access_token, "description": message},
                files={"source": handle},
                timeout=self.timeout,
            )

        payload = response.json()
        if response.status_code != 200 or "error" in payload:
            raise PublishError(f"Facebook API error: {payload}")
        return PublishReceipt(post_id=str(payload.get("id", "")), raw=payload)
