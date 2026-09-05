#!/usr/bin/env python3
"""Answers "is my TiengDong TTS session still good, and for how long?"

TiengDong hands out two different kinds of cookie, so the answer splits in two:

- `atts_user_id` (-> TIENGDONG_COOKIE_ID) has a real, discoverable expiry: the
  site's own JS (`core-user.js`) sets it client-side for exactly 365 days and
  never renews it on later visits, and the id string itself ends with the
  creation timestamp (`Date.now().toString(36)`) — so we can decode that and
  print the exact expiry date without any network call.
- `PHPSESSID` (-> TIENGDONG_PHPSESSID) is a plain server-side session cookie
  with no client-visible expiry at all. There is no way to know its remaining
  lifetime in advance — the only honest check is to actually try it. So this
  script also fires one real, minimal synthesis request and reports whether
  the session is currently accepted.

Run it before batch-drafting a week of videos, not just when a build fails.
"""
import datetime as dt
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fb_vocab_poster.domain import SpeechCue  # noqa: E402
from fb_vocab_poster.infrastructure.audio import (  # noqa: E402
    TiengDongSpeechSynthesizer,
    TiengDongSynthesisError,
)
from fb_vocab_poster.infrastructure.config import Settings  # noqa: E402

COOKIE_ID_PREFIX = "atts_v1"
COOKIE_LIFETIME_DAYS = 365


def describe_cookie_id_expiry(cookie_id: str) -> None:
    if not cookie_id.startswith(COOKIE_ID_PREFIX):
        print(f"TIENGDONG_COOKIE_ID doesn't look like an atts_ id ({cookie_id!r}) — skipping expiry check.")
        return

    # The id is prefix + a variable-length random part + Date.now().toString(36).
    # The random part's length varies, but the trailing timestamp is reliably
    # 8 base36 characters for any date before the year ~2059, so the last 8
    # characters are always the timestamp regardless of the random part.
    timestamp_b36 = cookie_id[len(COOKIE_ID_PREFIX):][-8:]
    try:
        created_at = dt.datetime.fromtimestamp(int(timestamp_b36, 36) / 1000, tz=dt.timezone.utc)
    except ValueError:
        print(f"Couldn't decode a timestamp out of {cookie_id!r} — skipping expiry check.")
        return

    expires_at = created_at + dt.timedelta(days=COOKIE_LIFETIME_DAYS)
    days_left = (expires_at - dt.datetime.now(dt.timezone.utc)).days
    print(f"TIENGDONG_COOKIE_ID created:  {created_at:%Y-%m-%d} (decoded from the id itself)")
    print(f"TIENGDONG_COOKIE_ID expires:  {expires_at:%Y-%m-%d} ({days_left} days left)")
    print("  (fixed 365-day cookie set client-side; visiting the page again does NOT reset this clock)")


def check_session_live(settings: Settings) -> None:
    if not settings.tiengdong_php_session_id or not settings.tiengdong_cookie_id:
        print("\nTIENGDONG_PHPSESSID / TIENGDONG_COOKIE_ID not set in .env — nothing to test.")
        return

    print("\nPHPSESSID has no client-visible expiry (plain server session) — the only way")
    print("to know if it's still valid is to actually try it:")
    synthesizer = TiengDongSpeechSynthesizer(
        php_session_id=settings.tiengdong_php_session_id,
        cookie_id=settings.tiengdong_cookie_id,
        voice=settings.tiengdong_voice,
    )
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name
    try:
        synthesizer.synthesize(SpeechCue(kind="word", text="hi"), out_path)
        size = os.path.getsize(out_path)
        print(f"  OK — session accepted, got {size} bytes of audio back.")
    except TiengDongSynthesisError as error:
        print(f"  STALE — session was rejected: {error}")
        print("  Re-capture PHPSESSID/atts_user_id from a browser (see .env.example) and update .env.")
    finally:
        os.unlink(out_path)


if __name__ == "__main__":
    settings = Settings.from_env()
    if settings.tiengdong_cookie_id:
        describe_cookie_id_expiry(settings.tiengdong_cookie_id)
    check_session_live(settings)
