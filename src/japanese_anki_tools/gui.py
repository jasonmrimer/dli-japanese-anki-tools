from aqt import mw
from aqt.qt import Qt
from aqt.qt import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showInfo, qconnect

from .filters import (
    FilterModel,
    SOURCE_DECK,
    STUDY_MODES,
    MODALITIES,
    should_reschedule,
    to_search,
)

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


def create_study_mode_buttons() -> list[QRadioButton]:
    """Create radio buttons for the available study modes."""

    buttons: list[QRadioButton] = []

    for label, value in STUDY_MODES:
        button = QRadioButton(label)
        button.setProperty("study_mode_value", value)
        buttons.append(button)

    return buttons


def get_selected_study_mode(
    buttons: list[QRadioButton],
) -> str:
    """Return the selected study mode."""

    for button in buttons:
        if button.isChecked():
            return button.property("study_mode_value")

    raise ValueError("Select a study mode.")


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
    reschedule: bool,
) -> None:
    """Create and configure the Filtered Deck in Anki."""

    deck_id = mw.col.decks.new_filtered(deck_name)

    filtered_deck = mw.col.sched.get_or_create_filtered_deck(deck_id)

    filtered_deck.config.reschedule = reschedule
    filtered_deck.allow_empty = True

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
    dialog.setWindowTitle("DLI Tools")

    layout = QVBoxLayout()

    # Deck name.
    deck_name_input = QLineEdit()
    deck_name_input.setPlaceholderText("Enter Filtered Deck name")
    layout.addWidget(deck_name_input)

    # Study type.
    layout.addWidget(
        create_section_caption(
            "Study Type",
            "Choose how cards should be scheduled.",
        )
    )

    mode_buttons = create_study_mode_buttons()
    mode_buttons[0].setChecked(True)

    mode_layout = QHBoxLayout()

    for button in mode_buttons:
        mode_layout.addWidget(button)

    mode_layout.addStretch()

    layout.addLayout(mode_layout)
    layout.addSpacing(12)

    # Modalities.
    modality_panel = ModalityPanel()
    modalities_label = QLabel("Modalities")
    modalities_label.setStyleSheet("font-weight: bold;")

    layout.addWidget(modalities_label)
    layout.addWidget(modality_panel)

    # Deck selection.
    source_panel = SourcePanel()
    layout.addWidget(source_panel)

    # Manual tag override.
    all_tags_panel = AllTagsPanel()
    layout.addWidget(all_tags_panel)

    # Create button.
    create_button = QPushButton("CREATE")
    style_primary_button(create_button)
    layout.addWidget(create_button)

    dialog.setLayout(layout)

    def create() -> None:
        selected_tags = all_tags_panel.get_selected_tags()
        selected_sfj_lessons = source_panel.sfj_panel.get_selected_lessons()

        try:
            study_mode = get_selected_study_mode(mode_buttons)
        except ValueError as error:
            showInfo(str(error))
            return

        model = FilterModel(
            jbc=source_panel.jbc_checkbox.isChecked(),
            sfj_lessons=selected_sfj_lessons,
            tags=selected_tags,
            modalities=modality_panel.get_selected_modalities(),
            study_mode=study_mode,
        )

        try:
            search = to_search(model)
        except ValueError as error:
            showInfo(str(error))
            return

        deck_name = deck_name_input.text().strip()

        if not validate_deck_name(deck_name):
            return

        reschedule = should_reschedule(study_mode)

        create_filtered_deck_in_anki(
            deck_name,
            search,
            reschedule,
        )

        dialog.accept()

        refresh_deck_browser()

        showInfo(
            f'Created Filtered Deck:\n\n"{deck_name}"\n\n'
            # f"Search:\n{search}"
        )

    qconnect(create_button.clicked, create)

    dialog.exec()


def setup() -> None:
    """Add the Japanese Anki Tools menu item."""

    old_action = getattr(mw, "_japanese_anki_tools_action", None)

    if old_action is not None:
        mw.form.menuTools.removeAction(old_action)
        old_action.deleteLater()

    action = QAction("DLI Tools", mw)
    qconnect(action.triggered, create_filtered_deck)
    mw.form.menuTools.addAction(action)

    mw._japanese_anki_tools_action = action


class AllTagsPanel(QWidget):
    """Panel for manually selecting tags as an override."""

    def __init__(self) -> None:
        super().__init__()

        self.tags = get_deck_tags()
        self.checkboxes = create_tag_checkboxes(self.tags)

        layout = QVBoxLayout()

        self.toggle_button = QPushButton("Choose from all tags ▸")
        self.toggle_button.setStyleSheet(
            """
            QPushButton {
                border: none;
                background: transparent;
                color: palette(link);
                text-align: left;
                padding: 4px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
            """
        )
        layout.addWidget(self.toggle_button)

        self.selection_panel = QFrame()
        self.selection_panel.setFrameShape(QFrame.Shape.StyledPanel)

        selection_layout = QVBoxLayout()

        explanation = QLabel(
            "<b>Override:</b> Selecting tags here replaces the "
            "JBC/SFJ selections above."
        )
        explanation.setWordWrap(True)
        selection_layout.addWidget(explanation)

        tag_list = create_tag_list_widget(self.checkboxes)
        selection_layout.addWidget(tag_list)

        button_layout = QHBoxLayout()

        select_all_button = QPushButton("Select All")
        clear_all_button = QPushButton("Clear All")

        button_layout.addWidget(select_all_button)
        button_layout.addWidget(clear_all_button)
        button_layout.addStretch()

        selection_layout.addLayout(button_layout)

        self.selection_panel.setLayout(selection_layout)
        self.selection_panel.setVisible(False)

        layout.addWidget(self.selection_panel)

        self.setLayout(layout)

        qconnect(
            self.toggle_button.clicked,
            self.toggle,
        )

        qconnect(
            select_all_button.clicked,
            lambda: select_all_tags(self.checkboxes),
        )

        qconnect(
            clear_all_button.clicked,
            lambda: clear_all_tags(self.checkboxes),
        )

    def toggle(self) -> None:
        """Show or hide the manual tag selection."""

        visible = not self.selection_panel.isVisible()

        self.selection_panel.setVisible(visible)

        if visible:
            self.toggle_button.setText("Hide all tags ▾")
        else:
            self.toggle_button.setText("Choose from all tags ▸")

    def get_selected_tags(self) -> list[str]:
        """Return the manually selected tags."""

        return get_selected_tags(self.checkboxes)

    
