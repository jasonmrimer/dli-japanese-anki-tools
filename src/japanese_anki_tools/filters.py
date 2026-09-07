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
    if model.tags:
        search_ingredient = "(" + " OR ".join(
            f"tag:{tag}"
            for tag in model.tags
        ) + ")"

    elif model.sfj_lessons:
        sfj_search = " OR ".join(
            f"tag:{lesson}"
            for lesson in model.sfj_lessons
        )

        search_ingredient = (
            f'("deck:{SOURCE_DECK}::SFJ" '
            f"({sfj_search}))"
        )

    else:
        raise ValueError(
            "Select at least one SFJ lesson or tag."
        )

    search_parts = [
        f'"deck:{SOURCE_DECK}"',
        search_ingredient,
    ]

    if model.study_mode == "introduce":
        search_parts.append("(is:new OR is:learn)")
    elif model.study_mode == "review":
        search_parts.append("is:review is:due")
    elif model.study_mode == "cram":
        pass
    else:
        raise ValueError("Select a valid study mode.")

    return " ".join(search_parts)


def should_reschedule(study_mode: str) -> bool:
    """Return whether Anki should update card scheduling."""

    if study_mode == "cram":
        return False

    return True