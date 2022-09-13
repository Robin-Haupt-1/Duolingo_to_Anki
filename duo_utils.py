import urllib.parse
import time
import os
import urllib.parse
import urllib.request
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
    """if raw, will delete all illegal characters. Else will replace '?' with '¿' and all others with '-' """
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


def loadurl(url, folder=r"/hdd/Software Engineering/PyCharm/2021 Q1/.pkl", headerstosend=None,
            maxfilenamelen=151, hourstillexpire=100000000000, makedirs=True, urllibparseurl=True, silent=False,
            cookies={}, timeout=120, request_delay=None, generic_delay=None, dontcache=False, error_delay=None):
    if not headerstosend:
        headerstosend = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
    if generic_delay:
        time.sleep(generic_delay)
    domainfolder = "_duolingo_"
    quotedurl = urllib.parse.quote(url) if urllibparseurl else url
    filenamefromurl = f'{string_to_filename(quotedurl.replace("/", "-"))}, headers={string_to_filename(str(headerstosend))} cookies={string_to_filename(str(cookies))}'  # "".join(c for c in urllib.parse.quote(url).replace("/", "-") if c in validfilenamechars) + ".pkl"
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


def get_phrasefinder(en):
    """Use the phrasefinder.io API to determine how common an english word is"""
    params = {'corpus': 'eng-us', 'query': urllib.parse.quote(en), 'topk': 20, 'format': 'tsv'}
    params = '&'.join('{}={}'.format(name, value) for name, value in params.items())
    try:
        response = loadurl('https://api.phrasefinder.io/search?' + params)
        return int(response.text.split("\t")[1])
    except Exception as e:
        # If the word can't be found, return 0
        return 0
