# -*- coding: utf-8 -*-
from scrapy.spider import *
from scrapy.selector import *
from scrapy.http import Request, FormRequest, HtmlResponse
from scrapy.conf import settings
from scrapy.item import Item, Field
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc

from configobj import ConfigObj
from crawler.items import CommonItem
from crawler.utils import *

import httplib
import urllib
import cookielib
import urlparse
import os
import re
import sys
import datetime
import itertools
import random
import hashlib
import copy

class DataNode:
    def __init__(self,name):
        self.name=name
        self.parent = None
        self.children=set()
        self.url_patterns = set()
        self.restrict_xpaths = set()
        self.xpaths = set()
        self.incremental = False
    def addChild(self, child):
        self.children.add(child)
    def getChildren(self):
        return self.children
    def setParent(self, parent):
        if parent.name != self.name:
            self.parent = parent
    def setUrlPatterns(self, url_patterns):
        self.url_patterns = set(url_patterns)
    def getUrlPatterns(self):
        return self.url_patterns
    def setRestrictXPaths(self, restrict_xpaths):
        self.restrict_xpaths = set(restrict_xpaths)
    def getRestrictXPaths(self, restrict_xpaths):
        return self.restrict_xpaths
    def setXPaths(self, xpaths):
        self.xpaths = set(xpaths)
    def getXPaths(self):
        return self.xpaths
    def setIncremental(self, incremental):
        self.incremental = incremental
    def getIncremental(self, incremental):
        return self.incremental
    def __repr__(self):
        return"<DataNode %s>"%self.name

class XPath:
    def __init__(self):
        pass

    def eval(self):
        pass

try:
    BaseSpider = Spider
except:
    pass

