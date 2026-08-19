"""Drafts a lesson with Claude.

Implements `application.ports.LessonDrafter`. The model is asked for the same
markdown the repository stores, so its reply goes through the one parser the
rest of the system uses — a malformed reply fails here, not three steps later.
"""
from dataclasses import dataclass
from typing import Optional

import anthropic

from ...domain import CEFRLevel, Lesson
from . import markdown_format

DRAFT_PROMPT = """You are writing content for a Facebook page that teaches \
English vocabulary to students. Topic: "{topic}". CEFR level: {level}.

Produce EXACTLY this markdown structure, nothing before or after it:

## Vocabulary
- word — /IPA pronunciation/ — short simple definition (max 12 words)
(6 to 8 words, all naturally usable in a paragraph about the topic, all \
appropriate for {level} learners)

## Paragraph
(A natural, engaging paragraph, 80-140 words, appropriate for {level} \
readers, that uses ALL the vocabulary words above at least once. Bold each \
vocabulary word with **double asterisks** the first time it appears.)

## Caption
(A short, friendly Facebook caption, 1-2 sentences, with 3-5 relevant \
hashtags, inviting students to comment their own sentence using the new \
words. Mention the level, e.g. "Level: {level}".)
"""


@dataclass
class AnthropicDrafter:
    api_key: str
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 1200
    _client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def draft(self, topic: str, level: CEFRLevel) -> Lesson:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": DRAFT_PROMPT.format(topic=topic, level=level),
                }
            ],
        )
        body = "".join(
            block.text for block in response.content if block.type == "text"
        )
        # The model returns only the sections; the frontmatter is ours to add.
        document = f"---\ntopic: {topic}\nlevel: {level}\n---\n\n{body.strip()}\n"
        return markdown_format.parse(document, source="Claude's reply")
