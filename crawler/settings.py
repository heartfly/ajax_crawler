# -*- coding: utf-8 -*-
# Scrapy settings for crawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
from configobj import ConfigObj

import os
import sys
import datetime
import re
from os.path import dirname

path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(path)
from utils import *

configs = load_configs()

#应用于此spider的配置
site_config = None
spider_name = None
spider_config = None
exist_site = False

for argv in sys.argv:
    for config in configs:
        if argv in config:
            exist_site = True
            spider_name = argv
            site_config = config
            spider_config = site_config[spider_name]

BOT_NAME = 'AjaxSpider'
#BOT_VERSION = '2.0'

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'
DEFAULT_ITEM_CLASS = 'crawler.items.CommonItem'
#USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)
#USER_AGENT = 'Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.2.3) Gecko/%s Fedora/3.6.3-4.fc13 Firefox/3.6.3' % (datetime.date.today().strftime("%Y%m%d"))
USER_AGENT = 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'
#USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.54 Safari/536.5'

LOG_FILE=(CRAWLER_DIR + '/log/'+ spider_name + '_log_'+datetime.date.today().strftime("%Y%m%d")+'.log')

ITEM_PIPELINES = {
    'crawler.pipelines.CommonPipeline':300,
}

if spider_config.has_key('download_delay'):
    DOWNLOAD_DELAY = float(spider_config['download_delay'])
else:
    DOWNLOAD_DELAY = 0.25
RANDOMIZE_DOWNLOAD_DELAY = True

print spider_config.keys()
if spider_config.has_key('js_parser') and spider_config['js_parser']=='on':
    DOWNLOADER_MIDDLEWARES = {
        'crawler.downloader.WebkitDownloader': 543,
    }

incremental = False
for cfg_key in spider_config.iterkeys():
    if cfg_key.endswith('_incremental') and spider_config[cfg_key]=='yes':
        incremental = True
        break
if incremental:
    print 'incremental is : ON'
    HTTPCACHE_EXPIRATION_SECS = 172800
    FEED_STORE_EMPTY = True
    DOWNLOADER_MIDDLEWARES = {
        'crawler.incremental.IncrementalDownloader': 544,
    }

RETRY_HTTP_CODES = [500, 503, 504, 400, 408]
if spider_config.has_key('ignore_http_code'):
    RETRY_HTTP_CODES.remove(int(spider_config['ignore_http_code']))

os.environ["DISPLAY"] = ":2"

COOKIES_ENABLED = True
COOKIES_DEBUG = True