class SFJPanel(QWidget):
    """Panel for selecting SFJ lessons."""

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()

        self.checkboxes: list[QCheckBox] = []

        # Study through control.
        through_layout = QHBoxLayout()

        through_label = QLabel("Study through:")

        self.through_combo = QComboBox()
        self.through_combo.addItem("None", None)

        for lesson_number in range(1, 25):
            lesson = f"L{lesson_number:02d}"
            self.through_combo.addItem(lesson, lesson_number)

        through_layout.addWidget(through_label)
        through_layout.addWidget(self.through_combo)

        layout.addLayout(through_layout)

        # Lesson list.
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        lesson_widget = QWidget()
        lesson_layout = QVBoxLayout()

        for lesson_number in range(1, 25):
            lesson = f"L{lesson_number:02d}"

            checkbox = QCheckBox(lesson)
            self.checkboxes.append(checkbox)
            lesson_layout.addWidget(checkbox)

        lesson_widget.setLayout(lesson_layout)
        scroll_area.setWidget(lesson_widget)

        layout.addWidget(scroll_area)

        self.setLayout(layout)

        qconnect(
            self.through_combo.currentIndexChanged,
            self.select_through,
        )

    def select_through(self) -> None:
        """Select all lessons through the chosen lesson."""

        through = self.through_combo.currentData()

        for lesson_number, checkbox in enumerate(self.checkboxes, start=1):
            checkbox.setChecked(
                through is not None and lesson_number <= through
            )

    def get_selected_lessons(self) -> list[str]:
        """Return the selected SFJ lessons."""

        return [
            checkbox.text()
            for checkbox in self.checkboxes
            if checkbox.isChecked()
        ]
    

class ModalityPanel(QWidget):
    """Panel for selecting card modalities."""

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.checkboxes: list[QCheckBox] = []

        for label, value in MODALITIES:
            checkbox = QCheckBox(label)
            checkbox.setProperty("modality_value", value)
            checkbox.setChecked(True)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        self.setLayout(layout)

    def get_selected_modalities(self) -> list[str]:
        """Return the selected modalities."""

        return [
            checkbox.property("modality_value")
            for checkbox in self.checkboxes
            if checkbox.isChecked()
        ]

    
class SourcePanel(QWidget):
    """Panel containing the JBC and SFJ selections."""

    def __init__(self) -> None:
        super().__init__()

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

       # JBC panel.
        jbc_widget = QWidget()
        jbc_layout = QVBoxLayout()
        jbc_layout.setContentsMargins(0, 0, 0, 0)

        self.jbc_checkbox = QCheckBox("Include all JBC cards")
        jbc_layout.addWidget(self.jbc_checkbox)

        jbc_widget.setLayout(jbc_layout)

        jbc_panel = create_subpanel("JBC", jbc_widget)
        layout.addWidget(jbc_panel)

        # SFJ panel.
        self.sfj_panel = SFJPanel()
        sfj_subpanel = create_subpanel("SFJ", self.sfj_panel)
        layout.addWidget(sfj_subpanel)

        self.setLayout(layout)


def create_subpanel(title: str, widget: QWidget) -> QWidget:
    """Create a titled panel containing a widget."""

    panel = QFrame()
    panel.setFrameShape(QFrame.Shape.StyledPanel)

    layout = QVBoxLayout()

    title_label = QLabel(title)
    title_label.setStyleSheet("font-weight: bold;")

    layout.addWidget(title_label)
    layout.addWidget(widget)
    layout.addStretch()

    panel.setLayout(layout)

    return panel


def style_primary_button(button: QPushButton) -> None:
    """Style a button as the primary action."""

    button.setStyleSheet(
        """
        QPushButton {
            background-color: #0078d4;
            color: white;
            font-weight: bold;
            padding: 8px 20px;
        }
        QPushButton:hover {
            background-color: #106ebe;
        }
        """
    )


def create_section_caption(
    title: str,
    description: str,
) -> QWidget:
    """Create a section title and description."""

    widget = QWidget()
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)

    title_label = QLabel(title)
    title_label.setStyleSheet("font-weight: bold;")

    description_label = QLabel(description)
    description_label.setStyleSheet(
        "font-size: 11px;"
    )
    description_label.setWordWrap(True)

    layout.addWidget(title_label)
    layout.addWidget(description_label)

    widget.setLayout(layout)

    return widget