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


class Duo:
    """Read learned words and their data from Duolingo"""

    def __init__(self, mw):
        self.cookies = cookies

        self.headers =  {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
        self.mw = mw

    def learned_words(self):
        website = requests.get("https://www.duolingo.com/vocabulary/overview?", cookies=self.cookies, headers=self.headers).text
        # print(json.dumps(json.loads(website), indent=2))
        words = json.loads(website)

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
                selected_deck_id = mw.col.decks.id("Duolingo Russisch Alternative_forms")
                mw.col.decks.select(selected_deck_id)
                model = mw.col.models.by_name("Duo Alternative_forms")
                deck = mw.col.decks.get(selected_deck_id)
                deck['mid'] = model['id']
                mw.col.decks.save(deck)
                model['did'] = selected_deck_id
                mw.col.models.save(model)
                # Create notes for alternative forms
                for form in detail["alternative_forms"]:
                    continue

                    note = mw.col.newNote()
                    md5=hashlib.md5(str(form).encode('utf-8')).hexdigest()

                    for field, value in form.items():
                        note[field] = str(value)

                    note["parent lexeme_id"] = str(detail["lexeme_id"])
                    note["parent learning_language"] = str(detail["learning_language"])
                    note["parent from_language"] = str(detail["from_language"])
                    note["md5"]=md5
                    if form["tts"]:
                        try:
                            audio_path = os.path.join(MEDIA_FOLDER, f"duolingo-{detail['from_language']}-alternative-form-{md5}.ogg")
                            with open(audio_path, "wb") as file:
                                file.write(loadurl(form["tts"]).content)
                                note["Audio"] = f"[sound:duolingo-{detail['from_language']}-alternative-form-{md5}.ogg]"

                        except Exception as e:
                            print(e)

                    mw.col.addNote(note)

                # Create the new notes
                # Set the right deck (according to how common the word is) and model
                selected_deck_id = mw.col.decks.id("Duolingo Russisch")
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
                note["translations line break"] =  "<br><br>".join(ens)

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

                """            
                                            for (name, value) in note.items():
                                                if name in fields:
                                                    note[name] = fields[name]
                                            mw.col.addNote(note)
                                            for card in note.cards():
                                                card.queue = anki.consts.QUEUE_TYPE_SUSPENDED
                                                card.flush()
                """
                tooltip("All words imported!")

                continue
                # test creating one card
                try:
                    audio_path = os.path.join(MEDIA_FOLDER, f"cambridge-{scrubbed}.ogg")
                    with open(audio_path, "wb") as file:
                        file.write(load_url(audio_url, True).content)
                        fields["Audio"] = f'[sound:cambridge-{scrubbed}.ogg]'

                except Exception as e:
                    print(e)


if not is_anki:
    print("fsfd")
    duo = Duo(mw)
    duo.learned_words()

"""website = requests.get("https://www.duolingo.com/api/1/dictionary_page?lexeme_id=5f514739434d886930fb8ff6fd6c312a&use_cache=false&from_language_id=en", cookies=duo.cookies,
                       headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'})
# print(json.dumps(json.loads(website.text), indent=2))
"""