class CommonSpider(BaseSpider):

    configs = load_configs()

    #settings applied to the spider
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

    item_fields = set()
    setting_vars = {}
    params = {}
    root_node = DataNode('root')
    site_tree = {'root':root_node}
    for cfg_key in spider_config.iterkeys():
        #初始化自定义变量
        if re.search('^\$',cfg_key):
            var_name = re.sub('^\$','',cfg_key)
            setting_vars[var_name] = spider_config[cfg_key]
        #/*------------初始化数据节点树 begin-------------------*/
        #初始化url种子列表
        if cfg_key.endswith('_url_pattern'):
            node_name = cfg_key.replace('_url_pattern', '')
            node_url_patterns = spider_config[cfg_key]
            if type(node_url_patterns) is not list:
                node_url_patterns = [node_url_patterns]
            if not site_tree.has_key(node_name):
                site_tree[node_name] = DataNode(node_name)
            node = site_tree[node_name]
            node.setUrlPatterns(node_url_patterns)
        if cfg_key.endswith('_restrict_xpaths'):
            node_name = cfg_key.replace('_restrict_xpaths', '')
            node_restrict_xpaths = spider_config[cfg_key]
            if type(node_restrict_xpaths) is not list:
                node_restrict_xpaths = [node_restrict_xpaths]
            if not site_tree.has_key(node_name):
                site_tree[node_name] = DataNode(node_name)
            node = site_tree[node_name]
            node.setRestrictXPaths(node_restrict_xpaths)
        if cfg_key.endswith('_incremental'):
            node_name = cfg_key.replace('_incremental', '')
            node_incremental = spider_config[cfg_key]
            if not site_tree.has_key(node_name):
                site_tree[node_name] = DataNode(node_name)
            node = site_tree[node_name]
            if node_incremental == 'yes':
                node.setIncremental(True)
        #/*------------初始化数据节点树 end-------------------*/
    params = setting_vars.copy()
  
    for k,v in site_tree.items():
        if k+'_content' in spider_config:
            node_contents = spider_config[k+'_content']
            if type(node_contents) is not list:
                node_contents = [node_contents]
            for node_content in node_contents:
                if not site_tree.has_key(node_content):
                    site_tree[node_content] = DataNode(node_content)
                #数据项定义
                if spider_config.has_key(node_content) or spider_config.has_key('item_'+node_content+'_xpaths'):
                    field_xpaths = spider_config[node_content] if spider_config.has_key(node_content) else spider_config['item_'+node_content+'_xpaths']
                    if type(field_xpaths) is not list:
                        field_xpaths = [field_xpaths]
                    site_tree[node_content].setXPaths(field_xpaths)
                    item_fields.add(node_content)
                    if not CommonItem().fields.has_key(node_content):
                        CommonItem().fields[node_content] = Field()
                v.addChild(site_tree[node_content])
                site_tree[node_content].setParent(v)
    
    item_fields.add('url')
    CommonItem().fields['url'] = Field()

    for k,v in site_tree.iteritems():
        if not v.parent and v.name != 'root':
            v.parent = site_tree['root']
            site_tree['root'].addChild(v)

    for item_field in item_fields:
        if not CommonItem().fields.has_key(item_field):
            CommonItem().fields[item_field] = {}

    name = spider_name
    allowed_domains = spider_config['allowed_domains']
    if type(allowed_domains) is not list:
        allowed_domains = [allowed_domains]

    start_urls = spider_config['start_urls']
    if type(start_urls) is not list:
        start_urls = [start_urls]

    start_urls = tuple(start_urls)

    items = {}
    queue = {}

    def __init__(self, *a, **kw):
        super(CommonSpider, self).__init__(*a, **kw)

    def _eval_xpath(self,hxs,xpath):
        """ 获得xpath表达式语句
        """
        ret_val = ''
        if xpath.find('&') > -1:
            m = re.search(r'<<(.+)&(.*)>>',xpath)
            xpath_ex = m.group(1)
            reg_ex = m.group(2)
            ret_val +=   hxs + """.select('""" + xpath_ex + """').re('""" + reg_ex + """'.decode('utf8'))"""
        else:
            m = re.search(r'<<(.+)>>',xpath)
            xpath_ex = m.group(1)
            ret_val +=   hxs + """.select('""" + xpath_ex + """').extract()"""

        return ret_val

    def _join_lists(self, ls, linearity=False):
        """ 交叉连接,参数ls为需要做连接的list,linearity表示交叉连接是否线性的(一一对应)

        """
        ret_val = []
        for x in ls:
            if type(x) is not list:
                x = [x]
        #if len(ls) <= 1:
            #return ls
        if linearity == True:
            ret_val = itertools.imap(None,*ls)
            return tuple(ret_val)
        ret_val = itertools.product(*ls)
        return tuple(ret_val)

    def _process_ex(self, hxs, ex_str, url=None):
        """ 对表达式的处理
        """
        ret_val = ''
        exs = ex_str.split('~')
        ret_val += '['
        for i,ex in enumerate(exs):
            if ex.startswith('<<') and ex.endswith('>>'):
                ret_val += self._eval_xpath(hxs,ex)
            else:
                try:
                    #if ex.find('(')>-1 and ex.find(')')>-1:
                    try:
                        ret_val += '[u\'' + re.search(ex, url).group(1) + '\']'
                    #else:
                    except:
                        ret_val += '[u\'' + re.search(ex, url).group(0) + '\']'
                except:
                    ret_val += '[u\'' + ex + '\']'
            if i == len(exs)-1:
                ret_val += ']'
            else:
                ret_val += ','
        return ret_val

    def eval_custom_var(self, response, hxs, var):
        """ 计算自定义变量表达式的结果 
        """
        ret_val = []
        tmp_v = var[:]
        if type(tmp_v) is not list:
            tmp_v = [tmp_v]
        for i in xrange(len(tmp_v)):
            tmp_var = tmp_v[i].split('~')
            for j in xrange(len(tmp_var)):
                val = tmp_var[j]
                if val.find('{')>-1 and val.find('}')>-1:
                    val = eval(""" " """+val.replace('{','').replace('}','')+""" " """)
                if val.startswith('<<') and val.endswith('>>'):
                    rs_var = eval(self._eval_xpath('hxs',val))
                    if rs_var:
                        tmp_var[j] = rs_var
                else:
                    try:
                        rs_var = eval(val)
                        if rs_var:
                            tmp_var[j] = rs_var
                    except:
                        try:
                            rs_var = re.search(val,response.url)
                            if rs_var:
                                try:
                                    tmp_var[j] = rs_var.group(1)
                                except:
                                    tmp_var[j] = rs_var.group(0)
                        except:
                            pass
                if type(tmp_var[j]) is not list:
                    tmp_var[j] = [tmp_var[j]]
            tmp_v[i] = [''.join([unicode(_x) for _x in tmp_x]) for tmp_x in self._join_lists(tmp_var)]
        for tmp_x in tmp_v:
            if type(tmp_x) is list:
                ret_val += tmp_x
            else:
                ret_val.append(tmp_x)

        return ret_val


    def extract_url(self, response, hxs, url_pattern, restrict_xpaths, params):
        """ 提取Url
        """
        ret_urls = []
        length = 0
        tmp_urls = []
        exists = set()
        base_url = get_base_url(response)
        #TODO:exist_list_param handler
        if not restrict_xpaths:
            restrict_xpaths = ["<<//a/@href>>"]
        for restrict_xpath in restrict_xpaths:
            url_xpath = restrict_xpath
            closed_xpath = False
            if re.search('/([^/]+\(\).*>>)', restrict_xpath) or re.search('/@([^/]+>>)', restrict_xpath):
                closed_xpath = True
            if not closed_xpath:
                joint_xpath = ''
                level = 0
                while not self.eval_custom_var(response, hxs, restrict_xpath.replace('/>>','>>').replace('>>', joint_xpath+'/@href>>')) or self.eval_custom_var(response, hxs, restrict_xpath.replace('/>>','>>').replace('>>', joint_xpath+'/@href>>'))==[restrict_xpath.replace('/>>','>>').replace('>>', joint_xpath+'/@href>>')]:
                    joint_xpath += '/*'
                    level += 1
                    if level>=5:
                        break
                url_xpath = restrict_xpath.replace('/>>','>>').replace('>>', joint_xpath+'/@href>>')
            tmp_urls += self.eval_custom_var(response, hxs, url_xpath)
        sorted_tmp_urls = list(set(tmp_urls))
        sorted_tmp_urls.sort(key=tmp_urls.index)
        length = len(sorted_tmp_urls)
        _url_pattern = self.process_url_pattern(url_pattern, response, hxs)
        for i,tmp_url in enumerate(sorted_tmp_urls):
            #handle incomplete urls
            tmp_url = urljoin_rfc(base_url, tmp_url)
            try:
                if re.search(_url_pattern, tmp_url):
                    #if url_pattern.find("(")>-1 and url_pattern.find(")")>-1:
                    try:
                        tmp_url = re.search(_url_pattern, tmp_url).group(1)
                    #else:
                    except:
                        tmp_url = re.search(_url_pattern, tmp_url).group(0)
                else:
                    continue
            except:
                pass
            tmp_params = re.findall('\{([^\{\}]*)\}', tmp_url)
            processed_url = tmp_url
            if tmp_params:
                exist_invalid_param = False
                for tmp_param in tmp_params:
                    if not tmp_param or tmp_param not in self.params:
                        exist_invalid_param = True
                        print 'invalid param:%s'%tmp_param
                if exist_invalid_param:
                    break
                processed_url = [urlparse.urljoin(response.url, ''.join(x_url_parts)) for x_url_parts in self._join_lists(eval('[[\'' + tmp_url.replace('{','\'],').replace('}',',[\'') + '\']]'))]
            if type(processed_url) is list:
                for _url in processed_url:
                    if _url in exists:
                        processed_url.remove(_url)
                ret_urls += [[(i+1)*(j+1)-1,_url] for j,_url in enumerate(processed_url)]
            else:
                if not processed_url in exists:
                    ret_urls.append([i, processed_url])
                    exists.add(processed_url)
        #TODO:exist_list_param handler
        tmp_params = re.findall('\{([^\{\}]*)\}', url_pattern)
        if not ret_urls and (params or tmp_params):
            tmp_urls = [url_pattern]
            exist_invalid_param = False
            for tmp_param in tmp_params:
                if not tmp_param or tmp_param not in self.params:
                    exist_invalid_param = True
                    print 'invalid param:%s'%tmp_param
            if not tmp_params or exist_invalid_param:
                pass
            else:
                tmp_urls = [urljoin_rfc(base_url, ''.join(x_url_parts)) for x_url_parts in self._join_lists(eval('[[\'' + url_pattern.replace('{','\'],').replace('}',',[\'') + '\']]'))]
            lengh = len(tmp_urls)
            for i,tmp_url in enumerate(tmp_urls):
                ret_urls.append((i,tmp_url))
        ret_urls = [ret_url for ret_url in ret_urls if ret_url[1].find('http://')>-1]
        return length, ret_urls

    def generate_sign(self):
        sign = hashlib.sha1(str(random.random())).hexdigest()
        while self.items.has_key(sign):
            sign = hashlib.sha1(str(random.random())).hexdigest()
        return sign

    def parse_item_xpaths(self, hxs, xpaths, item, url, name, replace=False, allow_empty=True):
        _res = []
        for item_field_xpath in xpaths:
            item_field_xpath = item_field_xpath.replace('`',',')
            _res += self._join_lists(eval(self._process_ex('hxs',item_field_xpath, url=url)))

        joined_res = [''.join(_one) for _one in _res]
        if name.find("url")>-1:
            for i,joined_one in enumerate(joined_res):
                if not joined_one.startswith("http://"):
                    if not joined_one.startswith("/"):
                        joined_one = "/" + joined_one
                    joined_res[i] = urlparse.urljoin(url, joined_one)

        if item.has_key(name):
            if replace:
                if joined_res or allow_empty:
                    item[name] = joined_res
            else:
                if joined_res != item[name]:
                    item[name] += joined_res
        else:
            if joined_res or allow_empty:
                item[name] = joined_res


    def parse_multi_items(self, hxs, node, item, response, index, count):
        if node.restrict_xpaths:
            for child in node.children:
                if child.xpaths:
                    restrict_xpath = '|'.join([restrict_xpath.replace("<<", "").replace(">>", "") for restrict_xpath in node.restrict_xpaths])
                    try:
                        m = re.search(r'<<(.+)&(.*)>>',xpath)
                        restrict_xpath = m.group(1)
                    except:
                        pass
                    restrict_selectors = hxs.select(restrict_xpath)
                    #fetch multi items from one page
                    if index != None and len(restrict_selectors) > index and len(restrict_selectors)==count:
                        try:
                            XmlXPathSelector = Selector
                        except:
                            pass
                        restrict_hxs = XmlXPathSelector(HtmlResponse(response.url, body=re.sub('[\n\r\t]+', '', restrict_selectors[index].extract()), encoding='utf8'))
                        #restrict_hxs = restrict_selectors[index]
                        self.parse_item_xpaths(restrict_hxs, child.xpaths, item, response.url, child.name, True, False)

    def process_url_pattern(self, url_pattern, response, hxs):
        return ''.join(self._join_lists(eval('[[\'' + url_pattern.replace('{','\'],').replace('}',',[\'') + '\']]'))[0])

    def match_url_pattern(self, url_pattern, url):
        match = False
        _url_pattern =  url_pattern[:]
        if re.search('\{\w+\}', url_pattern):
            _url_pattern = re.sub('\{\w+\}', '\w+', url_pattern).replace('?', '\?')
        if re.search(_url_pattern, url):
            match = True
        return match

    def parse(self, response):
        if self.spider_config.has_key('encoding'):
            _encoding = self.spider_config['encoding']
            response = response.replace(encoding=_encoding)
        try:
            HtmlXPathSelector = Selector
        except:
            pass

        hxs = HtmlXPathSelector(response)

        curr_nodes = set()

        #tell the curr_node
        if 'node' in response.meta:
            curr_nodes = set(response.meta['node'])
        else:
            for key, node in self.site_tree.items():
                for url_pattern in node.url_patterns:
                    if self.match_url_pattern(url_pattern, response.url):
                        curr_nodes.add(node)

        if not curr_nodes:
            curr_nodes.add(self.site_tree['root'])

        #make a sign of the item (when??)
        #curr_sign = self.generate_sign()
        #if response.request.headers.has_key('Sign'):
            #curr_sign = response.request.headers['Sign']

        is_root = False
        for curr_node in curr_nodes:
            #if not curr_node.parent or curr_node.parent.name == 'root':
            if not curr_node.parent:
                is_root = True

        #fetch an item from self.items
        if 'item' in response.meta:
            if is_root:
                item = CommonItem()
            else:
                item = copy.deepcopy(response.meta['item'])
                #item = copy.deepcopy(self.items[curr_sign]['item'])
                #self.items[curr_sign]['req_count'] -= 1
                #if not self.items[curr_sign]['req_count']:
                    #self.items.pop(curr_sign)
        else:
            item = CommonItem()

        #解析自定义变量或参数
        for k,v in self.setting_vars.iteritems():
            tmp_v = self.eval_custom_var(response, hxs, v)
            self.params[k] = tmp_v
            if len(tmp_v) == 1:
                self.params[k] = tmp_v[0]
            globals()[k] = self.params[k]


        #解析url和数据项
        for curr_node in curr_nodes:
            if curr_node.incremental and 'exist_in_cache' in response.flags:
                yield None
            else:
                tail_branch = True
                no_yield = True
                if curr_node.name == 'item' and not item.has_key('url'):
                    item['url'] = [response.url]
                for child in curr_node.children:
                    #if child.children and child is not curr_node:
                    if child.children:
                        tail_branch = False
                    #解析数据项
                    if child.xpaths:
                        self.parse_item_xpaths(hxs, child.xpaths, item, response.url, child.name)
                for child in curr_node.children:
                    #parse multi items from one single page
                    curr_items = []
                    #if child.restrict_xpaths and child.parent and child.parent.name != 'root':
                    if child.restrict_xpaths:
                        tail_child = True
                        belongtos = []
                        for restrict_xpath in child.restrict_xpaths:
                            belongtos += self._join_lists(eval(self._process_ex('hxs',restrict_xpath)))
                        #for chd in child.children:
                            #if chd.children and chd is not child:
                                #tail_child = False
                        if child.url_patterns:
                            tail_child = False
                        for i in xrange(len(belongtos)):
                            new_item = copy.deepcopy(item)
                            #item_sign = self.generate_sign()
                            self.parse_multi_items(hxs, child, new_item, response, i, len(belongtos))
                            if tail_child and len(new_item) == len(self.item_fields):
                                yield new_item
                                no_yield = False
                            else:
                                curr_items.append(new_item)

                    #parse follow urls
                    if child.url_patterns:
                        restrict_xpaths = child.restrict_xpaths
                        prefix = child.name + "_"
                        pending_params = {}
                        for key,val in self.params.iteritems():
                            if key.startswith(prefix):
                                pending_params[key.replace(prefix,'')] = val
                        pending_urls = []
                        urls_len = 0
                        for url_pattern in child.url_patterns:
                            urls_length, url_list = self.extract_url(response, hxs, url_pattern, restrict_xpaths, pending_params)
                            urls_len += urls_length
                            pending_urls += url_list
                        if pending_params:
                            tmp_param_list = []
                            pending_params_keys = []
                            for k,v in pending_params.items():
                                pending_params_keys.append(k)
                                tmp_param_list.append(v)
                            tmp_seq_params = self._join_lists(tmp_param_list)
                            for i,pending_url in pending_urls:
                                #TODO:exist_list_param handler
                                for j,tmp_seq_param in enumerate(tmp_seq_params):
                                    #req_sign = self.generate_sign()
                                    req_item = copy.deepcopy(item)
                                    _tmp_param = {}
                                    for i, k in enumerate(pending_params_keys):
                                        _tmp_param[k] = tmp_seq_param[i]
                                    #Attach item sign with the request
                                    req = FormRequest(pending_url, method="POST", formdata=_tmp_param)
                                    #req.headers['Sign'] = req_sign
                                    #attach item with the request
                                    if 'item' not in req.meta:
                                        req.meta['item'] = req_item
                                    #if req_sign not in self.items:
                                        #self.items[req_sign] = {'item':req_item, 'req_count':0}
                                    #self.items[req_sign]['req_count'] += 1
                                    if 'node' not in req.meta:
                                        req.meta['node'] = []
                                    req.meta['node'].append(child)
                                    yield req
                                    no_yield = False
                        else:
                            for i,pending_url in pending_urls:
                                #req_sign = self.generate_sign()
                                req_item = copy.deepcopy(item)
                                if len(curr_items)==urls_len and i<urls_len:
                                    #req_sign = curr_items[i][0]
                                    req_item = curr_items[i]
                                #Attach item with the request
                                req = Request(pending_url)
                                #req.headers['Sign'] = req_sign
                                #attach item_sign with the item
                                if 'item' not in req.meta:
                                    req.meta['item'] = req_item
                                #if req_sign not in self.items:
                                    #self.items[req_sign] = {'item':req_item, 'req_count':0}
                                #self.items[req_sign]['req_count'] += 1
                                if 'node' not in req.meta:
                                    req.meta['node'] = []
                                req.meta['node'].append(child)
                                yield req
                                no_yield = False

                #decide when to yield the item
                if (no_yield or tail_branch) and len(item) == len(self.item_fields):
                    yield item

