---
name: generate-lessons
description: Generates one or more LÊN BAND lesson videos end-to-end for fb-vocab-poster, from a topic through to a rendered 4:5 feed video. Use whenever the user asks to "generate N videos/lessons", "make posters/videos about <topic(s)>", asks for the post scheduled on a given weekday, or gives a URL/list of topics to turn into videos. Covers picking the format and topic, drafting, authoring lesson content and captions to the brand rules, and building (or publishing, if explicitly asked).
---

# Generate LÊN BAND lessons

The page is **LÊN BAND** — *"Mỗi ngày một bậc từ vựng."* Everything below comes
from the brand handbook (Sổ Tay Lên Band). When a rule here conflicts with what
the code's own prompts ask for, **this file wins** — the prompts have drifted
and the known gaps are listed at the end.

Three CLI commands (see `Makefile` and `main.py`):

```
venv/bin/python main.py draft "<Topic>" <LEVEL> [--format vocab|mistake|upgrade]
venv/bin/python main.py build   <draft.md>    # renders output/<slug>...mp4 (no posting)
venv/bin/python main.py publish <draft.md>    # renders AND posts to the Facebook Page
```

Always use `venv/bin/python`, not a bare `python`/`python3` — the project's
dependencies (Pillow, dotenv, moviepy) live in that venv.

## Step 1: Pick the format first, the topic second

A topic is not the unit of content — a **format** is. The same topic yields a
completely different lesson in each format, which is what takes the content
bank from six months to two years. Decide the format before anything else.

| Format | `--format` | Section heading | The three columns mean | Paragraph? |
|---|---|---|---|---|
| Vocab Drill | `vocab` | `## Vocabulary` | word — /ipa/ — meaning | yes |
| Sai chỗ nào? | `mistake` | `## Mistakes` | wrong sentence — corrected sentence — why (Vietnamese) | no |
| Đừng nói X, nói Y | `upgrade` | `## Upgrades` | weak phrase — stronger phrase — when to use it (Vietnamese) | no |

Only these three exist in code (`fb_vocab_poster/domain/lesson_format.py`).
The handbook also plans *Bẫy phát âm*, *Bài mẫu Part 2*, *Poll A/B*, *Từ trong
tin tức*, *Trả lời bình luận*, and *Carousel tuần* — if the user asks for one
of those, say it isn't built yet rather than forcing it into an existing
format.

### The weekly rhythm

If the user asks for "the post for Thứ 2" or similar, this is the schedule:

| Day | Format | Level | Notes |
|---|---|---|---|
| T2 | Vocab Drill | A1/A2 | video |
| T3 | Sai chỗ nào? | any | aims at comments |
| T4 | Vocab Drill | B1/B2 | video |
| T5 | Đừng nói X, nói Y | any | aims at private shares |
| T6 | Bẫy phát âm | any | **not implemented yet** |
| T7 | Poll A/B | — | static image, no video |
| CN | Carousel tuần | — | static, no video |

### Choosing the topic

**Never repeat a word. Repeating a topic is fine and expected.**

Five words do not exhaust a topic — Family at A1 has twenty more — so
"Family part 2" is a lesson worth making, not a duplicate to avoid. What must
never happen is teaching `mother` twice. The unit that gets used up is the
**word**, not the topic.

The pipeline enforces this for you. `DraftLesson` asks the `VocabularyLedger`
what the topic has already taught at that level, passes the list to the drafter
as `avoid=`, and records the new words after saving. You do not maintain this
by hand.

- If the user gives a URL, fetch it and extract candidate topics.
- For "N random topics", sample N without replacement.
- If they name topics directly, use those. A topic with existing drafts is
  **not** a reason to refuse or to warn — it is a second lesson.
- Default level is **B1** unless the user says otherwise or the weekly rhythm
  dictates one. `mistake` and `upgrade` don't need a topic bank at all; their
  material is common Vietnamese-learner errors and weak→strong phrase pairs.

### The taught-word ledger

Two adapters sit behind `VocabularyLedger`, and the container reads **both**:

- `DraftFolderLedger` parses every file in `drafts/`. The drafts folder is
  already a complete history, so this works with no configuration.
