# Testing code for adblock parser
# Feel free to add more urls to test it out

from abparser import abparser

# url with ads
url_ads = [
"http://pagead2.googlesyndication.com/simgad/2710810634177601288",
"https://s0.2mdn.net/viewad/3919605/1-2015_Chevrolet_SignAndDrive_Retail__January_FT_static_CA_ENG_v1_300x250.jpg"
]

# normal urls
url_non_ads = [
"http://www.google.com",
"http://www.winkerxiao.com"
]

# classes or ids with ads
elem_ads = ["ad_banner_div", "ad_bar"]

# classes or ids non-indicative of ads
elem_non_ads = ["cover", "photo"]

# assert that parser recognize urls as ads
def test_ad_url():
    match = abparser.lookup()
    for url in url_ads:
        # returns true if match is found
        assert match.match_url(url) == True

# assert that parser recognize urls are not ads
def test_non_ad_url():
    match = abparser.lookup()
    for url in url_non_ads:
        # returns none if no matches are found
        assert match.match_url(url) == None

# assert that parser recognizes elems are ads
def test_elem_ads():
    match= abparser.lookup()
    for elem in elem_ads:
        # returns true in an array if found for each individual elem
        assert match.match_elem("class", elem) == [True]

# assert that parser recognizes elems are not ads
def test_elem_non_ads():
    match = abparser.lookup()
    for elem in elem_non_ads:
        # returns false in an array if found for individual elem
        assert match.match_elem("class", elem) == [False]
