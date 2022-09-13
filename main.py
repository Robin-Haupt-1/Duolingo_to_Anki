import sys
from dataclasses import dataclass
from anki import consts

from .duo_utils import *
from .constants import *
from aqt import mw
from aqt import gui_hooks
import anki.consts
from aqt.utils import showInfo, tooltip
import hashlib


class Main:
    def __init__(self, mw):
        self.mw = mw

    def remove_nbsp(self):
        print("Removing &nbsp; from Begriffe...")
        all_notes = mw.col.find_notes(f'"deck:All::1) Sprachen::💬 Begriffe" &nbsp;')

        for note_id in all_notes:
            note = mw.col.get_note(note_id)
            for (name, value) in note.items():
                note[name] = value.replace("&nbsp;", " ")
            note.flush()