- `FirestoreVocabularyLedger` writes the same history to the `taught_vocabulary`
  collection, keyed by the draft's basename. It only switches on when
  `FIRESTORE_CREDENTIALS` in `.env` points at a service-account JSON. That file
  lives outside the repository and must never be copied into it or committed.

Firestore makes the history outlive one machine — `drafts/` is gitignored, so
it exists only where it was written. Both are read together, so turning
Firestore on does not lose what is already on disk.

To see what a topic has spent before drafting:

```
venv/bin/python -c "
from fb_vocab_poster.infrastructure.ledger import DraftFolderLedger
from fb_vocab_poster.domain import CEFRLevel
print(sorted(DraftFolderLedger(drafts_dir='drafts').taught('family', CEFRLevel.parse('A1'))))
"
```

When the key is missing and you author the draft by hand, the excluded words
are written into the draft for you as a comment under the column legend
(`<!-- Đã dạy ở bài trước, đừng dùng lại: ... -->`). **Read it and honour it** —
nothing downstream checks that you did. Leave the comment in place; the parser
ignores it.

## Step 2: Draft

```
venv/bin/python main.py draft "<Topic>" <LEVEL> --format <format>
```

`--format` defaults to `vocab`, so it can be omitted for a Vocab Drill.

If `ANTHROPIC_API_KEY` is configured the draft comes back filled in — inspect
it and correct it against Step 3. If the key is missing the command says so and
writes a **blank template** with the format's column names as placeholders;
author the content yourself. Either way the file must satisfy Step 3 before you
build.

## Step 3: The content rules

A draft looks like this (parsed by
`fb_vocab_poster/infrastructure/content/markdown_format.py`, validated by
`fb_vocab_poster/domain/lesson.py`):

```markdown
---
topic: <Topic>
level: <LEVEL>
format: vocab
---

## Vocabulary
<!-- word — ipa — meaning -->
- punctual — /ˈpʌŋktʃuəl/ — arriving on time, not late

## Paragraph
A paragraph that uses **punctual** and every other word at least once.

## Caption
Vietnamese caption ending in a five-second question.
```

Keep the frontmatter (`topic:`/`level:`/`format:`) unchanged, keep the
`<!-- ... -->` column legend, and overwrite the draft in place at the path
`draft` printed.

### Rows

- The field separator is an **em dash `—`**, never a hyphen.
- **5 rows per lesson. Five is the ceiling for 45 seconds** — do not push seven
  words into one video. If the drafter returns more, delete the weakest ones.
- Every row must be pitched at the requested CEFR level. A1 means concrete,
  everyday, one- or two-syllable words; C1 means the word a band-7.5 candidate
  would actually reach for.
- **Vocab Drill**: each word needs a real IPA transcription in `/slashes/` and a
  short plain-English meaning (max ~12 words).
- **Sai chỗ nào?**: each row is a full short sentence a Vietnamese learner
  really writes, not a bare phrase — `I very like it. — I really like it. — "very" không bổ nghĩa cho động từ`.
  The third column is Vietnamese.
- **Đừng nói X, nói Y**: both sides must mean the same thing at different
  bands — `very tired — exhausted — Band 5 → 7.5, cùng một ý`. Third column
  Vietnamese.

### The paragraph (Vocab Drill only)

- One paragraph that **uses every single vocab word at least once** — the video
  highlights words word-by-word, so a word that never appears never lights up.
  The domain layer won't catch this; you must.
- **Bold each vocab word with `**double asterisks**` the first time it appears.
  This is the only thing that decides what the slide paints gold** — since
  `[Fix][Paragraph Highlight]` the code no longer guesses by matching against
  the vocab list. A paragraph with no markers renders with **no highlighted
  word at all, and nothing warns you**. Bold the first occurrence only; later
  ones stay plain, and punctuation stays outside the asterisks
  (`**brother**.`, never `**brother.**`).
- Keep it short enough that the finished video lands in **25–45 seconds**
  (Step 4 verifies this). Roughly 50–80 words at A1/A2, up to ~120 at B2+.
  The code's prompt asks for 80–140 regardless of level — trim it at low levels.

### The caption — this is where reach is won or lost

- **Vietnamese**, xưng **"mình / bạn"**, like a study partner, not a teacher.
- Short sentences, one idea each. **Max 3 lines before the "xem thêm" fold.**
- Acknowledge the difficulty where it's real: *"Từ này người Việt hay đọc sai
  chỗ này."*
