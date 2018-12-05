from __future__ import absolute_import

from six.moves import range

from OpenWPM.automation import CommandSequence, TaskManager
from hashlib import md5
import sys
import time
import re
import os
from os.path import isfile, join
from adblockparser import AdblockRules

#from urllib.parse import urlparse #Python 3
from urlparse import urlparse  # Python 2

from selenium.common.exceptions import StaleElementReferenceException

from OpenWPM.automation.utilities import db_utils
import sqlite3
from OpenWPM.automation.utilities import domain_utils as du
from OpenWPM.automation.Commands.utils import webdriver_extensions as we
from OpenWPM.automation.SocketInterface import clientsocket

from six.moves.urllib.parse import urljoin

class ContainerSites:
    
    def __init__(self):
        self.depthUrl = {}
        
    def addSites(self, depth, sites):
        self.depthUrl[depth] = sites
        
    def addSite(self, depth, site):
        if depth not in self.depthUrl:
          self.depthUrl[depth] = []
      
        self.depthUrl[depth].append(site)
        

def helperE(driver, tag, attribute, isTopFrame):
    urls = {}
    for element in driver.find_elements_by_tag_name(tag):
        try:
            href = element.get_attribute(attribute)
        except StaleElementReferenceException:
            continue
        
        if href is None:
            continue
          
        urls[href] = not isTopFrame
        
    return urls
    

def paramE(depth, visitId, **kwargs):
    """A custom function that detects if a tags on the page are 
    inside of an iframe or not."""
        
    driver = kwargs['driver']
    
    urls = {}
    
    def collectLinks(driver, frameStack, urls={}):
        isTopFrame = len(frameStack) == 1
        
        urls.update(helperE(driver, 'a', 'href', isTopFrame))
        urls.update(helperE(driver, 'script', 'src', isTopFrame))
        urls.update(helperE(driver, 'img', 'src', isTopFrame))
        urls.update(helperE(driver, 'iframe', 'src', isTopFrame))
        urls.update(helperE(driver, 'style', 'href', isTopFrame))
        urls.update(helperE(driver, 'link', 'href', isTopFrame))
            
    
    #Default depth is 5 with (max_depth = 5)
    we.execute_in_all_frames(driver, collectLinks, {'urls': urls})
    
    db_path = kwargs["manager_params"]['database_name']
    with sqlite3.connect(db_path, check_same_thread=False) as database:
        cur = database.cursor()
        cur.execute("SELECT url FROM http_requests WHERE visit_id = ?", (visitId,))
        
        rows = cur.fetchall()
     
        for row in rows:
            #print("ROW: ", row)
            tempUrl = row[0]
            if tempUrl in urls:
                isNotIframe = urls[tempUrl]
                cur.execute("UPDATE http_requests SET depth = ?, E = ? WHERE url = ?", (depth, isNotIframe, tempUrl))
                database.commit()
        

