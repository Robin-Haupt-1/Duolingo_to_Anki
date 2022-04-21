import requests
import re
import urllib.parse
import time
import socket
import os
import urllib.parse
import urllib.request
from .lib import termcolor
import datetime
from aqt import mw
import anki.consts
import json

import hashlib
import re

import requests
import pickle
from os import path

validfilenamechars = "¿,-_.()= äöüßÄÜÖabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя"
illegal_characters_in_file_names = r'"/\*?<>|:'


def chop_down_string_length(stringtochop, maxlength):
    if len(stringtochop) > maxlength:
        firstbitlenght = maxlength // 2
        choppedstring = stringtochop[:firstbitlenght] + stringtochop[-(maxlength - firstbitlenght):]
        return choppedstring
    return stringtochop


def string_to_filename(filename, raw=False):
    """if raw, will delete all illegal characters. Else will replace '?' with '¿' and all others with '-'"""
    if raw:
        return ''.join(c for c in filename if c not in illegal_characters_in_file_names)

    for x in [["?", "¿"]] + [[x, "-"] for x in illegal_characters_in_file_names if x != "?"]:
        filename = filename.replace(x[0], x[1])
    return filename


def replace_multiple_strings_with_the_same(original_string, strings_to_replace, replacement_string, ignore_case=True):
    new_string = original_string
    for x in strings_to_replace:
        new_string = new_string.replace(x, replacement_string) if not ignore_case else re.sub(x, replacement_string,
                                                                                              new_string,
                                                                                              flags=re.IGNORECASE)
    return new_string


def replace_multiple_strings_with_the_same_case_insensitive(original_string, strings_to_replace, replacement_string,
                                                            ignore_case=True):
    re.sub('hello', 'bye', 'hello HeLLo HELLO', flags=re.IGNORECASE)
    new_string = original_string
    for x in strings_to_replace:
        new_string = re.sub(x, replacement_string, new_string)
        # new_string=new_string.replace(x,replacement_string) if not ignore_case else new_string.replace(x.lower(),replacement_string)
    return new_string


def strtomd5(stringtohash):
    result = hashlib.md5(stringtohash.encode())
    return result.hexdigest()


def log(text, start=None, end="\n", color="cyan", start_color="cyan"):
    """Print colorful log to stdout"""
    if start is None:
        start = "{:<10} {:<13}\t".format(datetime.datetime.now().strftime('%H:%M:%S'), f"[IMPORT CAMBRIDGE]")
    print(f"{termcolor.colored(start, start_color)}{termcolor.colored(text, color)}", end=end)


def load_url(url, silent=False):
    """Load a URL while sending an user-agent string to circumvent bot protection measures
    :param silent: whether to print about the event to stdout
    """
    try:
        if not silent:
            print(f'Downloading {url}')
        return requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}, timeout=120)

    except Exception as e:
        print("❌❌❌ Fehler in load_url!", e, url)


def loadurl(url, folder=r"/hdd/Software Engineering/PyCharm/2021 Q1/.pkl", headerstosend=None,
            maxfilenamelen=151, hourstillexpire=100000000000, makedirs=True, urllibparseurl=True, silent=False,
            cookies={}, timeout=120, request_delay=None, generic_delay=None, dontcache=False, error_delay=None):
    if not headerstosend:
        headerstosend = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
    if generic_delay:
        time.sleep(generic_delay)
    domainfolder = "_duolingo_"
    quotedurl = urllib.parse.quote(url) if urllibparseurl else url
    filenamefromurl = f'{string_to_filename(quotedurl.replace("/", "-"))}, headers={string_to_filename(str(headerstosend))}'  # "".join(c for c in urllib.parse.quote(url).replace("/", "-") if c in validfilenamechars) + ".pkl"
    filenamefromurl = f'{filenamefromurl}, md5={strtomd5(filenamefromurl)}'

    filenamefromurl = chop_down_string_length(filenamefromurl, maxfilenamelen)

    savepath = f'{folder}/.url/{domainfolder}/{filenamefromurl}.pkl'  # folder + "/.url/" + domainfolder + "/" + filenamefromurl
    if makedirs:
        os.makedirs(os.path.dirname(savepath), exist_ok=True)  # ! convoluted, just do makedirs(folder)

    if (path.exists(savepath) and (time.time() - path.getmtime(savepath)) < hourstillexpire * 3600):

        if not silent:
            print('✔️Loaded {} from cache'.format(url))

        return pickle.load(open(savepath, "rb"))

    else:
        try:
            if not silent:
                print('❌ Downloading and caching {} as {}'.format(url, filenamefromurl))
            f = requests.get(url,
                             headers=headerstosend, cookies=cookies, timeout=timeout)
            # print("dumped",len(f))
            if not dontcache:
                pickle.dump(f, open(savepath, "wb"))

            if request_delay:
                time.sleep(request_delay)
            return f

        except Exception as e:
            print("❌❌❌ Fehler in loadurl!", e, url, filenamefromurl)

            if error_delay:
                time.sleep(error_delay)


def scrub_word(word):
    """Remove annotations and parts of the term that aren't essential. Otherwise Cambridge or phrasefinder might not recognize it"""
    scrubbed = word.split("\t")[0].strip()

    # Cut out these strings:
    cut = ["sth.", "sb.", " from ", " into ", " with "]
    for x in cut:
        scrubbed = scrubbed.replace(x, "")

    # Cut off anything after these strings:
    split = ["[", "{", "<", " for ", " to ", " of "]
    for x in split:
        scrubbed = scrubbed.split(x)[0]

    # cut off these strings if they occur at the very end
    end = [" to", " up", " into", " on", " upon", " off", " (off)", " about", " back"]
    for x in end:
        if scrubbed[-len(x):] == x:
            scrubbed = scrubbed[:-len(x)].strip()

    # cut off these strings if they occur at the very beginning of the term
    start = ["to ", "make ", "a ", "be "]
    for x in start:
        if scrubbed[:len(x)] == x:
            scrubbed = scrubbed[len(x):].strip()

    # Remove any special characters
    scrubbed = re.sub("[^abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZé '-]", '', scrubbed).strip()

    return scrubbed


def get_phrasefinder(en):
    """Use the phrasefinder.io API to determine how common an english word is"""
    params = {'corpus': 'eng-us', 'query': urllib.parse.quote(en), 'topk': 20, 'format': 'tsv'}
    params = '&'.join('{}={}'.format(name, value) for name, value in params.items())
    try:
        response = requests.get('https://api.phrasefinder.io/search?' + params)
        return int(response.text.split("\t")[1])
    except Exception as e:
        # If the word can't be found, return 0
        return 0


def has_internet_connection(host="8.8.8.8", port=53, timeout=3):
    """Try connecting to the Google DNS server to check internet connectivity"""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False


def wait_for_internet_connection():
    """Try connecting to the Google DNS server to check internet connectivity. Wait until there is connectivity"""
    while not has_internet_connection():
        print("Waiting for internet connection")
        time.sleep(1)
    return True

