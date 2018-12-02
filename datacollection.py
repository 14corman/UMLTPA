from __future__ import absolute_import

from six.moves import range

from OpenWPM.automation import CommandSequence, TaskManager
from hashlib import md5
import sys
import time

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
        

    
def paramE(container_class, depth, visit_id, **kwargs):
    """A custom function that detects if a tags on the page are 
    inside of an iframe or not."""
        
    print("VISIT ID ", visit_id)
    container_class.inside = True
    driver = kwargs['driver']
    
    urls = {}
    
    def collectLinks(driver, frame_stack, urls={}):
        is_top_frame = len(frame_stack) == 1
        for element in driver.find_elements_by_tag_name('a'):
            try:
                href = element.get_attribute('href')
            except StaleElementReferenceException:
                continue
            
            if href is None:
                continue
#                
#                full_href = urljoin(url, href)
#                if not full_href.startswith('http'):
#                    continue
                
            #Check if the url is part of the top domain, or is external.
            #If it is not external then add to next calls.
            #container_class.addSite(depth + 1, href)
            
            urls[href] = not is_top_frame
            #print("Adding ", href, " and it is ", not is_top_frame)
            
        for element in driver.find_elements_by_tag_name('script'):
            try:
                href = element.get_attribute('src')
            except StaleElementReferenceException:
                continue
            
            if href is None:
                continue
            
            urls[href] = not is_top_frame
            
        for element in driver.find_elements_by_tag_name('img'):
            try:
                href = element.get_attribute('src')
            except StaleElementReferenceException:
                continue
            
            if href is None:
                continue
            
            urls[href] = not is_top_frame
            
        for element in driver.find_elements_by_tag_name('iframe'):
            try:
                href = element.get_attribute('src')
            except StaleElementReferenceException:
                continue
            
            if href is None:
                continue
            
            urls[href] = not is_top_frame
            
        for element in driver.find_elements_by_tag_name('style'):
            try:
                href = element.get_attribute('href')
            except StaleElementReferenceException:
                continue
            
            if href is None:
                continue
            
            urls[href] = not is_top_frame
    
    #Default depth is 5 with (max_depth = 5)
    we.execute_in_all_frames(driver, collectLinks, {'urls': urls})
		
		
    #print("URLS: ", urls)
    
    db_path = kwargs["manager_params"]['database_name']
    with sqlite3.connect(db_path, check_same_thread=False) as database:
        cur = database.cursor()
        cur.execute("SELECT url FROM http_requests WHERE visit_id = ?", (visit_id,))
        
        rows = cur.fetchall()
     
        for row in rows:
            #print("ROW: ", row)
            tempUrl = row[0]
            if tempUrl in urls:
                isNotIframe = urls[tempUrl]
                database.cursor().execute("UPDATE http_requests SET depth = ? AND E = ? WHERE url = ?", (depth, isNotIframe, tempUrl))
                database.commit()
                print("UPDATE http_requests SET depth = %d AND E = %d WHERE url = %s" % (depth, isNotIframe, tempUrl))
            #else:
              #print("%s is not included" % tempUrl)
        

def paramsAToD(visit_id, **kwargs):
    db_path = kwargs["manager_params"]['database_name']
    with sqlite3.connect(db_path, check_same_thread=False) as database:
        cur = database.cursor()
        cur.execute("SELECT url FROM http_requests WHERE visit_id = ?", (visit_id,))
        
        rows = cur.fetchall()
     
        for row in rows:
          print(row)


# The list of sites that we wish to crawl
NUM_BROWSERS = 3

sites = []

# We want the first 500 websites.
num_websites = 3
with open('top-1m.csv','rb') as f:
    for x in xrange(num_websites):
        line = next(f)
        line = line.replace('\r\n','')
        site = line.split(',')[1]
        sites.append("http://" + site)
        
container = ContainerSites()
container.addSites(0, sites)

# Loads the manager preference and 3 copies of the default browser dictionaries
manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)

# Update browser configuration (use this for per-browser settings)
for i in range(NUM_BROWSERS):
    # Record HTTP Requests and Responses
    browser_params[i]['http_instrument'] = True
    # Enable flash for all three browsers
    browser_params[i]['disable_flash'] = False
    #browser_params[i]['headless'] = True
    browser_params[i]['js_instrument'] = False

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '~/Desktop/'
manager_params['log_directory'] = '~/Desktop/'

# Have the program sleep for 10 milsec, and set the name of the database.
time.sleep(10)
manager_params['database_name'] = 'output_data.sqlite'

max_depth = 1
visit_counter = 1
for depth in range(max_depth):
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params) 
    
    database = manager.data_aggregator
    
    sites = container.depthUrl[depth]
      
    # Visits the sites with all browsers simultaneously
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site)
    
        # Start by visiting the page
        command_sequence.get(sleep=10, timeout=60)
        
        #Collect parameter E
        command_sequence.run_custom_function(paramE, (container, depth, visit_counter))
        
        #Collect parameters A through D
        command_sequence.run_custom_function(paramsAToD, (visit_counter,))
    
        # index='**' synchronizes visits between the three browsers
        manager.execute_command_sequence(command_sequence, index=None)
        visit_counter += 1
    
    # Shuts down the browsers and waits for the data to finish logging
    manager.close()
