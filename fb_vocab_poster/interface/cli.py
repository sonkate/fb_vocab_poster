"""The command-line adapter.

Its whole job is turning argv into a use-case call and a use-case result into
words on a terminal. No pipeline logic lives here.
"""
import argparse
from typing import List, Optional

from ..container import Container
from ..domain import FORMATS, DomainError

PROGRAM = "main.py"
DESCRIPTION = "Draft, render and publish English vocabulary lessons as Facebook videos."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=DESCRIPTION)
    commands = parser.add_subparsers(dest="command", required=True)

    draft = commands.add_parser(
        "draft", help="write an editable lesson draft to drafts/"
    )
    draft.add_argument("topic", help='lesson topic, e.g. "Ordering coffee"')
    draft.add_argument("level", help="CEFR level: A1 A2 B1 B2 C1 C2")
    draft.add_argument(
        "--format",
        dest="lesson_format",
        default="vocab",
        choices=[name.value for name in FORMATS],
        help="which kind of lesson to write (default: vocab)",
    )

    build = commands.add_parser(
        "build", help="render audio + video from a draft, without posting"
    )
    build.add_argument("draft", help="path to a draft .md file")

    publish = commands.add_parser(
        "publish", help="render a draft and post it to your Facebook Page"
    )
    publish.add_argument("draft", help="path to a draft .md file")
    publish.add_argument(
        "--skip-render",
        action="store_true",
        help="reuse output/<basename>.mp4 from a previous build instead of "
        "re-rendering, if it is newer than the draft",
    )

    commands.add_parser(
        "backfill-ledger",
        help="record every draft already in drafts/ into the vocabulary ledger",
    )

    return parser


def _draft(container: Container, args) -> int:
    ref = container.draft_lesson(args.topic, args.level, args.lesson_format)
    reporter = container.reporter

    if not container.settings.can_auto_draft:
        reporter.notice("(No ANTHROPIC_API_KEY set — wrote a blank template. Paste in")
        reporter.notice(" content from a free Claude chat, or add a key to auto-draft.)")

    reporter.result(f"\nDraft ready: {ref}")
    reporter.result("Open it, edit the paragraph/vocab/caption as you like, then run:")
    reporter.result(f"  python {PROGRAM} build {ref}      # preview only")
    reporter.result(f"  python {PROGRAM} publish {ref}    # preview + post to Facebook")
    return 0


def _backfill_ledger(container: Container, args) -> int:
    reporter = container.reporter
    if not container.settings.can_remember_vocabulary:
        # Without credentials the ledger is the drafts folder itself, so a
        # backfill would read the files and write them straight back.
        reporter.notice("No FIRESTORE_CREDENTIALS set — nothing to back fill into.")
        reporter.notice("The drafts folder is already its own record.")
        return 1

    report = container.backfill_ledger()
    reporter.result(
        f"\nRecorded {len(report.recorded)} of {report.total} drafts into "
        f"'{container.settings.firestore_collection}'."
    )
    for basename, reason in report.skipped:
        reporter.result(f"  skipped {basename} — {reason}")
    return 0


def _build(container: Container, args) -> int:
    rendered = container.render_lesson(args.draft)
    container.reporter.result(f"Video ready: {rendered.video_path}")
    return 0


def _publish(container: Container, args) -> int:
    rendered, receipt = container.publish_lesson(args.draft, skip_render=args.skip_render)
    container.reporter.result(f"Video ready: {rendered.video_path}")
    container.reporter.result(f"Posted! Facebook video id: {receipt.post_id}")
    return 0


HANDLERS = {
    "draft": _draft,
    "build": _build,
    "publish": _publish,
    "backfill-ledger": _backfill_ledger,
}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    container = Container.from_env()
    try:
        return HANDLERS[args.command](container, args)
    except DomainError as error:
        # Expected, user-fixable problems: a bad level, an unfinished draft.
        print(f"Error: {error}")
        return 1
