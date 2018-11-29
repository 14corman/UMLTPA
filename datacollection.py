from __future__ import absolute_import

from six.moves import range

from OpenWPM.automation import CommandSequence, TaskManager
from hashlib import md5
import sys
import time
import Queue

from selenium.common.exceptions import StaleElementReferenceException

from OpenWPM.automation.utilities import db_utils
from OpenWPM.automation.utilities import domain_utils as du
from OpenWPM.automation.Commands.utils import webdriver_extensions as we
from OpenWPM.automation.SocketInterface import clientsocket

from six.moves.urllib.parse import urljoin

class ContainerSites:
    
    def __init__(self):
        #maxsize <= 0 means infinite size queue.
        #OpenWPM uses Python 2.7, so need Q instead of q.
        self.queue = {}
            
        self.inside = True
        
    def addSites(self, depth, sites):
        self.queue[depth] = sites
        
    def addSite(self, depth, site):
        if depth not in self.queue:
          self.queue[depth] = []
      
        self.queue[depth].append(site)
        

    
def getParentContainer(container_class, depth, url, **kwargs):
    """A custom function that detects if a tags on the page are 
    inside of an iframe or not."""
        
    container_class.inside = True
    driver = kwargs['driver']
    
    urls = {}
    
    def collectLinks(driver, frame_stack, urls={}):
        is_top_frame = len(frame_stack) == 1
        for element in driver.find_elements_by_tag_name('a'):
            if element.is_displayed() is True:
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
                
                urls[href] = not is_top_frame
                container_class.addSite(depth, href)
                print("Adding ", href, " and it is ", not is_top_frame)
    
    #Default depth is 5 with (max_depth = 5)
    we.execute_in_all_frames(driver, collectLinks, {'urls': urls})
		
		
    #print("URLS: ", urls)
		
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    query = "CREATE TABLE IF NOT EXISTS parent_containers (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, url TEXT, iframe_container INTEGER, level INTEGER);"
    sock.send(("create_table", query))

    for url, container in urls:
        query = ('parent_containers', {
                "url": url,
                "iframe_container": container,
                "level": depth + 1
                })
        sock.send(query)
        container_class.queue.put(url)
    sock.close()
    container_class.inside = False
    print("inside is now false")




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
    browser_params[i]['js_instrument'] = True

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '~/Desktop/'
manager_params['log_directory'] = '~/Desktop/'

# Have the program sleep for 10 milsec, and set the name of the database.
time.sleep(10)
manager_params['database_name'] = 'output_data.sqlite'

max_depth = 2
for depth in range(max_depth):
    # Instantiates the measurement platform
    # Commands time out by default after 60 seconds
    manager = TaskManager.TaskManager(manager_params, browser_params) 
    
    sites = container.queue[depth]
      
    # Visits the sites with all browsers simultaneously
    for site in sites:
        command_sequence = CommandSequence.CommandSequence(site)
    
        # Start by visiting the page
        command_sequence.get(sleep=10, timeout=60)
    	
        #command_sequence.recursive_dump_page_source()
        
        command_sequence.run_custom_function(getParentContainer, (container, depth, site))
    
        # index='**' synchronizes visits between the three browsers
        manager.execute_command_sequence(command_sequence, index=None)
    
    # Shuts down the browsers and waits for the data to finish logging
    manager.close()
