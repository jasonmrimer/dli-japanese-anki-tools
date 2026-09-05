from dataclasses import dataclass


SOURCE_DECK = "Japanese 20566 Collab::SFJ"
TAG = "L01"


@dataclass
class FilterModel:
    include_l01: bool


def to_search(model: FilterModel) -> str:
    if not model.include_l01:
        raise ValueError("L01 must be selected.")

    return f'"deck:{SOURCE_DECK}" "tag:{TAG}"'