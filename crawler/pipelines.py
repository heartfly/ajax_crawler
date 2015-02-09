# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from scrapy.exceptions import DropItem
from scrapy.http import Request

class CommonPipeline(object):
    def __init__(self):
        self.duplicates = {}
        dispatcher.connect(self.spider_opened, signals.spider_opened)
        dispatcher.connect(self.spider_closed, signals.spider_closed)

    def spider_opened(self, spider):
        self.duplicates[spider] = {}

    def spider_closed(self, spider):
        for k in self.duplicates[spider].keys():
            del self.duplicates[spider][k]
        del self.duplicates[spider]
        del self.duplicates

    def ensure_not_empty(self, item, field):
        if field in item:
            if item[field] ==[]:
                raise DropItem("Empty item found: %s" % item)

    def ensure_not_duplicate(self, spider, item, field):
        if field in item:
            if field not in self.duplicates[spider]:
                self.duplicates[spider][field] = set()
            if item[field] and type(item[field]) is list:
                if item[field][0] in self.duplicates[spider][field]:
                    raise DropItem("Duplicate item found: %s" % item)
                else:
                    self.duplicates[spider][field].add(item[field][0])

    def process_item(self, item, spider):
        self.ensure_not_empty(item, 'url')

        self.ensure_not_duplicate(spider, item, 'url')

        return item

