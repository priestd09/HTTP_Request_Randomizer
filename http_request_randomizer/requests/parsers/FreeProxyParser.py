import logging

import requests
from bs4 import BeautifulSoup

from http_request_randomizer.requests.parsers.UrlParser import UrlParser
from http_request_randomizer.requests.proxy.ProxyObject import ProxyObject, AnonymityLevel

logger = logging.getLogger(__name__)
__author__ = 'pgaref'


class FreeProxyParser(UrlParser):
    def __init__(self, id, web_url, timeout=None):
        UrlParser.__init__(self, id, web_url, timeout)

    def parse_proxyList(self):
        curr_proxy_list = []
        response = requests.get(self.get_URl(), timeout=self.timeout)

        if not response.ok:
            logger.warn("Proxy Provider url failed: {}".format(self.get_URl()))
            return []

        content = response.content
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find("table", attrs={"id": "proxylisttable"})

        # The first tr contains the field names.
        headings = [th.get_text() for th in table.find("tr").find_all("th")]

        datasets = []
        for row in table.find_all("tr")[1:]:
            dataset = zip(headings, (td.get_text() for td in row.find_all("td")))
            if dataset:
                datasets.append(dataset)

        for dataset in datasets:
            proxy_obj = self.create_proxy_object(dataset)
            # Make sure it is a Valid Proxy Address
            if proxy_obj is not None and UrlParser.valid_ip_port(proxy_obj.get_address()):
                curr_proxy_list.append(proxy_obj)
            else:
                logger.debug("Proxy Invalid: {}".format(dataset))
        return curr_proxy_list

    def create_proxy_object(self, dataset):
        # Check Field[0] for tags and field[1] for values!
        ip = ""
        port = None
        anonymity = AnonymityLevel.UNKNOWN
        country = None
        for field in dataset:
            if field[0] == 'IP Address':
                # Make sure it is a Valid IP
                ip = field[1].strip()  # String strip()
                # Make sure it is a Valid IP
                if not UrlParser.valid_ip(ip):
                    logger.debug("IP with Invalid format: {}".format(ip))
                    return None
            elif field[0] == 'Port':
                port = field[1].strip()  # String strip()
            elif field[0] == 'Anonymity':
                anonymity = AnonymityLevel(field[1].strip())  # String strip()
            elif field[0] == 'Country':
                country = field[1].strip()  # String strip()
        return ProxyObject(source=self.id, ip=ip, port=port, anonymity_level=anonymity, country=country)

    def __str__(self):
        return "FreeProxy Parser of '{0}' with required bandwidth: '{1}' KBs" \
            .format(self.url, self.minimum_bandwidth_in_KBs)
