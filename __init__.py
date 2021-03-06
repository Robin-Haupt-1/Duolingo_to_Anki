from aqt.qt import QAction
from aqt import gui_hooks

from .utils import *
from .duo import *


def init():
    duo = Duo(mw)
    duo.learned_words()
    return
    # add menu option to import new cards
    options_action = QAction("Import from Duolingo ...", mw)
    options_action.triggered.connect(lambda _, o=mw: start_import())
    mw.form.menuTools.addAction(options_action)


gui_hooks.profile_did_open.append(lambda *args: init())
