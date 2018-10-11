from __future__ import absolute_import

from . import utilities
from ..automation import CommandSequence, TaskManager
from ..automation.utilities import db_utils
from ..automation.SocketInterface import clientsocket


class CustomFunctions:
    """Will hold any custom functions we need to collect data."""

	def getParentContainer(url, **kwargs):
		"""Collects the parent container for the url."""
		driver = kwargs['driver']
		manager_params = kwargs['manager_params']
		urls = [
			x for x in (
				element.get_attribute("href")
				for element in driver.find_elements_by_tag_name('a')
			)
			if x == url
		]
		
		#Need to get the oldest parent and see if it is html or iframe. Will need to be boolean for iframe or not.
		url_container = zip(urls, url.find_element_by_xpath("..") for url in urls)
		
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
