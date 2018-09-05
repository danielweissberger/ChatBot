import random
import re
import requests
from bs4 import BeautifulSoup
from django.utils.timezone import now
from requests.exceptions import ProxyError



GOOGLE_URLS = {
    "en": "https://www.google.com/search",
    "he": "https://www.google.co.il/search"
}


ORDER_CHOICES = [
    'desc',
    'rand'
]


# This is the function which makes the http request to google search passing the requested keyword as a parameter

def scrape(keyword, page, lang, user_agent, proxy):
    params = {
        "q": keyword.strip(),
        "start": page,
        "num": 10,
        "complete": 0,
        "pws": 0,
        "hl": lang,
        "lr": "lang_%s" % lang
    }

    headers = {
        "User-agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    proxy = {
        'http': 'https://108.59.14.203:13010',
        'https': 'https://108.59.14.203:13010',
    }

    return requests.request(
        method="GET",
        url=GOOGLE_URLS[lang],
        params=params,
        headers=headers,
        # proxies=proxy,
    )


def keyword_scrape(keyword, from_page, to_page, lang, user_agent):

    for page in range(from_page, to_page):
        try:
            # Call scrape function to make an http request to google search with the keyword
            response = scrape(keyword, page, lang, user_agent, None)

            if response.status_code != 200:
                return False, '[%s] Error: %s' % (timestamp(), response.status_code)
            else:
                ads = parse_results(response.text, keyword, lang)
                return ads[1]

        # Http response failure
        except (Exception, ProxyError) as e:
            return "The search request failed, please try again"


# Several unused parameters here (they are preserved in case more complex search functionality may be added
# in the future

def run_scraper(keyword=None, count_keywords=1, from_page=0, to_page=1, lang="en", user_agent=None,
                sleep_randomly_from=10, sleep_randomly_to=30, ignore_randomly=True):

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 ' \
                 '(HTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

    try:
        #
        result = keyword_scrape(keyword, from_page, to_page, lang, user_agent)
        return result

    except Exception as e:
        print(e)
        return "The search request failed, please try again"


# Retrieve a formatted timestamp
def timestamp():
    return now().strftime('%Y-%m-%d %H:%M:%S')


# This function parses the google search results using beautiful soup
def parse_results(source, keyword, lang):
    phone_regex = re.compile('(\+?[0-9]{1,3})?1?\W([0-9][0-9][0-9])\W{1,2}([0-9][0-9]{2})\W([0-9]{4})(\s?e?x?t? ?(\d*))?')

    soup = BeautifulSoup(source, 'html.parser')

    ads = []
    sequence = 0

    for ad in soup.find_all('div', {'class': 'Z0LcW'}):
        return [None, [{'url': '', 'description': ad.text}]]

    for ad in soup.find_all('li', {'class': 'ads-ad'}):
        sequence += 1
        ad_item = {
            "keyword": keyword.strip(),
            "lang": lang,
            "sequence": sequence
        }

        try:
            ad_item["final_url"] = ad.h3.a.attrs["href"]
            ad_item["headline"] = ad.h3.a.text
        except:
            ad_item["final_url"] = ""  # parse_qs(urlparse(ad.h3.a["href"]).query)["adurl"][0]
            ad_item["headline"] = ""

        ad_item["display_url"] = ad.cite.text
        ad_item["description"] = ad.find('div', {"class": "ads-creative"}).text.strip()
        ad_item["phones"] = []

        phone = ad.find('span', {"class": "_r2b"})
        if phone:
            ad_item["phones"].append(phone.text)

        phone = ad.find('span', {"class": "_xnd"})
        if phone:
            ad_item["phones"].append(phone.text)

        phone = re.search(phone_regex, ad_item["headline"])
        if phone:
            ad_item["phones"].append(clean_phone_number(phone.group()))

        phone = re.search(phone_regex, ad_item["description"])
        if phone:
            ad_item["phones"].append(clean_phone_number(phone.group()))

        address = ad.find('a', {"class": "_vnd"})
        if address:
            ad_item["address"] = address.text
        else:
            ad_item["address"] = ""

        opening_hours = ad.find('span', {"class": "_G2b"})
        if opening_hours:
            ad_item["opening_hours"] = opening_hours.span.text
        else:
            ad_item["opening_hours"] = ""

        ads.append(ad_item)

    #Parse organic search results
    organic_ads = []
    sequence = 0
    for organic_ad in soup.find_all('div', {'class': 'rc'}):
        url = organic_ad.h3.a.attrs["href"]
        sequence += 1
        if url:

            phones = []
            organic_ad_item = {
                "keyword": keyword.strip(),
                "lang": lang,
                "sequence": sequence,
                "url": url
            }
            try:
                headline = organic_ad.h3.a.text
            except:
                headline = ''

            if headline:
                phone = re.search(phone_regex, headline)
                if phone:
                    phones.append(clean_phone_number(phone.group()))
            try:
                alternate_url = organic_ad.cite.text
            except:
                alternate_url = ''

            if alternate_url:
                phone = re.search(phone_regex, alternate_url)
                if phone:
                    phones.append(clean_phone_number(phone.group()))

            try:
                description = organic_ad.find('span', {'class': 'st'}).text

            except:
                description = ''

            if description:
                phone = re.search(phone_regex, description)
                if phone:
                    phones.append(clean_phone_number(phone.group()))

            organic_ad_item['headline'] = headline
            organic_ad_item['description'] = description
            organic_ad_item['phones'] = phones
            organic_ad_item['alternate_url'] = alternate_url
            organic_ads.append(organic_ad_item)

    return ads, organic_ads


def clean_phone_number(phone):
    ascii = ord(phone[0])
    if 57 < ascii or ascii < 48 or ascii != 43 or ascii != 40:
        phone = phone.replace(phone[0], "")
    return phone
