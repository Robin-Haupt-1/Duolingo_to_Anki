import requests
from private import cookies2


website = requests.get("https://www.duolingo.com/vocabulary/overview?", cookies=cookies2, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'})
print(website.text)

website = requests.get("https://www.duolingo.com/api/1/dictionary_page?lexeme_id=6e42f1fe9c9668451800a18965d0efca&use_cache=false&from_language_id=en", cookies=cookies2, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'})
print(website.text)