def paramsAToD(visitId, dbPath):
    with sqlite3.connect(dbPath, check_same_thread=False) as database:
        cur = database.cursor()
        cur.execute("SELECT url FROM http_requests WHERE visit_id = ?", (visitId,))
        
        AOneCheck = ["ad.",       "ad/",        "ad&",        "ad=",        "ad;",        "ad-",        "ad_",
                     "advert.",   "advert/",    "advert&",    "advert=",    "advert;",    "advert-",    "advert_",
                     "popup.",    "popup/",     "popup&",     "popup=",     "popup;",     "popup-",     "popup_",
                     "banner.",   "banner/",    "banner&",    "banner=",    "banner;",    "banner-",    "banner_",
                     "sponsor.",  "sponsor/",   "sponsor&",   "sponsor=",   "sponsor;",   "sponsor-",   "sponsor_",
                     "iframe.",   "iframe/",    "iframe&",    "iframe=",    "iframe;",    "iframe-",    "iframe_",
                     "googlead.", "googlead/",  "googlead&",  "googlead=",  "googlead;",  "googlead-",  "googlead_",
                     "adsys.",    "adsys/",     "adsys&",     "adsys=",     "adsys;",     "adsys-",     "adsys_",
                     "adser.",    "adser/",     "adser&",     "adser=",     "adser;",     "adser-",     "adser_"]
        
        ATwoCheck = ["ad", "advert", "popup", "banner", "sponsor", "iframe", "googlead", "adsys", "adser"]
        
        BOneCheck = "[\w\-]+=[^;]+;*"
        
        BTwoCheck = "[\w\-]+=[^&]+&*"
        
        DOneCheck = "\d{2,4}x\d{2,4}"
        
        DTwoCheck = ["screenheight", "screenwidth", "browserheight", "browserwidth", "screendensity", "screenresolution", "browsertimeoffset"]
        
        rows = cur.fetchall()
     
        for row in rows:
          url = row[0]
          
          #Anything from AOneCheck exists in url
          AOne = any(check in url for check in AOneCheck)
          
          #Anything from ATwoCheck exists in url
          ATwo = any(check in url for check in ATwoCheck)
          
          #There are at least 2 occurences of ..;.. in the url (parameters being split by semicolon)
          BOne = len(re.findall(BOneCheck, url)) >= 2
          
          #The parameters are being set up before the ?
          urlSplit = url.split("?")
          BTwo = len(re.findall(BTwoCheck, urlSplit[0])) >= 2
              
          #The base domain is anywhere in url path or query strings 
          COne = False
          
          #The url is not a subdomain of the base url
          CTwo = False
          
          cur.execute("SELECT top_level_url, is_third_party_channel FROM http_requests WHERE url = ? AND visit_id = ?", (url, visitId))
          
          possibleRows = cur.fetchall()
          for CRow in possibleRows:
              topUrl = CRow[0]
              
              if topUrl is not None:
                urlTuple = urlparse(url)
                parsedTopUrl = urlparse(topUrl).netloc.replace("http://", "").replace("https://", "").replace("www.", "")
                COne = parsedTopUrl in urlTuple.path or \
                       parsedTopUrl in urlTuple.query
              
              CTwo = CRow[1]
          
          #The URL contains 2-4 numbers followed by an "x" followed by 2-4 more numbers (EX: 950x2500)
          DOne = len(re.findall(DOneCheck, url)) >= 1
          
          #Anything from DTwoCheck exists in url
          DTwo = any(check in url for check in DTwoCheck)
          
          cur.execute("UPDATE http_requests SET A_one = ?, A_two = ?, B_one = ?, B_two = ?, C_one = ?, C_two = ?, \
                      D_one = ?, D_two = ? WHERE url = ? AND visit_id = ?", (AOne, ATwo, BOne, BTwo, COne, CTwo, DOne, DTwo, url, visitId))
          
          database.commit()
          
def paramF(visitId, dbPath):
    with sqlite3.connect(dbPath, check_same_thread=False) as database:
        num = (visitId,)
        cur = database.cursor()
    
        # This part of the function calculates proportion of external iframes for each website ID and
            # and stores it in a list 'prop_ext_iframe'.
        
        cur.execute('SELECT * FROM http_requests WHERE E = 1 AND visit_id = ?', num)
        ext_iframe, total_iframe = 0,0
        prop_ext_iframe = 0.0
        for row in cur.fetchall():
            total_iframe += 1
            if row[13] == 1: # row[10] is binary column for external
                ext_iframe += 1 
        if total_iframe !=0 :
            prop_ext_iframe = ext_iframe/float(total_iframe)
    
        # This part of the function calculates proportion of external scripts for each website ID and
            # and stores it in a list 'prop_ext_script'.
            
        cur.execute('SELECT * FROM http_requests WHERE content_policy_type = 2 AND visit_id = ?', num)
        ext_script, total_script = 0, 0
        prop_ext_script = 0.0
        for row in cur.fetchall():
            total_script += 1
            if row[13] == 1: # row[10] is binary column for external
                ext_script += 1
        if total_script !=0 :
            prop_ext_script = ext_script/float(total_script)
    
        # This part of the function calculates proportion of URL's which are external resources for each website ID and
            # and stores it in a list 'prop_ext_resources'.
    
        cur.execute('SELECT * FROM http_requests WHERE visit_id = ?', num)
        ext_url_resources, total_url_resources = 0, 0
        prop_ext_url_resources = 0.0
        for row in cur.fetchall():
            total_url_resources += 1
            if row[13] == 1 : # row[10] is binary column for external
                ext_url_resources += 1
        if total_url_resources != 0:
            prop_ext_url_resources = ext_url_resources/float(total_url_resources)
            
        cur.execute ('UPDATE http_requests SET F_iframe = (?) WHERE visit_id = ?', (prop_ext_iframe, visitId))
        cur.execute ('UPDATE http_requests SET F_script = (?) WHERE visit_id = ?', (prop_ext_script, visitId))
        cur.execute ('UPDATE http_requests SET F_resource = (?) WHERE visit_id = ?', (prop_ext_url_resources, visitId))
        
        database.commit()
        
