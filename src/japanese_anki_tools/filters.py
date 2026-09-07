from dataclasses import dataclass


SOURCE_DECK = "Japanese 20566 Collab"


STUDY_MODES = [
    ("Introduce", "introduce"),
    ("Review", "review"),
    ("Cram", "cram"),
]

MODALITIES = [
    ("Vocab", "Vocab"),
    ("Audio", "Audio"),
    ("Image", "Image"),
    ("Typing", "Typing"),
]

@dataclass
class FilterModel:
    jbc: bool
    sfj_lessons: list[str]
    tags: list[str]
    modalities: list[str]
    study_mode: str


def to_search(model: FilterModel) -> str:
    if model.tags:
        source_search = "(" + " OR ".join(
            f"tag:{tag}"
            for tag in model.tags
        ) + ")"

    else:
        source_parts = []

        if model.jbc:
            source_parts.append(
                f'"deck:{SOURCE_DECK}::JBC"'
            )

        if model.sfj_lessons:
            sfj_search = " OR ".join(
                f"tag:{lesson}"
                for lesson in model.sfj_lessons
            )

            source_parts.append(
                f'("deck:{SOURCE_DECK}::SFJ" ({sfj_search}))'
            )

        if not source_parts:
            raise ValueError(
                "Select at least one deck or lesson."
            )

        source_search = "(" + " OR ".join(source_parts) + ")"

    if not model.modalities:
        raise ValueError(
            "Select at least one modality."
        )

    modality_parts = []

    for modality in model.modalities:
        if modality == "Audio":
            modality_parts.append("(card:Audio Audio:_*)")
        elif modality == "Image":
            modality_parts.append("(card:Image Image:_*)")
        else:
            modality_parts.append(f"card:{modality}")

    modality_search = "(" + " OR ".join(modality_parts) + ")"

    search_parts = [
        f'"deck:{SOURCE_DECK}"',
        source_search,
        modality_search,
    ]

    if model.study_mode == "introduce":
        search_parts.append("(is:new OR is:learn)")
    elif model.study_mode == "review":
        search_parts.append("(is:learn OR is:due)")
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