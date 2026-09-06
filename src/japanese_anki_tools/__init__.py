import importlib

from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect

from . import filters
from . import gui


def reload_addon() -> None:
    # Reload the modules in dependency order.
    importlib.reload(filters)
    importlib.reload(gui)

    # Rebuild the menu action.
    gui.setup()


gui.setup()

reload_action = QAction("Reload Japanese Anki Tools", mw)
qconnect(reload_action.triggered, reload_addon)
mw.form.menuTools.addAction(reload_action)