def blockerCheck(visitId, dbPath, blocker, blockerNum):
    with sqlite3.connect(dbPath, check_same_thread=False) as database:
        cur = database.cursor()
        cur.execute("SELECT url FROM http_requests WHERE visit_id = ?", (visitId,))
        rows = cur.fetchall()
        
        blockerString = "_month_list"
        if blockerNum == 0:
            blockerString = "current_list"
        elif blockerNum == 1:
            blockerString = "two" + blockerString
        elif blockerNum == 2:
            blockerString = "four" + blockerString
        elif blockerNum == 3:
            blockerString = "six" + blockerString
     
        for row in rows:
            url = row[0]    
            result = blocker.should_block(url)
            cur.execute("UPDATE http_requests SET " + blockerString + " = ? WHERE url = ? AND visit_id = ?", (result, url, visitId))
            
        database.commit()
          
        
def getAdBlock(directory):
    files = [join(directory, f) for f in os.listdir(directory) if isfile(join(directory, f))]
    
    content = []
    for file in files:
        with open(file) as f:
            for line in f:
                content.append(line.strip())
                
    return content
  
def getNextDepthHelper(url, depth, cur):
    cur.execute("INSERT INTO url_depth (depth, url) VALUES (?, ?)", (depth + 0, url))
  
def getNextDepth(url, depth, **kwargs):
    driver = kwargs['driver']
    domain = urlparse(url).netloc.replace("http://", "").replace("https://", "").replace("www.", "")
    
    db_path = kwargs["manager_params"]['database_name']
    with sqlite3.connect(db_path, check_same_thread=False) as database:
        cur = database.cursor()
        for element in driver.find_elements_by_tag_name("a"):
            try:
                href = element.get_attribute("href")
            except StaleElementReferenceException:
                continue
            
            if href is None:
                continue
              
            if domain in href:
                #print("Next url in depth: ", href)
                getNextDepthHelper(href, depth + 1, cur)
                
        database.commit()
          


# The list of sites that we wish to crawl
NUM_BROWSERS = 3

#Will hold all websites and their respective depth
container = ContainerSites()

easyListDirs = ["easylist-Dec 4", "easylist-Oct 4", "easylist-Aug 4", "easylist-Jun 4"]
blockers = []        

# Loads the manager preference and 3 copies of the default browser dictionaries
managerParams, browserParams = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    browserParams[i]['http_instrument'] = True
    # Enable flash for all three browsers
    browserParams[i]['disable_flash'] = False
    #browserParams[i]['headless'] = True
    browserParams[i]['js_instrument'] = True
    browserParams[i]['ublock-origin'] = False
    browserParams[i]['ghostery'] = False
    

# Update TaskManager configuration (use this for crawl-wide settings)
managerParams['data_directory'] = '~/Desktop/'
managerParams['log_directory'] = '~/Desktop/'

# Have the program sleep for 10 milsec, and set the name of the database.
time.sleep(10)
managerParams['database_name'] = 'output_data.sqlite'

db_path = os.path.join(os.path.expanduser('~/Desktop/'), managerParams['database_name'])

# We want the first 500 websites.
num_websites = 500

maxDepth = 2
visitCounter = 1
for depth in range(maxDepth + 1):
  
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(managerParams, browserParams) 
    
    #sites = container.depthUrl[depth]
    
    sites = []
    
    if depth == 0:
        with open('top-1m.csv','rb') as f:
          for x in xrange(num_websites):
              line = next(f)
              line = line.replace('\r\n','')
              site = line.split(',')[1]
              sites.append("http://" + site)
    else:
        with sqlite3.connect(db_path, check_same_thread=False) as database:
            cur = database.cursor()
            cur.execute("SELECT url FROM url_depth WHERE depth = ?", (depth,))
            rows = cur.fetchall()
            for row in rows:
                sites.append(row[0])
      
    # Visits the sites with all browsers simultaneously
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site)
    
        # Start by visiting the page
        command_sequence.get(sleep=10, timeout=60)
        
        #Collect parameter E
        command_sequence.run_custom_function(paramE, (depth, visitCounter))
        
        #Get URLs for next depth
        command_sequence.run_custom_function(getNextDepth, (site, depth))
        
        #Collect parameters A through D
        #command_sequence.run_custom_function(paramsAToD, (visitCounter,))
    
        # index='**' synchronizes visits between the three browsers
        manager.execute_command_sequence(command_sequence, index=None)
        
        visitCounter += 1
    
    # Shuts down the browsers and waits for the data to finish logging
    manager.close()
    
print("Manager done......")
for easyListDir in easyListDirs:
    blockers.append(AdblockRules(getAdBlock(easyListDir)))
    print("blocker %s created" % (easyListDir,))


#Perform any commands outside of manager crawls.
for i in range(visitCounter):
    paramsAToD(i, db_path)
    paramF(i, db_path)
    
    for (index, blocker) in enumerate(blockers):
        blockerCheck(i, db_path, blocker, index)
        
    print("id %d parsed" % (i,))
