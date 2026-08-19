"""Entry point. Everything it does lives in `fb_vocab_poster.interface.cli`.

  python main.py draft "Travel" B1
  python main.py build   drafts/travel_B1_20260101-120000.md
  python main.py publish drafts/travel_B1_20260101-120000.md
"""
import sys

from fb_vocab_poster.interface.cli import main

if __name__ == "__main__":
    sys.exit(main())
