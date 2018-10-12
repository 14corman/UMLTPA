from __future__ import absolute_import

from six.moves import range

from OpenWPM.automation import CommandSequence, TaskManager
import sys
import time

from OpenWPM.automation.utilities import db_utils
from OpenWPM.automation.SocketInterface import clientsocket

class CustomFunctions:
    """Will hold any custom functions we need to collect data."""
    def getParentContainer(sites, **kwargs):
        """Collects the parent container for the url."""
        driver = kwargs['driver']
        manager_params = kwargs['manager_params']
        url_elements = [
                element.get_attribute("href")
                for element in driver.find_elements_by_tag_name('a')
        ]
    		
        urls = [
                url.get_attribute("href") for url in url_elements
        ]
    		
        conatiners = [
                element.find_element_by_xpath(".//ancestor::iframe") for element in url_elements
        ]
    		
        print("Containers: ", containers)
    		
        #Need to get the oldest parent and see if it is html or iframe. Will need to be boolean for iframe or not.
        url_container = zip(urls, containers)
    		
        sock = clientsocket()
        sock.connect(*manager_params['aggregator_address'])
    
        query = "CREATE TABLE IF NOT EXISTS parent_containers (id NOT NULL INTEGER PRIMARY KEY, url TEXT, container TEXT);"
        sock.send(("create_table", query))
    
        for url, container in url_container:
            query = ('parent_containers', {
                    "url": url,
                    "container": container
                    })
            sock.send(query)
        sock.close()




# The list of sites that we wish to crawl
NUM_BROWSERS = 3

sites = []

# We want the first 500 websites.
num_websites = 1
with open('top-1m.csv','rb') as f:
    for x in xrange(num_websites):
        line = next(myfile)
        line = line.replace('\n','')
	     site = line.split(',')[1]
        sites.append("http://"+site)

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
for site in sites:
    command_sequence = CommandSequence.CommandSequence(site)

    # Start by visiting the page
    command_sequence.get(sleep=10, timeout=60)
	
    command_sequence.run_custom_function(CustomFunctions.getParentContainer, (sites))

    # dump_profile_cookies/dump_flash_cookies closes the current tab.
    #command_sequence.dump_profile_cookies(120)

    # index='**' synchronizes visits between the three browsers
    manager.execute_command_sequence(command_sequence, index=None)

# Shuts down the browsers and waits for the data to finish logging
manager.close()
