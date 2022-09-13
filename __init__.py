from aqt.qt import QAction
from aqt import gui_hooks

from .utils import *
from .main import Main


def init():
    main = Main(mw)
    # add menu option to import new cards
    options_action = QAction("Remove &nbsp; ...", mw)
    options_action.triggered.connect(lambda _, o=mw: main.remove_nbsp())
    gui_hooks.sync_will_start.append(lambda *args: main.remove_nbsp())

    mw.form.menuTools.addAction(options_action)
    main.remove_nbsp()


gui_hooks.profile_did_open.append(lambda *args: init())
