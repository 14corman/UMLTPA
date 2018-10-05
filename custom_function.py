from __future__ import absolute_import

from . import utilities
from ..automation import CommandSequence, TaskManager
from ..automation.utilities import db_utils
from ..automation.SocketInterface import clientsocket


class CustomFunctions:
    """Will hold any custom functions we need to collect data."""

	def getParentContainer(**kwargs):
		"""Collects the parent container for the url."""
		driver = kwargs['driver']
		manager_params = kwargs['manager_params']
		link_urls = [
			x for x in (
				element.get_attribute("href")
				for element in driver.find_elements_by_tag_name('a')
			)
			if x.startswith(scheme + '://')
		]
		current_url = driver.current_url

		sock = clientsocket()
		sock.connect(*manager_params['aggregator_address'])

		query = ("CREATE TABLE IF NOT EXISTS parent_containers ("
				 "url TEXT, container TEXT);")
		sock.send(("create_table", query))

		query = ('parent_containers', {
			"url": current_url,
			"container": link
		})
		sock.send(query)
		sock.close()