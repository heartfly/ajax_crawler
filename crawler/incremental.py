#coding=utf8
from scrapy.contrib.downloadermiddleware.httpcache import FilesystemCacheStorage
from scrapy.utils.httpobj import urlparse_cached
from scrapy.exceptions import IgnoreRequest
import settings

class IncrementalDownloader(object):

    storage = None
    storage_class = FilesystemCacheStorage
    ignore_schemes = []
    ignore_http_codes = []    

    def _get_storage(self, spider):
        return self.storage_class(spider.settings)

    def process_response(self, request, response, spider):
        if not self.storage:
            self.storage = self._get_storage(spider)
            if not self.ignore_schemes:
                self.ignore_schemes = spider.settings.getlist('HTTPCACHE_IGNORE_SCHEMES')
            if not self.ignore_http_codes:
                self.ignore_http_codes = map(int, spider.settings.getlist('HTTPCACHE_IGNORE_HTTP_CODES'))
        cached_response = self.storage.retrieve_response(spider, request)
        if cached_response and cached_response.body == response.body:
            # return what if exist??
            response.flags.append('exist_in_cache')
            # raise IgnoreRequest
        if self.is_cacheable(request) and self.is_cacheable_response(response):
            self.storage.store_response(spider, request, response)
        return response

    def is_cacheable_response(self, response):
        return response.status not in self.ignore_http_codes

    def is_cacheable(self, request):
        return urlparse_cached(request).scheme not in self.ignore_schemes
