import sys
from dataclasses import dataclass
from anki import consts
from .private import cookies

is_anki = True
if is_anki:
    from .duo_utils import *
    from .constants import *
else:
    from duo_utils import *
    from constants import *

from aqt import mw
from aqt import gui_hooks
import anki.consts
from aqt.utils import showInfo, tooltip
import hashlib

"""
Fragen:
-Wachsen die alternative_forms mit den fortschreitenden Fähigkeiten-niveaus?  

"""


@dataclass
class Sentence:
    text: str
    translation: str
    words: [str]
    md5: str
    occurrences: int
    score: float = 0

    def known_score(self):
        self.score = self.occurrences / len(self.text.split(" "))
        return self.score


class Duo:
    """Read learned words and their data from Duolingo"""
    sentence_ocurrences: dict[str, Sentence] = {}
    WORDS_DECK_NAME: str
    SENTENCES_DECK_NAME: str

    def __init__(self, mw):
        self.cookies = cookies

        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
        self.mw = mw

    def log_sentence_occurence(self, text, translation, word):
        md5 = hashlib.md5(str([text, translation]).encode('utf-8')).hexdigest()
        if md5 in self.sentence_ocurrences:
            self.sentence_ocurrences[md5].occurrences += 1
            self.sentence_ocurrences[md5].words.append(word)
        else:
            self.sentence_ocurrences[md5] = Sentence(text, translation, [word], md5, 1, 0)

    def get_sentence_occurrences(self, md5):
        if md5 in self.sentence_ocurrences:
            return self.sentence_ocurrences[md5]
        else:
            print("A sentence does not have any occurrences after card updating!")
            print("Sentence: " + md5)
            return Sentence(occurrences=-1, md5="md5", score=-1, text="Unknown", translation="Unknown", words=[])

    def learned_words(self):
        website = requests.get("https://www.duolingo.com/vocabulary/overview?", cookies=self.cookies, headers=self.headers).text
        # print(json.dumps(json.loads(website), indent=2))
        words = json.loads(website)
        self.WORDS_DECK_NAME = f'Duolingo Words::Duolingo {words["language_string"]}'
        self.SENTENCES_DECK_NAME = f'Duolingo {words["language_string"]} Alternative_forms'
        print("Language: " + words["language_string"])
        # get already imported words
        imported_words_ids = [mw.col.get_note(note_id)["id"] for note_id in mw.col.find_notes(f'"deck:{self.WORDS_DECK_NAME}"')]
        imported_sentences_md5_hashes = [mw.col.get_note(note_id)["md5"] for note_id in mw.col.find_notes(f'"deck:{self.SENTENCES_DECK_NAME}"')]
        # print (imported_sentences_md5_hashes)

        for word in words["vocab_overview"]:

            print(word["normalized_string"])

            # load word details
            detail = loadurl("https://www.duolingo.com/api/1/dictionary_page?lexeme_id=%id&use_cache=false&from_language_id=en".replace("%id", word["id"]), cookies=self.cookies, headerstosend=self.headers, silent=False)
            detail = json.loads(detail.text)
            tts = loadurl(detail["tts"], cookies=self.cookies, headerstosend=self.headers, silent=False)

            # create note

            # sort english meanings by Häufigkeit
            ens = detail["translations"].split(", ")
            ens = sorted(ens, key=lambda x: get_phrasefinder(x), reverse=True)
            print(ens)

            if is_anki:
                # Set the right deck (according to how common the word is) and model
                selected_deck_id = mw.col.decks.id(self.SENTENCES_DECK_NAME)
                mw.col.decks.select(selected_deck_id)
                model = mw.col.models.by_name("Duo Alternative_forms")
                deck = mw.col.decks.get(selected_deck_id)
                deck['mid'] = model['id']
                mw.col.decks.save(deck)
                model['did'] = selected_deck_id
                mw.col.models.save(model)
                # Create notes for alternative forms
                for form in detail["alternative_forms"]:
                    self.log_sentence_occurence(form["text"], form["translation_text"], word["word_string"])
                    md5 = hashlib.md5(str([form["text"], form["translation_text"]]).encode('utf-8')).hexdigest()
                    if md5 in imported_sentences_md5_hashes:
                        print(f"skipping sentence, it has already been imported (md5:{md5})")
                        continue
                    imported_sentences_md5_hashes.append(md5)

                    note = mw.col.newNote()

                    for field, value in form.items():
                        note[field] = str(value)

                    note["parent lexeme_id"] = str(detail["lexeme_id"])
                    note["parent learning_language"] = str(detail["learning_language"])
                    note["parent from_language"] = str(detail["from_language"])
                    note["md5"] = md5
                    if form["tts"]:
                        try:
                            audio_path = os.path.join(MEDIA_FOLDER, f"duolingo-{detail['learning_language']}-alternative-form-{md5}.mp3")
                            with open(audio_path, "wb") as file:
                                file.write(loadurl(form["tts"]).content)
                                note["Audio"] = f"[sound:duolingo-{detail['learning_language']}-alternative-form-{md5}.mp3]"

                        except Exception as e:
                            print(e)

                    mw.col.addNote(note)
                if word["id"] in imported_words_ids:
                    print(f"skipping word, it has already been imported (id:{word['id']})")
                    continue

                # Create the new notes
                selected_deck_id = mw.col.decks.id(self.WORDS_DECK_NAME)
                mw.col.decks.select(selected_deck_id)
                model = mw.col.models.by_name("Duo Russisch")
                deck = mw.col.decks.get(selected_deck_id)
                deck['mid'] = model['id']
                mw.col.decks.save(deck)
                model['did'] = selected_deck_id
                mw.col.models.save(model)

                note = mw.col.newNote()

                note["word"] = detail["word"]
                note["translations sorted"] = ", ".join(ens)
                note["translations original"] = detail["translations"]
                note["translations line break"] = "<br><br>".join(ens)

                note["id"] = str(word["id"])
                note["lexeme_id"] = str(detail["lexeme_id"])
                note["learning_language"] = str(detail["learning_language"])
                note["skill"] = str(word["skill"])
                note["infinitive"] = str(detail["infinitive"])
                note["related_lexemes"] = str(detail["related_lexemes"])
                note["normalized_string"] = str(word["normalized_string"])
                note["pos"] = str(word["pos"])
                note["from_language"] = str(detail["from_language"])
                note["related_discussions"] = str(detail["related_discussions"])
                note["is_generic"] = str(detail["is_generic"])
                note["tts"] = str(detail["tts"])
                note["lexeme_image"] = str(detail["lexeme_image"])
                note["canonical_path"] = str(detail["canonical_path"])
                note["gender"] = str(word["gender"])

                if detail["tts"]:
                    try:
                        audio_path = os.path.join(MEDIA_FOLDER, f"duolingo-{detail['from_language']}-{detail['lexeme_id']}.ogg")
                        with open(audio_path, "wb") as file:
                            file.write(loadurl(detail["tts"]).content)
                            note["Audio"] = f"[sound:duolingo-{detail['from_language']}-{detail['lexeme_id']}.ogg]"

                    except Exception as e:
                        print(e)

                if detail["lexeme_image"]:
                    try:
                        image_path = os.path.join(MEDIA_FOLDER, f"duolingo-{detail['from_language']}-{detail['lexeme_id']}.svg")
                        with open(image_path, "wb") as file:
                            file.write(loadurl(detail["lexeme_image"]).content)
                            note["Image"] = f"[sound:duolingo-{detail['from_language']}-{detail['lexeme_id']}.svg]"

                    except Exception as e:
                        print(e)
                        break

                mw.col.addNote(note)

                tooltip("All words imported!")

        with open("/home/robin/.local/share/Anki2/addons21/duolingo import/ranked by score.json", "w+", encoding="utf-8") as file:
            file.write(json.dumps([x.__dict__ for x in sorted(self.sentence_ocurrences.values(), key=lambda x: x.known_score(), reverse=True)], indent=2))
        with open("/home/robin/.local/share/Anki2/addons21/duolingo import/ranked by occurrences.json", "w+", encoding="utf-8") as file:
            file.write(json.dumps([x.__dict__ for x in sorted(self.sentence_ocurrences.values(), key=lambda x: x.occurrences, reverse=True)], indent=2))
        print(json.dumps([x.__dict__ for x in sorted(self.sentence_ocurrences.values(), key=lambda x: x.known_score(), reverse=True)[:100]], indent=2))
        self.update_occurrences()
        self.sentence_ocurrences = {}

        # update information on occurrences in notes

    def update_occurrences(self):
        """Delay new cards for a few days (with specific settings for different decks) and activate them again after the specified time has passed"""

        all_notes = mw.col.find_notes(f'"deck:{self.SENTENCES_DECK_NAME}"')

        for note_id in all_notes:
            note = mw.col.get_note(note_id)
            note_occurrences = note["sentence_occurrences"]
            try:
                note_occurrences = int(note_occurrences)
            except:
                note_occurrences = -1
            current_occurrences = self.get_sentence_occurrences(note["md5"]).occurrences
            if current_occurrences != note_occurrences:

                print(f'{note_occurrences} occurrences for sentence {note["md5"]} ({note["text"]}) saved in card, {current_occurrences} found in Duolingo data')
                print("Updating note and enabling its cards")

                note["sentence_occurrences"] = str(current_occurrences)
                note.flush()

                for card in note.cards():
                    if card.queue == anki.consts.QUEUE_TYPE_SUSPENDED:
                        #  Reset the card to 'new'
                        #  I copied the card parameters to be reset from AnkiConnect's forgetCard() function: collection().db.execute('update cards set type=0, queue=0, left=0, ivl=0, due=0, odue=0, factor=0 where id in ' + scids)
                        card.queue = anki.consts.QUEUE_TYPE_NEW
                        card.due = 0
                        card.ivl = 0
                        card.odue = 0
                        card.type = anki.consts.CARD_TYPE_NEW
                        card.factor = 0
                        card.left = 0
                        card.flush()
                        print(f'Enabled card id {card.id} ({note["text"]})')


if not is_anki:
    print("this is not running in anki")
    duo = Duo(mw)
    duo.learned_words()
