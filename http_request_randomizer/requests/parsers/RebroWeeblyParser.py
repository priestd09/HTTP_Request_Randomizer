import logging

import requests
from bs4 import BeautifulSoup

from http_request_randomizer.requests.parsers.UrlParser import UrlParser
from http_request_randomizer.requests.proxy.ProxyObject import ProxyObject, AnonymityLevel

logger = logging.getLogger(__name__)
__author__ = 'pgaref'


class RebroWeeblyParser(UrlParser):
    def __init__(self, id, web_url, timeout=None):
        self.top_proxy_path = "proxy-list.html"
        self.txt_proxy_path = "txt-lists.html"
        UrlParser.__init__(self, id, web_url, timeout)

    def parse_proxyList(self, use_top15k=False):
        curr_proxy_list = []
        response = requests.get(self.get_URl() + "/" + self.top_proxy_path, timeout=self.timeout)

        if not response.ok:
            logger.warn("Proxy Provider url failed: {}".format(self.get_URl()))
            return []

        content = response.content
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find("div", attrs={"class": "paragraph", 'style': "text-align:left;"}).find('font', attrs={
            'color': '#33a27f'})
        # Parse Top Proxy List page
        for row in [x for x in table.contents if getattr(x, 'name', None) != 'br']:
            # Make sure it is a Valid Proxy Address
            proxy_obj = self.create_proxy_object(row)
            if proxy_obj is not None and UrlParser.valid_ip_port(row):
                curr_proxy_list.append(proxy_obj)
            else:
                logger.debug("Proxy Invalid: {}".format(row))
        # Usually these proxies are stale
        if use_top15k:
            # Parse 15k Nodes Text file (named *-all-*.txt)
            content = requests.get(self.get_URl() + "/" + self.txt_proxy_path).content
            soup = BeautifulSoup(content, "html.parser")
            table = soup.find("div", attrs={"class": "wsite-multicol-table-wrap"})
            for link in table.findAll('a'):
                current_link = link.get('href')
                if current_link is not None and "all" in current_link:
                    self.txt_proxy_path = current_link
            more_content = requests.get(self.get_URl() + self.txt_proxy_path).text
            for proxy_address in more_content.split():
                if UrlParser.valid_ip_port(proxy_address):
                    proxy_obj = self.create_proxy_object(row)
                    curr_proxy_list.append(proxy_obj)
        return curr_proxy_list

    def create_proxy_object(self, dataset):
        # Provider specific code
        dataset = dataset.strip()  # String strip()
        ip = dataset.split(":")[0]
        # Make sure it is a Valid IP
        if not UrlParser.valid_ip(ip):
            logger.debug("IP with Invalid format: {}".format(ip))
            return None
        port = dataset.split(":")[1]
        # TODO: Parse extra tables and combine data - Provider seems to be out-of-date
        country = "Unknown"
        anonymity = AnonymityLevel("unknown")

        return ProxyObject(source=self.id, ip=ip, port=port, anonymity_level=anonymity, country=country)

    def __str__(self):
        return "RebroWeebly Parser of '{0}' with required bandwidth: '{1}' KBs" \
            .format(self.url, self.minimum_bandwidth_in_KBs)
