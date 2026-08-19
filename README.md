# FB Vocab Poster — prototype

Draft → review → auto-record voice → auto-build video → post to your
Facebook Page. One topic + one CEFR level per post.

## Stack (and why)

- **Python** — fastest to prototype media pipelines + has a good FB SDK story via `requests`.
- **Clean architecture** — the pieces most likely to be replaced (TTS engine, social platform, drafting model) sit behind interfaces, so replacing one doesn't ripple.
- **Claude (Anthropic API)** — drafts the paragraph + vocab list + caption from a topic/level. You review and edit before anything goes out.
- **gTTS** — free Google Translate TTS for narration. Robotic but $0 and zero setup. Swap-in point noted below if you want a natural voice later.
- **Pillow + moviepy** — draws simple text slides (title / vocab / paragraph) and stitches them into an MP4 synced to the narration length. No video editing skill needed, no ImageMagick dependency.
- **Facebook Graph API** (`graph-video.facebook.com/.../videos`) — direct HTTP upload, no heavy SDK.

## Architecture

The code is organised in clean-architecture layers. Dependencies point inwards
only — `domain` knows about nobody, and nothing inside `application` knows
which TTS engine or social network is in use.

```
fb_vocab_poster/
  domain/                 pure rules, standard library only
    lesson.py             Lesson, VocabEntry, which words to highlight
    level.py              CEFRLevel
    narration.py          what gets spoken, in what order, at what pace
    slides.py             which slides exist and how long each holds
    naming.py             the topic_level_timestamp filename convention
  application/
    ports.py              the interfaces adapters must satisfy
    use_cases/            draft_lesson, render_lesson, publish_lesson
  infrastructure/         one adapter per port, all the messy outside world
    config/               Settings (.env), FileSystemWorkspace, SystemClock
    content/              Claude drafter, blank-template drafter, markdown store
    audio/                gTTS synthesiser, moviepy narration composer
    video/                Theme, Pillow slide painter, moviepy renderer
    publishing/           Facebook Graph API publisher
  interface/
    cli.py                argv in, use case out
    console.py            the only module that prints
  container.py            composition root — the one place adapters are chosen
main.py                   entry point, delegates to interface/cli.py
```

Two rules keep this honest, and both are worth preserving as you extend it:

- **The domain never imports a library.** Pacing, ordering and highlighting are
  decided in `domain/` with no Pillow, moviepy, HTTP or filesystem in sight,
  which is why those rules are testable in milliseconds.
- **Adapters are chosen once, in `container.py`.** Nothing else constructs a
  gTTS client or a Facebook publisher, so swapping one is a single-line change.

## Tests

```bash
pytest
```

The suite covers the domain rules and drives all three use cases through fake
adapters, so it needs no API keys, no network and no ffmpeg.

## 1. Install

```bash
cd fb-vocab-poster
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
- `ANTHROPIC_API_KEY` — optional. Get one at console.anthropic.com (Settings →
  API Keys). The API is pay-per-token with no permanent free tier — new
  accounts get a small one-time trial credit. **If you leave this blank**,
  `python main.py draft` writes a blank template instead of an AI draft; you
  can then paste in content from a free claude.ai chat by hand and edit
  normally. Same file format either way.
- `FB_PAGE_ACCESS_TOKEN` / `FB_PAGE_ID` — see below

## 2. Facebook setup (one-time)

1. Create a Facebook App at developers.facebook.com (type: "Business").
2. Add the **Pages API** product.
3. In Graph API Explorer: select your app, select your Page, request
   permissions `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`,
   generate a **User** token, then exchange it for a **Page** token
   (Graph API Explorer has a "Get Page Access Token" step, or call
   `GET /me/accounts` with the user token — it returns each Page's own token).
4. That Page token is short-lived by default. Exchange it for a long-lived
   one (~60 days):
   `GET /oauth/access_token?grant_type=fb_exchange_token&client_id=...&client_secret=...&fb_exchange_token=<short_token>`
5. Put the resulting Page token in `.env` as `FB_PAGE_ACCESS_TOKEN`, and the
   Page's numeric ID as `FB_PAGE_ID`.

Note: Facebook periodically reviews apps that post video automatically —
for personal/small-scale use this generally runs in dev mode against your
own Page without app review, but check current Graph API terms if you plan
to scale this to many pages.

## 3. Run the pipeline

```bash
# 1. Generate a draft (AI writes it, you review/edit before it goes out)
python main.py draft "Ordering coffee" B1

# -> writes drafts/ordering-coffee_B1_<timestamp>.md
# Open that file. Edit the vocab words, paragraph, or caption freely.
# The format is plain markdown with ## Vocabulary / ## Paragraph / ## Caption.

# 2. Preview the rendered video WITHOUT posting
python main.py build drafts/ordering-coffee_B1_<timestamp>.md
# -> output/ordering-coffee_B1_<timestamp>.mp4 — watch it locally

# 3. Happy with it? Post it for real
python main.py publish drafts/ordering-coffee_B1_<timestamp>.md
```

`build` and `publish` both regenerate audio+video from whatever is
currently in the `.md` file, so your edits always take effect.

## What you'll actually see

- A title slide (topic + level)
- A vocabulary slide (word, IPA, short meaning)
- 2–4 "read along" slides with the paragraph, synced to narration length
- One MP4, one caption, posted as a native video on your Page

## What to extend first

Roughly in the order I'd tackle them:

1. **Human approval gate for posting, not just content** — right now `publish` posts immediately once you run it. If multiple people run this, add a simple "approved: yes/no" field in the draft frontmatter that `publish` checks.
2. **Better visuals** — swap the plain-color background for topic-relevant stock/generated images per slide. `infrastructure/video/slide_painter.py` draws every slide onto a canvas from `_canvas()`; load an image there instead of a solid fill, and adjust `Theme` in `theme.py` to match.
3. **Natural voice** — write a class with a single `synthesize(cue, out_path)` method against ElevenLabs or Azure Neural TTS, and swap it in `container.py`. Nothing else changes: it satisfies the same `SpeechSynthesizer` port gTTS does.
4. **Scheduling** — wrap `main.py publish` in a cron job / GitHub Action that pulls the next unpublished draft from `drafts/` on a schedule (e.g. daily 9am), instead of running by hand.
5. **Topic queue** — instead of typing one topic at a time, loop the `DraftLesson` use case over a CSV/sheet of topics+levels so you can batch-draft a week of content at once.
6. **Multi-platform** — the render step is already decoupled from publishing; adding Instagram/TikTok means one more class satisfying the `LessonPublisher` port, fed the same rendered MP4.
7. **Vocab reuse tracking** — store which words you've already covered (a simple JSON/CSV log behind a new port) and feed "avoid these" into the Claude prompt so posts don't repeat words.

## Known rough edges (it's a prototype)

- gTTS pacing is fixed; long paragraphs can feel rushed. Trim to ~100 words if it sounds fast.
- Facebook Graph API occasionally takes a minute to finish processing an
  uploaded video before it's visible on the Page — that's normal.
- No retry/backoff on the Facebook upload; add one before relying on this unattended.
