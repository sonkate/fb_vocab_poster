from fb_vocab_poster.domain import CEFRLevel, Lesson, VocabEntry, build_audio_plan


def lesson() -> Lesson:
    return Lesson(
        topic="Greetings",
        level=CEFRLevel.B1,
        vocab=(
            VocabEntry(word="hello", ipa="/həˈloʊ/", meaning="greeting"),
            VocabEntry(word="world", ipa="/wɜːld/", meaning="earth"),
        ),
        paragraph="Hello world is a friendly phrase.",
    )


def test_build_audio_plan_repeats_each_vocab_word_before_paragraph():
    plan = build_audio_plan(lesson())

    assert [cue.kind for cue in plan] == ["word", "word", "word", "word", "paragraph"]
    assert [cue.text for cue in plan[:4]] == ["hello", "hello", "world", "world"]
    assert plan[-1].text == "Hello world is a friendly phrase."


def test_each_word_is_spoken_slowly_then_at_normal_speed():
    plan = build_audio_plan(lesson())

    assert [cue.slow for cue in plan[:4]] == [True, False, True, False]
    assert plan[-1].slow is False


def test_clip_names_are_stable_and_unique_per_cue():
    names = [cue.clip_name for cue in build_audio_plan(lesson())]

    assert names == [
        "word_0_slow",
        "word_0_normal",
        "word_1_slow",
        "word_1_normal",
        "paragraph",
    ]
