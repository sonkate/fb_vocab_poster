"""The output layout: finished videos land in a month folder keyed by the
draft's own timestamp, while narration audio and per-slide intermediates —
the technical junk nobody opens — live apart from them under `_work/`."""
import os
from datetime import datetime, timedelta

from fb_vocab_poster.infrastructure.config.workspace import FileSystemWorkspace

BASENAME = "work-email_B1_20260908-231010"


def _workspace(tmp_path):
    return FileSystemWorkspace(output_dir=str(tmp_path))


def test_a_video_lands_in_the_month_folder_its_own_timestamp_names(tmp_path):
    workspace = _workspace(tmp_path)

    path = workspace.video(BASENAME)

    assert path == os.path.join(str(tmp_path), "2026-09", f"{BASENAME}.mp4")


def test_narration_and_slide_intermediates_stay_out_of_the_month_folders(tmp_path):
    workspace = _workspace(tmp_path)

    audio = workspace.narration_audio(BASENAME)
    audio_workdir = workspace.narration_workdir(BASENAME)
    slides_workdir = workspace.slides_workdir(BASENAME)

    for path in (audio, audio_workdir, slides_workdir):
        assert f"{os.sep}_work{os.sep}" in path
        assert "2026-09" not in path


def test_fresh_video_finds_a_video_already_rendered_at_the_new_path(tmp_path):
    workspace = _workspace(tmp_path)
    video_path = workspace.video(BASENAME)
    open(video_path, "w").close()
    since = datetime.now() - timedelta(minutes=5)

    assert workspace.fresh_video(BASENAME, since) == video_path


def test_fresh_video_also_finds_a_video_left_over_from_the_old_flat_layout(tmp_path):
    """Transition-period compatibility: a video rendered before the month
    split still resolves, so `--skip-render` keeps working without every old
    file having to be moved by hand first."""
    workspace = _workspace(tmp_path)
    legacy_path = os.path.join(str(tmp_path), f"{BASENAME}.mp4")
    open(legacy_path, "w").close()
    since = datetime.now() - timedelta(minutes=5)

    assert workspace.fresh_video(BASENAME, since) == legacy_path


def test_fresh_video_prefers_the_new_path_when_both_exist(tmp_path):
    workspace = _workspace(tmp_path)
    new_path = workspace.video(BASENAME)
    open(new_path, "w").close()
    legacy_path = os.path.join(str(tmp_path), f"{BASENAME}.mp4")
    open(legacy_path, "w").close()
    since = datetime.now() - timedelta(minutes=5)

    assert workspace.fresh_video(BASENAME, since) == new_path


def test_fresh_video_rejects_a_video_older_than_since_at_either_path(tmp_path):
    workspace = _workspace(tmp_path)
    legacy_path = os.path.join(str(tmp_path), f"{BASENAME}.mp4")
    open(legacy_path, "w").close()
    since = datetime.now() + timedelta(minutes=5)

    assert workspace.fresh_video(BASENAME, since) is None