- **Always end with a question a reader can answer in five seconds.**
- At most **1–2 emoji**, at the end, never sprinkled through the sentences.
- **Exactly 4 hashtags: the three fixed ones plus one topical.** The fixed set
  is `#LenBand #HocTiengAnh #TuVungTiengAnh` — never vary these three, they are
  what makes the page's posts findable as a set. The fourth names the topic
  (`#GiaDinh`, `#PhongVanXinViec`). The code's prompt says 3–5 — settle on 4.
- For `mistake` and `upgrade`, write the caption so the post is worth **sending
  privately to one specific person** — private shares are the highest-weighted
  signal in the 2026 algorithm. *"Gửi cho đứa bạn suốt ngày nói 'I'm boring' 😅"*
  works because a specific face comes to mind.

> **Never write engagement bait.** "Tag một người bạn", "Comment YES", "Share
> nếu bạn đồng ý" trip Facebook's classifier and the post gets held inside its
> seed audience — the penalty is per-post. A sincere opinion question is
> completely safe; a demand for a specific action is not. *"Bạn sửa câu này thế
> nào?"* good. *"Tag bạn bè để nhận tài liệu"* fatal.

### The first three seconds

Videos open straight on content — there is no title slide, and the brand card
runs at the end. The first row is therefore the hook, so make it the strongest
one. Opening lines that work:

- Lỗi sai — "Câu này sai. Bạn thấy sai chỗ nào không?"
- Đối lập band — "Đây là cách nói band 5. Còn đây là band 7.5."
- Gọi đúng tên — "Người Việt học tiếng Anh gần như ai cũng đọc sai từ này."
- Đếm ngược — "5 từ để nói về phỏng vấn xin việc. Từ số 4 là từ giám khảo thích nhất."
- Phủ định — "Đừng nói 'very good' trong phòng thi nữa."

## Step 4: Build, then verify the artefact

```
venv/bin/python main.py build "<draft path>"
```

Prints `Video ready: output/<slug>....mp4`. Then actually check it:

```
ffprobe -v error -show_entries format=duration \
  -show_entries stream=codec_type,width,height \
  -of default=noprint_wrappers=1 "<mp4 path>"
```

- **Resolution must be 1080×1350** (4:5). These go out as ordinary Facebook
  **feed posts, not Reels** — the publisher posts to `/{page_id}/videos`, not
  `/video_reels` — and 4:5 is the tallest shape a feed post fills without
  cropping. The handbook's "Reels get 3–4× the reach" line compares Reels
  against *photo and link posts*; it says nothing about 9:16 video versus 4:5
  video, so it is not a reason to go taller. If it isn't 1080×1350, stop and
  report — don't patch the renderer from inside this workflow.
- **Duration should land in 25–45 seconds.** If it doesn't, say so plainly
  rather than gutting the content to hit the number.
- Both a video and an audio stream must be present.

Only run `publish` instead of `build` if the user **explicitly** asked to post
to Facebook. `publish` renders **and** posts live to the configured Page —
treat it as an outward-facing action to confirm first.

## Step 5: Report back

- The rows, paragraph and caption verbatim, so they can be reviewed without
  opening files.
- Relative markdown links to the draft `.md` and the rendered `.mp4`.
- The ffprobe numbers.
- Anything you changed from what the drafter produced, and why.
- Whether content was auto-drafted or hand-authored due to a missing API key.

If the user does publish, remind them once: **the first 60 minutes decide ~80%
of a post's reach**, so replying to comments in that window — and replying with
a question back — is the highest-value hour of the day.

## Known drift between this file and the code

Fix these in the draft file; don't work around them in the pipeline.

- `infrastructure/content/anthropic_drafter.py` asks for **6–8 vocab words**;
  the brand rule is **5**. Trim after drafting.
- The same prompt asks for **80–140 words** of paragraph at every level; that
  is too long for A1/A2 inside a 45-second video.
- It asks for **3–5 hashtags**; settle on **4** (3 fixed + 1 topical).
- It doesn't specify the caption's language; the caption must be **Vietnamese**.
- Formats `pronunciation` and `cuecard` appear in the handbook's frontmatter
  example but are **not implemented** — `LessonFormat.parse` rejects them.
