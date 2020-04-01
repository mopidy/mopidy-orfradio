import os


class HttpClientMock:
    def __init__(self):
        thisdir = os.path.dirname(__file__)
        self.urlMappings = {
            "http://audioapi.orf.at/oe1/json/2.0/broadcasts/": f"{thisdir}/broadcasts.json",  # noqa: B950
            "https://audioapi.orf.at/oe1/api/json/4.0/broadcast/475617/20170604": f"{thisdir}/broadcast475617.json",  # noqa: B950
        }

    def get(self, url):
        file_name = self.urlMappings[url]
        with open(file_name) as content_file:
            return content_file.read()
