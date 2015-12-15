ajax_crawler
============

A flexible web crawler based on Scrapy for fetching most of Ajax or other various types of web pages. 

Easy to use: To customize a new web crawler, You just need to write a config file and run.

# Usage
* Edit A Config File In The 'Configs' Directory
```shell
cd configs
touch xxx.cfg
vim xxx.cfg
```
like this
```INI
[dianping_beijingyumao] # crawler name, should be the same as config file name.
allowed_domains = dianping.com # domain name, can be a list.
start_urls = http://www.dianping.com/search/category/2/45/g152 # start url, should be a certain url.
list_url_pattern = .*category/2/45/g152[p\d]* # list url pattern # list url patern, you can use regular expressions here.
list_restrict_xpaths = '<<//div[@class="page"]//a/@href>>' # list restrict xpaths, we use this to find item urls.
list_content = list,item # decide what kind of content you can find in the list restrict xpaths.
item_url_pattern = .*shop/\d+ # item url patter, you can use regular expressions here.
item_restrict_xpaths = <<//div[@class="tit"]>> # item restrict xpaths, we use this to find item contents.
item_content = name,address,region,intro,phone_num,cover_image,hours,sport # decide what field names can find in the item_restrict_xpaths.
#item_incremental = yes # decide this crawler should be incremental (should use cache)
item_name_xpaths = <<//h1[@class="shop-title"]/text()>> # we can find item content in the item field xpaths
item_address_xpaths = <<//span[@itemprop="street-address"]/text()>>
item_region_xpaths = <<//span[@class="region"]/text()>>
item_phone_num_xpaths = <<//span[@itemprop="tel"]/text()>>
item_cover_image_xpaths = <<//img[@itemprop="photo"]/@src>>
item_hours_xpaths = <<//div[@class="desc-info"]//ul/li/span[@class="J_full-cont"]/text()>>
item_sport_xpaths = "羽毛球" # also can be a certain string
download_delay = 5 # downlaod delay to reduce crawling frequency
```
* Then Just Run The Crawler
```bash
scrapy crawl xxx
```
