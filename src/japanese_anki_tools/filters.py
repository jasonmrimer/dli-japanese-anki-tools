from dataclasses import dataclass

SOURCE_DECK = "Japanese 20566 Collab"


@dataclass
class FilterModel:
    tags: list[str]


def to_search(model: FilterModel) -> str:
    if not model.tags:
        raise ValueError("Select at least one tag.")

    tag_searches = [f'"tag:{tag}"' for tag in model.tags]

    return " OR ".join(tag_searches)