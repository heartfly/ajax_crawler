# -*- coding: utf-8 -*-
from configobj import ConfigObj

import os
import sys
import urlparse
import re

from os.path import dirname
path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(path)

CRAWLER_DIR = dirname(path)
print CRAWLER_DIR

def load_configs():
    filenames = []
    try:
        cfg_dir = CRAWLER_DIR + '/configs/'
        if CRAWLER_DIR.startswith("~"):
            filenames += [ os.path.expanduser(cfg_dir) + filename for filename in os.listdir(os.path.expanduser(cfg_dir)) ]
        else:
            filenames += [ cfg_dir + filename for filename in os.listdir(cfg_dir) ]
    except Exception,e:
        print e

    cfg_list = []
    for filename in filenames:
        if re.search('\.cfg$',filename) != None:
            cfg_list.append(filename)

    configs = []
    for cfg in cfg_list:
        try:
            configs.append(ConfigObj( cfg, encoding='utf8'))
        except Exception,e:
            print e
            print "error occured when reading config file @" + cfg

    return configs

configs = load_configs()
#应用于此spider的配置
site_config = None
spider_name = None
spider_config = None
exist_site = False

print sys.argv
for argv in sys.argv:
    for config in configs:
        if argv in config:
            exist_site = True
            spider_name = argv
            site_config = config
            spider_config = site_config[spider_name]

if exist_site == False:
    if 'crawl' in sys.argv:
        print "Unable to find spider: " + sys.argv[sys.argv.index('crawl') + 1]
        sys.exit()
    else:
        try:
            net_loc = urlparse.urlsplit(sys.argv[sys.argv.index('shell') + 1]).netloc
            site_name = re.search('([^\.]+)\.[^\.]+$',net_loc).group(1)
            for config in configs:
                if site_name in config:
                    spider_name = site_name
                    site_config = config
                    spider_config = site_config[spider_name]
                    exist_site = True
            if exist_site == False:
                spider_name = configs[0].keys()[0]
                site_config = configs[0]
                spider_config = site_config[spider_name]
        except:
            print "Unable to resolve the commands"
            sys.exit()
