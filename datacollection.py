from __future__ import absolute_import

from six.moves import range

from OpenWPM.automation import CommandSequence, TaskManager
from hashlib import md5
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
        
#From webdriver_extensions.py
def get_intra_links(webdriver, url):
    ps1 = du.get_ps_plus_1(url)
    links = list()
    for elem in webdriver.find_elements_by_tag_name("a"):
        try:
            href = elem.get_attribute('href')
        except StaleElementReferenceException:
            continue
        if href is None:
            continue
        full_href = urljoin(url, href)
        if not full_href.startswith('http'):
            continue
        if du.get_ps_plus_1(full_href) == ps1:
            links.append(elem)
    return links

#From browser_commands.py
#This is called when the command (browse) is given. We want to simulate this
#functionality with modifications.
def browse_website(url, num_links, sleep, visit_id, webdriver,
                   browser_params, manager_params, extension_socket):
    """Calls get_website before visiting <num_links> present on the page.

    Note: the site_url in the site_visits table for the links visited will
    be the site_url of the original page and NOT the url of the links visited.
    """
    # First get the site
    get_website(url, sleep, visit_id, webdriver,
                browser_params, extension_socket)

    # Connect to logger
    logger = loggingclient(*manager_params['logger_address'])

    # Then visit a few subpages
    for i in range(num_links):
        links = [x for x in get_intra_links(webdriver, url)
                 if x.is_displayed() is True]
        if not links:
            break
        r = int(random.random() * len(links))
        logger.info("BROWSER %i: visiting internal link %s" % (
            browser_params['crawl_id'], links[r].get_attribute("href")))

        try:
            links[r].click()
            wait_until_loaded(webdriver, 300)
            time.sleep(max(1, sleep))
            if browser_params['bot_mitigation']:
                bot_mitigation(webdriver)
            webdriver.back()
            wait_until_loaded(webdriver, 300)
        except Exception:
            pass
    
def getParentContainer(container_class, **kwargs):
    """A custom function that detects if a tags on the page are 
    inside of an iframe or not."""
        
    container_class.inside = True
    driver = kwargs['driver']
    
    source_dump_path= kwargs['manager_params'].source_dump_path
    site_encoded = md5(driver.current_url.encode('utf-8')).hexdigest()
    site_id = 
    print("source dump path:", source_dump_path + )
    
    urls = []
    containers = []
    
    #If the element is in an iframe then it is invisible until you go in
    #that iframe, so we can safely assume that all elements returned from
    #this are all not in an iframe.
    for element in driver.find_elements_by_tag_name('a'):
        urls.append(element.get_attribute("href"))
        containers.append(False)
    
    #Obviously all elements in here are in an iframe.
    for iframe_element in driver.find_elements_by_tag_name('iframe'):
        for iframe in driver.switch_to_frame(iframe_element):
            for element in iframe.find_elements_by_tag_name('a'):
                urls.append(element.get_attribute("href"))
                containers.append(True)
		
		
    print("Containers: ", containers)
		
    #Need to get the oldest parent and see if it is html or iframe. Will need to be boolean for iframe or not.
#    url_container = zip(urls, containers)
		
#    sock = clientsocket()
#    sock.connect(*manager_params['aggregator_address'])
#
#    query = "CREATE TABLE IF NOT EXISTS parent_containers (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, url TEXT, iframe_container INTEGER);"
#    sock.send(("create_table", query))
#
#    for url, container in url_container:
#        query = ('parent_containers', {
#                "url": url,
#                "iframe_container": container
#                })
#        sock.send(query)
#        container_class.queue.put(url)
#    sock.close()
    container_class.inside = False
    print("inside is now false")




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
while container.inside or not container.queue.empty():
    time.sleep(10)
    print("Number in the queue: ", container.queue.qsize())
    print("inside boolean:", container.inside)
    while not container.queue.empty():
        temp_site = container.queue.get()
        command_sequence = CommandSequence.CommandSequence(temp_site)
    
        # Start by visiting the page
        command_sequence.browse(num_links=1000, sleep=10, timeout=60)
    	
        command_sequence.recursive_dump_page_source()
        
        command_sequence.run_custom_function(getParentContainer, (container,))
    
        # index='**' synchronizes visits between the three browsers
        manager.execute_command_sequence(command_sequence, index=None)

# Shuts down the browsers and waits for the data to finish logging
manager.close()
