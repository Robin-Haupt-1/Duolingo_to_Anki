from aqt.qt import QAction
from aqt import gui_hooks

from .utils import *
from .duo import *
import_task = None
unsuspend_timer = None


def start_import():
    global import_task
    import_task = ImportEwFromCambridge()


def init():
    duo = Duo(mw)
    duo.learned_words()
    return
    # add menu option to import new cards
    options_action = QAction("Import from Cambridge ...", mw)
    options_action.triggered.connect(lambda _, o=mw: start_import())
    mw.form.menuTools.addAction(options_action)
    # add menu option to import new cards
    options_action = QAction("Update Tampermonkey list...", mw)
    options_action.triggered.connect(lambda _, o=mw: update_tampermonkey_list())
    mw.form.menuTools.addAction(options_action)
    # start timer to unsuspend new cards
    unsuspend_new_cards()
    global unsuspend_timer
    unsuspend_timer = mw.progress.timer(3600000, unsuspend_new_cards, True)
    update_tampermonkey_list()


gui_hooks.profile_did_open.append(lambda *args: init())
