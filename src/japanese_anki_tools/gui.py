from aqt import mw
from aqt.qt import (
    QAction,
    QCheckBox,
    QDialog,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showInfo, qconnect

from .filters import FilterModel, SOURCE_DECK, to_search


def get_deck_tags() -> list[str]:
    """Return all tags used by notes in the source deck."""

    card_ids = mw.col.find_cards(f'"deck:{SOURCE_DECK}"')

    tags: set[str] = set()

    for card_id in card_ids:
        card = mw.col.get_card(card_id)
        tags.update(card.note().tags)

    return sorted(tags, key=str.casefold)


def create_tag_checkboxes(tags: list[str]) -> list[QCheckBox]:
    """Create a checkbox for each tag."""

    checkboxes: list[QCheckBox] = []

    for tag in tags:
        checkbox = QCheckBox(tag)
        checkboxes.append(checkbox)

    return checkboxes


def create_tag_list_widget(
    checkboxes: list[QCheckBox],
) -> QScrollArea:
    """Create the scrollable widget containing the tag checkboxes."""

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    tag_widget = QWidget()
    tag_layout = QVBoxLayout()

    for checkbox in checkboxes:
        tag_layout.addWidget(checkbox)

    tag_widget.setLayout(tag_layout)
    scroll_area.setWidget(tag_widget)

    return scroll_area


def select_all_tags(checkboxes: list[QCheckBox]) -> None:
    """Select every tag."""

    for checkbox in checkboxes:
        checkbox.setChecked(True)


def clear_all_tags(checkboxes: list[QCheckBox]) -> None:
    """Clear every tag selection."""

    for checkbox in checkboxes:
        checkbox.setChecked(False)


def get_selected_tags(checkboxes: list[QCheckBox]) -> list[str]:
    """Return the tags currently selected by the user."""

    return [
        checkbox.text()
        for checkbox in checkboxes
        if checkbox.isChecked()
    ]


def validate_deck_name(deck_name: str) -> bool:
    """Validate that the requested deck name is usable."""

    if not deck_name:
        showInfo("Enter a name for the Filtered Deck.")
        return False

    existing_deck = next(
        (
            deck_info
            for deck_info in mw.col.decks.all_names_and_ids(
                include_filtered=True
            )
            if deck_info.name == deck_name
        ),
        None,
    )

    if existing_deck is not None:
        if mw.col.decks.is_filtered(existing_deck.id):
            showInfo(
                f'A Filtered Deck named "{deck_name}" already exists.\n\n'
                "Please choose a different name."
            )
        else:
            showInfo(
                f'A regular deck named "{deck_name}" already exists.\n\n'
                "Please choose a different name."
            )

        return False

    return True


def create_filtered_deck_in_anki(
    deck_name: str,
    search: str,
) -> None:
    """Create and configure the Filtered Deck in Anki."""

    deck_id = mw.col.decks.new_filtered(deck_name)

    filtered_deck = mw.col.sched.get_or_create_filtered_deck(deck_id)

    filtered_deck.config.search_terms.clear()

    search_term = filtered_deck.config.search_terms.add()
    search_term.search = search
    search_term.limit = 100
    search_term.order = 0

    mw.col.sched.add_or_update_filtered_deck(filtered_deck)

def refresh_deck_browser() -> None:
    """Refresh Anki's deck list."""

    mw.deckBrowser.refresh()

def create_filtered_deck() -> None:
    """Display the Filtered Deck creation dialog."""

    dialog = QDialog(mw)
    dialog.setWindowTitle("Japanese Anki Tools")

    layout = QVBoxLayout()

    # Deck name.
    deck_name_input = QLineEdit()
    deck_name_input.setPlaceholderText("Enter Filtered Deck name")
    layout.addWidget(deck_name_input)

    # Tags.
    tags = get_deck_tags()
    tag_checkboxes = create_tag_checkboxes(tags)
    tag_list = create_tag_list_widget(tag_checkboxes)
    layout.addWidget(tag_list)

    # Tag selection controls.
    select_all_button = QPushButton("Select All")
    clear_all_button = QPushButton("Clear All")

    layout.addWidget(select_all_button)
    layout.addWidget(clear_all_button)

    qconnect(
        select_all_button.clicked,
        lambda: select_all_tags(tag_checkboxes),
    )

    qconnect(
        clear_all_button.clicked,
        lambda: clear_all_tags(tag_checkboxes),
    )

    # Create button.
    create_button = QPushButton("CREATE")
    layout.addWidget(create_button)

    dialog.setLayout(layout)

    def create() -> None:
        selected_tags = get_selected_tags(tag_checkboxes)

        model = FilterModel(tags=selected_tags)

        try:
            search = to_search(model)
        except ValueError as error:
            showInfo(str(error))
            return

        deck_name = deck_name_input.text().strip()

        if not validate_deck_name(deck_name):
            return

        create_filtered_deck_in_anki(deck_name, search)

        refresh_deck_browser()

        dialog.accept()

        showInfo(
            f'Created Filtered Deck:\n\n"{deck_name}"\n\n'
            f"Search:\n{search}"
        )

    qconnect(create_button.clicked, create)

    dialog.exec()


def setup() -> None:
    """Add the Japanese Anki Tools menu item."""

    old_action = getattr(mw, "_japanese_anki_tools_action", None)

    if old_action is not None:
        mw.form.menuTools.removeAction(old_action)
        old_action.deleteLater()

    action = QAction("Japanese Anki Tools", mw)
    qconnect(action.triggered, create_filtered_deck)
    mw.form.menuTools.addAction(action)

    mw._japanese_anki_tools_action = action