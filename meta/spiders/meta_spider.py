#encoding:utf-8
import os
import urlparse
import codecs
import sys
import json
import re
import math
import time
import datetime
from bs4 import BeautifulSoup

from scrapy.selector import Selector
from scrapy.http import Request,FormRequest
from scrapy.spider import Spider
from scrapy.conf import settings
from scrapy import log
from scrapy.signalmanager import SignalManager
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

from meta.receive_conf import receive_conf
from meta.config import *
from meta.item import *
from meta.format_time import format_time
from meta.meta_util import *
import meta.redis_api as redis
reload(sys)
sys.setdefaultencoding('utf-8')

def get_redis_key(template_name):
    template_name = os.path.basename(template_name)
    redis_keyword = template_name.split('.')[0]
    time_flag = datetime.datetime.now().strftime('%m%d%H')
    return redis_keyword+time_flag

class MetaSpider(Spider):
    
    name = 'meta'
    def __init__(self,**kwargs):
        
        if not 'config' in kwargs:
            err =  'failed to find seed file (config=*.conf)'
            print err
#         if not 'keywords' in kwargs:
#             err =  'failed to find seed file (keywords=*.dat)'
#             print err
        config = kwargs['config']
#         self.keywords = kwargs['keywords']
        self.load_conf(config)
        if self.Sleep_Flag=='SEARCH_ENGINE_SLEEP' or self.Sleep_Flag=='true' or not self.Sleep_Flag:
            settings.set('RANDOMIZE_DOWNLOAD_DELAY', True, priority='cmdline')
            settings.set('DOWNLOAD_DELAY', float(self.SE_Sleep_Base), priority='cmdline')
        else:
            settings.set('RANDOMIZE_DOWNLOAD_DELAY', False, priority='cmdline')
        
        log_filename = self.conf_name.replace('.conf','')+'.log'
        settings.set('LOG_FILE', log_filename, priority='cmdline')
        #redis key
        self.meta_next_url = meta_redis_key()
        #初始化redis
        self.init_redis()
        self.redis_keyword = get_redis_key(self.conf_name)
        #注册signal
        sig = SignalManager(dispatcher.Any)
        sig.connect(self.idle,signal=signals.spider_idle)
        self.metatime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #保存该次获取的url，用于判断该次抓取是否和上次重复{keyword:md5(url)}
        self.urlmd5 = dict()
        self.log_writer = open('log.dat','a+') 
        self.date_from_url_re = re.compile("[-_/][a-zA-Z]*[-_]?(?P<year>(20)?([0-1][0-9]))([-_/])?(?P<m>(10|11|12|(0?[1-9])){1})([-_/])?(?P<day>(10|20|30|31|([0-2]?[1-9])){1})([-_/])")
    def start_requests(self):
        reqs = self.make_reqs_by_keyword(1)
        log.msg('start_requests:  %s'%(str(reqs)),log.INFO)
        return reqs
    
    def make_reqs_by_keyword(self,num):
        reqs = []
        cookie = self.load_cookie()
        ostart_page = self.OStart_Page
        start_page = self.Start_Page 
        keywords = self.get_keywords(num)
        searchtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for keyword in keywords:
            #url = self.Url_Front_Part + keyword + self.Url_Rear_Part
            url = self.Url_Front_Part + keyword.decode('utf-8').encode(self.Query_Encoding) + self.Url_Rear_Part
            cur_page = 0
            if start_page:
                url = url + self.Url_Change_page + start_page
                cur_page  = start_page
            else:
                url = url + self.Url_Change_page + ostart_page
                cur_page = ostart_page
            if cookie:
                req = Request(url,cookies=cookie,meta={'keyword':keyword.decode('utf-8'),'cur_page':cur_page,'searchtime':searchtime})
            else:
                req = Request(url,meta={'keyword':keyword.decode('utf-8'),'cur_page':cur_page,'searchtime':searchtime})
            reqs.append(req)
        return reqs
    
    def idle(self,spider):
        log.msg('catch idle signal...',log.INFO)
        if spider != self:
            return
        time.sleep(5)
        req = self.create_request()
        if req:
            self.crawler.engine.crawl(req, spider)
    
    def create_request(self):
        reqs = self.make_reqs_by_keyword(1)
        if reqs:
            return reqs[0]
        else:
            return 
            
    def init_redis(self):
        self.redis_conn = redis.redis_connect()
        redis.set_expire_time(self.redis_conn, self.meta_next_url, EFFECTIVE_TIME)
        
        
    def load_xpath(self):
        self.xpaths = dict()
        self.xpaths_num = dict()
        self.xpaths_split = dict()
        self.xpaths_split_num = dict()
        
        #U T D A B P C R S
        #xpath:xpath选择器
        self.xpaths.update({'U':self.params.get('Url_XPath',None)})
        self.xpaths.update({'T':self.params.get('Title_Xpath',None)})
        self.xpaths.update({'D':self.params.get('Date_Xpath',None)})
        self.xpaths.update({'A':self.params.get('Author_Xpath',None)})
        self.xpaths.update({'B':self.params.get('Abstract_Xpath',None)})
        self.xpaths.update({'P':self.params.get('Copy_Url_Xpath',None)})
        self.xpaths.update({'C':self.params.get('Click_Xpath',None)})
        self.xpaths.update({'R':self.params.get('Reply_Xpath',None)})
        self.xpaths.update({'S':self.params.get('Source_Xpath',None)})
        self.xpaths.update({'I':self.params.get('Id_Xpath',None)})
        #xpath_num：取xpath选择器的第几个值，默认取0
        self.xpaths_num.update({'U':self.params.get('Url_XPath_Num',0)})
        self.xpaths_num.update({'T':self.params.get('Title_Xpath_Num',0)})
        self.xpaths_num.update({'D':self.params.get('Date_Xpath_Num',0)})
        self.xpaths_num.update({'A':self.params.get('Author_Xpath_Num',0)})
        self.xpaths_num.update({'B':self.params.get('Abstract_Xpath_Num',0)})
        self.xpaths_num.update({'P':self.params.get('Copy_Url_Xpath_Num',0)})
        self.xpaths_num.update({'C':self.params.get('Click_Xpath_Num',0)})
        self.xpaths_num.update({'R':self.params.get('Reply_Xpath_Num',0)})
        self.xpaths_num.update({'S':self.params.get('Source_Xpath_Num',0)})
        self.xpaths_num.update({'I':self.params.get('Id_Xpath_Num',0)})
        #xpath_split：是否需要对xpath选择器选择出来的值进行split，默认不需要
        self.xpaths_split.update({'U':self.params.get('Url_XPath_Split',None)})
        self.xpaths_split.update({'T':self.params.get('Title_Xpath_Split',None)})
        self.xpaths_split.update({'D':self.params.get('Date_Xpath_Split',None)})
        self.xpaths_split.update({'A':self.params.get('Author_Xpath_Split',None)})
        self.xpaths_split.update({'B':self.params.get('Abstract_Xpath_Split',None)})
        self.xpaths_split.update({'P':self.params.get('Copy_Url_Xpath_Split',None)})
        self.xpaths_split.update({'C':self.params.get('Click_Xpath_Split',None)})
        self.xpaths_split.update({'R':self.params.get('Reply_Xpath_Split',None)})
        self.xpaths_split.update({'S':self.params.get('Source_Xpath_Split',None)})
        self.xpaths_split.update({'I':self.params.get('Id_Xpath_Split',None)})
        #xpath_split_num：取经过split之后的第几个值，默认为0
        self.xpaths_split_num.update({'U':self.params.get('Url_XPath_Split_Num',0)})
        self.xpaths_split_num.update({'T':self.params.get('Title_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'D':self.params.get('Date_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'A':self.params.get('Author_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'B':self.params.get('Abstract_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'P':self.params.get('Copy_Url_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'C':self.params.get('Click_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'R':self.params.get('Reply_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'S':self.params.get('Source_Xpath_Split_Num',0)})
        self.xpaths_split_num.update({'I':self.params.get('Id_Xpath_Split_Num',0)})
        #是否需要对原始网页进行分组，若Item_Xpath为空，则不分组
        '''
            items = sel.xpath(self.Item_Xpath)
                for item in items:
                    item.xpath(...)
                    ...
        '''
        self.Item_Xpath = self.params.get('Item_Xpath',None)
                
        #next_page：选择下一页链接的xpath
        #主要用于判断下一页是否存在
        #若Next_Page_Xpath为空，则此参数无效
        self.Next_Page_Xpath = self.params.get('Next_Page_Xpath',None)
        self.Next_Page_Xpath_Num = self.params.get('Next_Page_Xpath_Num',0)
        
    def load_find(self):
        self.find_start = dict()
        self.find_end = dict()
        
        #U T D A B P C R S
        #start
        self.find_start.update({'U':self.params.get('Url_Start',None)})
        self.find_start.update({'T':self.params.get('Title_Start',None)})
        self.find_start.update({'D':self.params.get('Date_Start',None)})
        self.find_start.update({'A':self.params.get('Author_Start',None)})
        self.find_start.update({'B':self.params.get('Abstract_Start',None)})
        self.find_start.update({'P':self.params.get('Copy_Start',None)})
        self.find_start.update({'C':self.params.get('Click_Start',None)})
        self.find_start.update({'R':self.params.get('Reply_Start',None)})
        self.find_start.update({'S':self.params.get('Source_Start',None)})
        self.find_start.update({'I':self.params.get('Id_Start',None)})
        #end
        self.find_end.update({'U':self.params.get('Url_End',None)})
        self.find_end.update({'T':self.params.get('Title_End',None)})
        self.find_end.update({'D':self.params.get('Date_End',None)})
        self.find_end.update({'A':self.params.get('Author_End',None)})
        self.find_end.update({'B':self.params.get('Abstract_End',None)})
        self.find_end.update({'P':self.params.get('Copy_End',None)})
        self.find_end.update({'C':self.params.get('Click_End',None)})
        self.find_end.update({'R':self.params.get('Reply_End',None)})
        self.find_end.update({'S':self.params.get('Source_End',None)})
        self.find_end.update({'I':self.params.get('Id_End',None)})
    
    def load_select_type(self):
        #使用的选择器类型 xpath/find
        self.select_type = dict()
        
        #U T D A B P C R S
        self.select_type.update({'U':self.params.get('Url_Selector','xpath')})
        self.select_type.update({'T':self.params.get('Title_Selector','xpath')})
        self.select_type.update({'D':self.params.get('Date_Selector','xpath')})
        self.select_type.update({'A':self.params.get('Author_Selector','xpath')})
        self.select_type.update({'B':self.params.get('Abstract_Selector','xpath')})
        self.select_type.update({'P':self.params.get('Copy_Selector','xpath')})
        self.select_type.update({'C':self.params.get('Click_Selector','xpath')})
        self.select_type.update({'R':self.params.get('Reply_Selector','xpath')})
        self.select_type.update({'S':self.params.get('Source_Selector','xpath')})
        self.select_type.update({'I':self.params.get('Id_Selector','xpath')})
    
    def load_xpath_bs4(self):
        self.xpath_bs4 = dict()
        
        #xpath_bs4:是否需要使用bs4
        self.xpath_bs4.update({'U':self.params.get('Url_XPath_Bs4',None)})
        self.xpath_bs4.update({'T':self.params.get('Title_Xpath_Bs4',None)})
        self.xpath_bs4.update({'D':self.params.get('Date_Xpath_Bs4',None)})
        self.xpath_bs4.update({'A':self.params.get('Author_Xpath_Bs4',None)})
        self.xpath_bs4.update({'B':self.params.get('Abstract_Xpath_Bs4',None)})
        self.xpath_bs4.update({'P':self.params.get('Copy_Url_Xpath_Bs4',None)})
        self.xpath_bs4.update({'C':self.params.get('Click_Xpath_Bs4',None)})
        self.xpath_bs4.update({'R':self.params.get('Reply_Xpath_Bs4',None)})
        self.xpath_bs4.update({'S':self.params.get('Source_Xpath_Bs4',None)})
        self.xpath_bs4.update({'I':self.params.get('Id_Xpath_Bs4',None)})
    
    def load_re_pattern(self):
        self.re_pattern = dict()
        
        #xpath_bs4:是否需要使用正在表达式对xpath结果进行筛选
        self.re_pattern.update({'U':self.params.get('Url_XPath_RE',None)})
        self.re_pattern.update({'T':self.params.get('Title_Xpath_RE',None)})
        self.re_pattern.update({'D':self.params.get('Date_Xpath_RE',None)})
        self.re_pattern.update({'A':self.params.get('Author_Xpath_RE',None)})
        self.re_pattern.update({'B':self.params.get('Abstract_Xpath_RE',None)})
        self.re_pattern.update({'P':self.params.get('Copy_Url_Xpath_RE',None)})
        self.re_pattern.update({'C':self.params.get('Click_Xpath_RE',None)})
        self.re_pattern.update({'R':self.params.get('Reply_Xpath_RE',None)})
        self.re_pattern.update({'S':self.params.get('Source_Xpath_RE',None)})
        self.re_pattern.update({'I':self.params.get('Id_Xpath_RE',None)})
    
    def load_conf(self,filename):
        self.conf = receive_conf(filename)
        self.conf_name = self.conf[0]
        self.params = self.conf[1]
        
        self.load_xpath()
        self.load_find()
        self.load_select_type()
        self.load_xpath_bs4()
        self.load_re_pattern()
        #需要的结果：U T D A B P C R S
        self.Result_Order = self.params['Result_Order']
        #网站类型
        self.Site_Type = self.params['Site_Type']
        #url
        self.Query_Encoding = self.params.get('Query_Encoding','utf-8')
        self.Url_Front_Part = self.params['Url_Front_Part']
        self.Url_Rear_Part = self.params['Url_Rear_Part']
        self.Url_Change_page = self.params['Url_Change_page']
        self.Url_Check_Tag = self.params.get('Url_Check_Tag',None)
        self.Query_Skip_Items = self.params.get('Query_Skip_Items',1)
        self.OStart_Page = self.params.get('OStart_Page','1')
        self.Start_Page = self.params.get('Start_Page',None)
        #sleep
        self.Sleep_Flag = self.params.get('Sleep_Flag','true')
        self.SE_Sleep_Base = self.params.get('SE_Sleep_Base',30)
        #回溯日期
        self.Start_Day = self.params.get('Start_Day',None)
        self.Start_Month = self.params.get('Start_Month',None)
        self.Start_Year = self.params.get('Start_Year',None)
        #stop
        self.Check_Article_Time = self.params.get('Check_Article_Time','true')
#         if not self.Check_Article_Time:
#             self.Check_Article_Time = 'true'
        #total pages
        self.Crawle_Total_Pages = self.params.get('Crawle_Total_Pages',None)
        #max page
        self.Max_Page = int(self.params.get('Max_Page',20))
	#print 'Max_Page: ',self.Max_Page
        
    def load_keywords(self):
        res = []
        f = open(self.keywords,'r')
        keywords = f.readlines()
        for keyword in keywords:
            res.append(keyword.strip().decode('utf-8').encode(self.Query_Encoding))
        return res
    
    def get_keywords(self,num):
        keywords = redis.get_urls(self.redis_conn, num, self.redis_keyword)
        return keywords
    
    def load_cookie(self):
        cookie = load_cookie(self.conf_name)
        return cookie
    
    def get_timestamp(self):
        today_timestamp,yesterday_timestamp,twodaysago_timestamp = get_timestamp()
        return today_timestamp,yesterday_timestamp,twodaysago_timestamp
    
    def datetime_to_timestamp(self,posttime):
        return time.mktime(posttime.timetuple())
    
    def get_cur_item(self,results=[],res_num=''):
        res = get_cur_item(results, res_num)
        return res
    
    def selector(self,sel,item,Tag):
        select_type = self.select_type[Tag]
        if select_type!='find':
            tmp = sel.xpath(self.xpaths[Tag]).extract()
            result = get_cur_item(tmp,self.xpaths_num[Tag])
            if self.xpaths_split[Tag]:
                result_tmp = result.split(unicode(self.xpaths_split[Tag]))
                result = get_cur_item(result_tmp, self.xpaths_split_num[Tag])
            if self.re_pattern[Tag]:
                result_re = re.compile(self.re_pattern[Tag])
                result = result_re.search(result).group()
            if self.xpath_bs4[Tag]:
                result = ''.join(BeautifulSoup(result).findAll(text=True))
        else:
            content = item
            start = self.find_start[Tag].decode('utf-8')
            end = self.find_end[Tag].decode('utf-8')
            start_pos = content.find(start)
            tmp_content = content[(start_pos+len(start)):]
            end_pos = tmp_content.find(end)
            result = tmp_content[:end_pos]
            if self.xpaths_split[Tag]:
                result_tmp = result.split(unicode(self.xpaths_split[Tag]))
                result = get_cur_item(result_tmp, self.xpaths_split_num[Tag])
            if self.re_pattern[Tag]:
                result_re = re.compile(self.re_pattern[Tag])
                result = result_re.search(result).group()
            if self.xpath_bs4[Tag]:
                result = ''.join(BeautifulSoup(result).findAll(text=True))
        if result:
            result = result.replace(u'\xa0',' ').replace('\r\n','\n').strip().replace('\n','')
        return result
    
    def calculate_url(self,base,url_tmp):
        if not url_tmp or url_tmp.startswith('#'):
            return ''
        if url_tmp.startswith('http://') or url_tmp.startswith('https://'):
            if self.Url_Check_Tag:
                pos = url_tmp.find(self.Url_Check_Tag)
                if pos!=-1:
                    url_tmp = url_tmp[:pos]
            return url_tmp
        url = urlparse.urljoin(base,url_tmp)
        if url == base:
            return ''
        if self.Url_Check_Tag:
            pos = url.find(self.Url_Check_Tag)
            if pos!=-1:
                url = url[:pos]
        return url
    
    def get_next_page(self,keyword,cur_page):
        cur = (int(cur_page)+1)*int(self.Query_Skip_Items)
        url = self.Url_Front_Part + keyword.encode(self.Query_Encoding) + self.Url_Rear_Part + self.Url_Change_page + str(cur) 
        return url
    
    def next_urls(self,keyword,cur_page):
        url_maps = {}
        if self.Crawle_Total_Pages:
            curpage = 2
            if cur_page==0:
                curpage = 1
            for _ in range(int(self.Crawle_Total_Pages)-1):
                cur = curpage*int(self.Query_Skip_Items)
                url = self.Url_Front_Part + keyword.encode(self.Query_Encoding) + self.Url_Rear_Part + self.Url_Change_page + str(cur)
                url_maps.update({curpage:url})
                curpage +=1
        else:
            curpage = int(cur_page)+1
            for _ in range(5):
                cur = curpage*int(self.Query_Skip_Items)
                url = self.Url_Front_Part + keyword.encode(self.Query_Encoding) + self.Url_Rear_Part + self.Url_Change_page + str(cur)
                url_maps.update({curpage:url})
                curpage +=1
        url_maps_list = sorted(url_maps.iteritems(), reverse=False)
        return url_maps_list
    
    def make_next_request(self,keyword,cur_page,searchtime):
        next_urls = self.next_urls(keyword, cur_page)
#         print "next_urls: ",next_urls
        cookie = self.load_cookie()
        reqs = []
        for cur_page,next_url in next_urls:
#             print next_url
            if redis.check_set_value(self.redis_conn, self.meta_next_url, next_url):
                continue
            if cookie:
                req = Request(next_url,cookies=cookie,meta={'keyword':keyword,'cur_page':cur_page,'searchtime':searchtime})
                redis.add_set_value(self.redis_conn, self.meta_next_url, next_url)
                reqs.append(req)
            else:
                req =  Request(next_url,meta={'keyword':keyword,'cur_page':cur_page,'searchtime':searchtime})
                redis.add_set_value(self.redis_conn, self.meta_next_url, next_url)
                reqs.append(req)
        return reqs

    def judge_url_duplicate(self,keyword,current_crawler_url):
        urlmd5 = md5(current_crawler_url)
        his_urlmd5 = self.urlmd5.get(keyword,'')
        if not his_urlmd5:
            self.urlmd5.update({keyword:urlmd5})
        else:
            if urlmd5==his_urlmd5:
                return False
            self.urlmd5.update({keyword:urlmd5})
        return True
                
    def parse(self,response):
        keyword = response.request.meta.get('keyword')
        cur_page = response.request.meta.get('cur_page')
        searchtime = response.request.meta.get('searchtime')
        url = response.url
        log.msg('response url: %s'%(response.url),log.INFO)
#         print 'cur_page: ',cur_page
#         print url
        try:
            content = response.body_as_unicode()
        except:
            content = response.body
        
        content = clear_html_comment(content)
        content = special_require_content(content,self.conf_name)
        sel = Selector(text=content)
        order_result = self.Result_Order.upper()
#         print 'order_result: ',order_result
        last_artilce_time = 0
        items = sel.xpath(self.Item_Xpath).extract()
	whether_get_next_page = 0
        current_crawler_url = ''
        for item in items:
            metareslt = MetaResult()
            metareslt['template_name'] = self.conf_name
            metareslt['template_type'] = self.Site_Type
            metareslt['keyword'] = keyword
            metareslt['meta_pages'] = cur_page
            metareslt['searchtime'] = searchtime
            metareslt['metatime'] = self.metatime
            
            item_sel = Selector(text=item)
            result_item = []
            itemurl = ''
            if order_result.find('U')!=-1:
                url = self.selector(item_sel, item, 'U')
                if not url or url.startswith('#'):
                    continue
                url = self.calculate_url(response.url, url)
                domain = urlparse.urlparse(url).hostname
                metareslt['domain'] = domain
                metareslt['url'] = url
                current_crawler_url += url
                result_item.append('U')
                itemurl = url
		whether_get_next_page += 1
            if  order_result.find('T')!=-1:
                title = self.selector(item_sel, item, 'T')
                metareslt['title'] = title
                result_item.append('T')
            if  order_result.find('D')!=-1:
                date_re = self.date_from_url_re.search(itemurl)
                if date_re:
                    try:
                        url_date = date_re.groupdict()
                        posttime = url_date['year']+'-'+url_date['m']+'-'+url_date['day']
                        #筛选出的posttime有可能不对，则取last_artilce_time会抛出异常
                        last_artilce_time = datetime.datetime(* time.strptime(posttime, "%Y-%m-%d")[:6])
                    except:
                        posttime = self.selector(item_sel, item, 'D')
                        posttime = format_time(posttime, time.time())
                        last_artilce_time = posttime
                        if posttime:
                            posttime = posttime.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    posttime = self.selector(item_sel, item, 'D')
                    posttime = format_time(posttime, time.time())
                    last_artilce_time = posttime
                    if posttime:
                        posttime = posttime.strftime('%Y-%m-%d %H:%M:%S')
                metareslt['posttime'] = posttime
                result_item.append('D')
            if  order_result.find('A')!=-1:
                author = self.selector(item_sel, item, 'A')
                metareslt['author'] = author
                result_item.append('A')
            if  order_result.find('B')!=-1:
                abstract = self.selector(item_sel, item, 'B')
                metareslt['abstract'] = abstract
                result_item.append('B')
            if  order_result.find('C')!=-1:
                click = self.selector(item_sel, item, 'C')
                metareslt['click_count'] = click
                result_item.append('C')
            if  order_result.find('R')!=-1:
                reply = self.selector(item_sel, item, 'R')
                metareslt['comment_count'] = reply
                result_item.append('R')
            if  order_result.find('P')!=-1:
                copy_url = self.selector(item_sel, item, 'P')
                copy_url = self.calculate_url(response.url, copy_url)
                metareslt['copy_url'] = copy_url
                result_item.append('P')
            if  order_result.find('S')!=-1:
                source = self.selector(item_sel, item, 'S')
                metareslt['source'] = source
                result_item.append('S')
            if  order_result.find('I')!=-1:
                id = self.selector(item_sel, item, 'I')
                metareslt['id'] = id
                result_item.append('I')
            result_item = '`'.join(result_item)
            metareslt['result_item'] = result_item
            yield metareslt
        	
	
	judge_url = self.judge_url_duplicate(keyword,current_crawler_url)
	#print 'judge parse: ',judge_url
        if items and whether_get_next_page>=5 and int(cur_page)<=self.Max_Page and judge_url:
	    #print 'next...'
	    #print 'last_artilce_time: ',last_artilce_time
            if last_artilce_time==0 and not last_artilce_time:
                cur_timestamp = time.time()
            else:
		try:
                    cur_timestamp = self.datetime_to_timestamp(last_artilce_time)
		except:
		    cur_timestamp = time.time()
    #         print 'cur_timestamp: ',cur_timestamp
            today_timestamp,yesterday_timestamp,twodaysago_timestamp = self.get_timestamp()
            cur_hour = datetime.datetime.now().hour
            if self.Next_Page_Xpath:
                next_page_href = sel.xpath(self.Next_Page_Xpath).extract()
                flag = False
                try:
                    next_page_href = next_page_href[int(self.Next_Page_Xpath_Num)]
                    if not next_page_href.startswith('#'):
                        flag = True
                except:
                    flag = False
            else:
                flag = True
    #         print 'cur_hour: ',cur_hour
    #         print 'flag: ',flag
            if self.Check_Article_Time.lower()=='false':
                if flag:
                    reqs = self.make_next_request(keyword, cur_page,searchtime)
                    for req in reqs:
                        yield req
                else:
                    #抓取下一个关键词
                    reqs = self.make_reqs_by_keyword(1)
                    for req in reqs:
                        yield req
            elif self.Crawle_Total_Pages:
                reqs = self.make_next_request(keyword, cur_page,searchtime)
                #if int(cur_page)==1:
                #    print reqs
                for req in reqs:
                    yield req
                if self.Start_Page:
                    if self.Start_Page==0:
                        cur_page = int(cur_page)+1
                else:
                    if self.OStart_Page==0:
                        cur_page = int(cur_page)+1
                if int(cur_page)==int(self.Crawle_Total_Pages):
                    #抓取下一个关键词
                    log.msg('catch next keyword   cur_page: %s  Crawle_Total_Pages:%s'%(str(cur_page),str(self.Crawle_Total_Pages)),log.INFO)
                    reqs = self.make_reqs_by_keyword(1)
                    for req in reqs:
                        yield req
            else:
                if cur_hour<18 and cur_hour>8:
                    min_time = yesterday_timestamp-1
                else:
                    min_time = twodaysago_timestamp-1

                    
                if cur_timestamp>min_time and flag:
                    reqs = self.make_next_request(keyword, cur_page,searchtime)
                    for req in reqs:
                        yield req
                else:
                    #抓取下一个关键词
                    reqs = self.make_reqs_by_keyword(1)
                    for req in reqs:
                        yield req

        else:
            self.log_writer.write('%s\tcan`t get items:\t%s\n'%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),response.url))



