"""Keeps the taught-word history in Firestore.

Implements `application.ports.VocabularyLedger`. The drafts folder already
records this history (see `draft_folder.py`); Firestore makes it outlive one
machine's `drafts/`, which is gitignored and therefore local only.

Credentials are a path read from the environment — the service-account file
stays wherever it lives and nothing about it is stored in this repository.
"""
from dataclasses import dataclass, field
from typing import Optional, Set

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from ...application.ports import DraftRef
from ...domain import CEFRLevel, Lesson
from .draft_folder import normalise_topic

COLLECTION = "taught_vocabulary"


@dataclass
class FirestoreVocabularyLedger:
    credentials_path: str
    collection: str = COLLECTION
    _client: Optional[firestore.Client] = field(default=None, repr=False)

    @property
    def client(self) -> firestore.Client:
        if self._client is None:
            self._client = firestore.Client.from_service_account_json(
                self.credentials_path
            )
        return self._client

    def taught(self, topic: str, level: CEFRLevel) -> Set[str]:
        query = (
            self.client.collection(self.collection)
            .where(filter=FieldFilter("topic_key", "==", normalise_topic(topic)))
            .where(filter=FieldFilter("level", "==", str(level)))
        )
        words: Set[str] = set()
        for document in query.stream():
            words.update(document.to_dict().get("words", ()))
        return words

    def record(self, lesson: Lesson, ref: DraftRef) -> None:
        words = [entry.word.strip() for entry in lesson.vocab if entry.word.strip()]
        if not words:
            return
        # The draft's basename is unique per lesson and already carries topic,
        # level and minute, so re-running a draft updates its row instead of
        # piling up duplicates.
        self.client.collection(self.collection).document(ref.basename).set(
            {
                "topic": lesson.topic,
                "topic_key": normalise_topic(lesson.topic),
                "level": str(lesson.level),
                "format": str(lesson.format),
                "words": words,
                "draft": ref.basename,
                "recorded_at": firestore.SERVER_TIMESTAMP,
            }
        )
