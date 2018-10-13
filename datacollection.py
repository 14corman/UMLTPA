from __future__ import absolute_import

from six.moves import range

from OpenWPM.automation import CommandSequence, TaskManager
import sys
import time
import Queue

from OpenWPM.automation.utilities import db_utils
from OpenWPM.automation.SocketInterface import clientsocket

class ContainerSites:
    
    def __init__(self, sites):
        #maxsize <= 0 means infinite size queue.
        #OpenWPM uses Python 2.7, so need Q instead of q.
        self.queue = Queue.Queue(maxsize = -1)
        
        for site in sites:
            self.queue.put(site)
            
        self.inside = True
    
def getParentContainer(container_class, **kwargs):
    """A custom function that detects if a tags on the page are 
    inside of an iframe or not."""
    container_class.inside = True
    driver = kwargs['driver']
    manager_params = kwargs['manager_params']
    url_elements = [
            element for element in driver.find_elements_by_tag_name('a')
    ]
		
    urls = []
    containers = []
    for element in url_elements:
        urls.append(element.get_attribute("href"))
        try:
            element.find_element_by_xpath(".//ancestor::iframe") 
            containers.append(True)
        except:
            containers.append(False)
		
    print("Containers: ", containers)
		
    #Need to get the oldest parent and see if it is html or iframe. Will need to be boolean for iframe or not.
    url_container = zip(urls, containers)
		
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    query = "CREATE TABLE IF NOT EXISTS parent_containers (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, url TEXT, iframe_container INTEGER);"
    sock.send(("create_table", query))

    for url, container in url_container:
        query = ('parent_containers', {
                "url": url,
                "iframe_container": container
                })
        sock.send(query)
        container_class.queue.put(url)
    sock.close()
    container_class.inside = False




# The list of sites that we wish to crawl
NUM_BROWSERS = 3

sites = []

# We want the first 500 websites.
num_websites = 1
with open('top-1m.csv','rb') as f:
    for x in xrange(num_websites):
        line = next(f)
        line = line.replace('\r\n','')
        site = line.split(',')[1]
        sites.append("http://" + site)
        
container = ContainerSites(sites)

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

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params)

# Visits the sites with all browsers simultaneously
#This while loop is still breaking out too early. It will not process more
#than 1 site at a time if 1 is in the queue.
while container.inside and not container.queue.empty():
    command_sequence = CommandSequence.CommandSequence(container.queue.get())

    # Start by visiting the page
    command_sequence.get(sleep=10, timeout=60)
	
    command_sequence.run_custom_function(getParentContainer, (container,))

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index=None)

# Shuts down the browsers and waits for the data to finish logging
manager.close()
