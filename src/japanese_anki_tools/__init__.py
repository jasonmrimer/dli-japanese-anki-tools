from aqt import mw
from aqt.qt import QAction, QCheckBox, QDialog, QVBoxLayout, QPushButton
from aqt.utils import showInfo, qconnect

from .filters import FilterModel, to_search


def create_filtered_deck() -> None:
    dialog = QDialog(mw)
    dialog.setWindowTitle("Japanese Anki Tools")

    layout = QVBoxLayout()

    l01_checkbox = QCheckBox("L01")
    layout.addWidget(l01_checkbox)

    create_button = QPushButton("CREATE")
    layout.addWidget(create_button)

    dialog.setLayout(layout)

    def create() -> None:
        model = FilterModel(
            include_l01=l01_checkbox.isChecked(),
        )

        try:
            search = to_search(model)
        except ValueError as error:
            showInfo(str(error))
            return

        deck_name = "L01"

        # Create the Filtered Deck.
        deck_id = mw.col.decks.new_filtered(deck_name)

        # Get the Filtered Deck configuration.
        filtered_deck = mw.col.sched.get_or_create_filtered_deck(deck_id)

        # Configure its search.
        filtered_deck.config.search_terms.clear()

        search_term = filtered_deck.config.search_terms.add()
        search_term.search = search
        search_term.limit = 100
        search_term.order = 0

        # Save the Filtered Deck.
        mw.col.sched.add_or_update_filtered_deck(filtered_deck)

        showInfo(
            f'Created Filtered Deck:\n\n"{deck_name}"\n\n'
            f"Search:\n{search}"
        )
        
    qconnect(create_button.clicked, create)

    dialog.exec()


action = QAction("Japanese Anki Tools", mw)
qconnect(action.triggered, create_filtered_deck)
mw.form.menuTools.addAction(action)