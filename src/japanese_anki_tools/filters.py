from dataclasses import dataclass


SOURCE_DECK = "Japanese 20566 Collab"


STUDY_MODES = [
    ("Introduce", "introduce"),
    ("Review", "review"),
    ("Cram", "cram"),
]


@dataclass
class FilterModel:
    tags: list[str]
    study_mode: str


def to_search(model: FilterModel) -> str:
    if not model.tags:
        raise ValueError("Select at least one tag.")

    tag_search = " OR ".join(
        f'"tag:{tag}"'
        for tag in model.tags
    )

    deck_search = f'"deck:{SOURCE_DECK}"'

    if model.study_mode == "introduce":
        status_search = "(is:new OR is:learn)"
        return f"{deck_search} ({tag_search}) {status_search}"

    if model.study_mode == "review":
        status_search = "is:review is:due"
        return f"{deck_search} ({tag_search}) {status_search}"

    if model.study_mode == "cram":
        return f"{deck_search} ({tag_search})"

    raise ValueError("Select a valid study mode.")


def should_reschedule(study_mode: str) -> bool:
    """Return whether Anki should update card scheduling."""

    if study_mode == "cram":
        return False

    return True