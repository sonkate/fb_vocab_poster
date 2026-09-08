from fb_vocab_poster.domain import (
    CEFRLevel,
    HOOK,
    Lesson,
    LessonFormat,
    VocabEntry,
    build_audio_plan,
)


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


def test_every_plan_opens_with_a_spoken_hook_cue():
    """The hook is spoken too — muted autoplay is 85-90% of feed views, but
    the rest still need to hear it, not just see it."""
    plan = build_audio_plan(lesson())

    assert plan[0].kind == HOOK
    assert plan[0].text == lesson().spec.default_hook
    assert plan[0].clip_name == "hook"


def test_build_audio_plan_repeats_each_vocab_word_before_paragraph():
    plan = build_audio_plan(lesson())[1:]   # [0] is the hook, covered above

    assert [cue.kind for cue in plan] == ["word", "word", "word", "word", "paragraph"]
    assert [cue.text for cue in plan[:4]] == ["hello", "hello", "world", "world"]
    assert plan[-1].text == "Hello world is a friendly phrase."


def test_each_word_is_spoken_slowly_then_at_normal_speed():
    plan = build_audio_plan(lesson())[1:]

    assert [cue.slow for cue in plan[:4]] == [True, False, True, False]
    assert plan[-1].slow is False


def test_clip_names_are_stable_and_unique_per_cue():
    names = [cue.clip_name for cue in build_audio_plan(lesson())[1:]]

    assert names == [
        "word_0_slow",
        "word_0_normal",
        "word_1_slow",
        "word_1_normal",
        "paragraph",
    ]


def mistake_lesson() -> Lesson:
    return Lesson(
        topic="Common slips",
        level=CEFRLevel.B1,
        format=LessonFormat.MISTAKE,
        vocab=(
            VocabEntry("I very **like** it.", "I **really** like it.", "why 1"),
            VocabEntry("She **go** home.", "She **goes** home.", "why 2"),
        ),
    )


def test_a_contrast_row_speaks_both_the_wrong_and_the_right_sentence_stripped_of_markup():
    """The wrong sentence is worth hearing too — a buzzer and an on-screen
    SAI tag mark it as wrong the instant it's heard — so both halves of every
    row are read, in order, with their `**` markers stripped before TTS."""
    plan = build_audio_plan(mistake_lesson())[1:]   # [0] is the hook

    assert [cue.text for cue in plan] == [
        "I very like it.",
        "I really like it.",
        "She go home.",
        "She goes home.",
    ]
    assert [cue.role for cue in plan] == ["wrong", "right", "wrong", "right"]


def test_contrast_row_clip_names_are_stable_and_unique_per_cue():
    names = [cue.clip_name for cue in build_audio_plan(mistake_lesson())[1:]]

    assert names == ["mistake_0_wrong", "mistake_0_right", "mistake_1_wrong", "mistake_1_right"]


def upgrade_lesson() -> Lesson:
    return Lesson(
        topic="Small talk",
        level=CEFRLevel.B1,
        format=LessonFormat.UPGRADE,
        vocab=(VocabEntry("very tired", "exhausted", "Band 5 -> 7.5, same idea"),),
    )


def test_upgrade_also_runs_the_before_after_rhythm_speaking_both_halves():
    """`upgrade` shares the same generic contrast-rhythm plan as `mistake` —
    both the weak and the strong phrase get read, in order."""
    plan = build_audio_plan(upgrade_lesson())[1:]   # [0] is the hook

    assert [cue.text for cue in plan] == ["very tired", "exhausted"]
    assert [cue.role for cue in plan] == ["wrong", "right"]
