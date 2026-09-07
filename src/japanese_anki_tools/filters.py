from dataclasses import dataclass


SOURCE_DECK = "Japanese 20566 Collab"


STUDY_MODES = [
    ("Introduce", "introduce"),
    ("Review", "review"),
    ("Cram", "cram"),
]


@dataclass
class FilterModel:
    sfj_lessons: list[str]
    tags: list[str]
    study_mode: str


def to_search(model: FilterModel) -> str:
    if not model.sfj_lessons:
        raise ValueError("Select at least one SFJ lesson.")

    if not model.tags:
        raise ValueError("Select at least one tag.")

    sfj_search = " OR ".join(
        f"tag:{lesson}"
        for lesson in model.sfj_lessons
    )

    sfj_ingredient = (
        f'"deck:{SOURCE_DECK}::SFJ" '
        f"({sfj_search})"
    )

    tag_search = " OR ".join(
        f'"tag:{tag}"'
        for tag in model.tags
    )

    deck_search = f'"deck:{SOURCE_DECK}"'

    if model.study_mode == "introduce":
        status_search = "(is:new OR is:learn)"
    elif model.study_mode == "review":
        status_search = "is:review is:due"
    elif model.study_mode == "cram":
        status_search = ""
    else:
        raise ValueError("Select a valid study mode.")

    search_parts = [
        f'"deck:{SOURCE_DECK}"',
        f"({sfj_ingredient})",
    ]

    if status_search:
        search_parts.append(status_search)

    return " ".join(search_parts)


def should_reschedule(study_mode: str) -> bool:
    """Return whether Anki should update card scheduling."""

    if study_mode == "cram":
        return False

    return True