#encoding:utf-8
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
import meta.mysql_api as mysql
reload(sys)
sys.setdefaultencoding('utf-8')

REDIS_KEYWORD = 'REDISKEYWORD'
def get_redis_key():
    time_flag = datetime.datetime.now().strftime('%m%d%H')
    return REDIS_KEYWORD+time_flag

class MetaSpider(Spider):
    
    name = 'cluster_meta'
    total = 0
    def __init__(self,**kwargs):
        
        if not 'config' in kwargs:
            err =  'failed to find seed file (config=*.conf)'
            print err
        if 'startdate' in kwargs:
            self.startdate = kwargs['startdate']
        else:
            self.startdate = (datetime.datetime.now()-datetime.timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        if 'enddate' in kwargs:
            self.enddate = kwargs['enddate']
        else:
            self.enddate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         if not 'keywords' in kwargs:
#             err =  'failed to find seed file (keywords=*.dat)'
#             print err
        config = kwargs['config']
        self.load_conf(config)
        if self.Sleep_Flag=='SEARCH_ENGINE_SLEEP' or self.Sleep_Flag=='true' or not self.Sleep_Flag:
            settings.set('RANDOMIZE_DOWNLOAD_DELAY', True, priority='cmdline')
            settings.set('DOWNLOAD_DELAY', float(self.SE_Sleep_Base), priority='cmdline')
        else:
            settings.set('RANDOMIZE_DOWNLOAD_DELAY', False, priority='cmdline')
        
        log_filename = self.conf_name.replace('.conf','')+'.log'
        settings.set('LOG_FILE', log_filename, priority='cmdline')
        #初始化redis
        self.init_redis()
        self.redis_keyword = get_redis_key()
        #注册signal
        sig = SignalManager(dispatcher.Any)
        sig.connect(self.idle,signal=signals.spider_idle)
        sig.connect(self.close,signal=signals.spider_closed)
        self.metatime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.conn_local = mysql.connect('meta',host='localhost')
        self.conn_local_cursor = self.conn_local.cursor()
#        self.conn_local_cursor.execute('set global autocommit=1')
	try:
            self.meta_ip = get_meta_ip(network_card='enp7s0')
	except:
	    self.meta_ip = get_meta_ip(network_card='eth0')
        #初始化meta库的state
        self.init_state()
        
    def init_state(self):
        sql = "update meta_result set state=0 where template_name='%s' and state=1 and meta_ip='%s';"%(self.conf_source_name,self.meta_ip)
        #print 'init_state sql: ',sql
        self.conn_local_cursor.execute(sql)
        self.conn_local.commit()

    def get_cluster_urls(self,num):
        try:
            sql = "update meta_result set state=1 where state=0 and template_name='%s' and cluster_url<>'' and meta_ip='%s' and posttime>='%s' and posttime<'%s' order by posttime desc limit %d;"
            sql = sql%(self.conf_source_name,self.meta_ip,self.startdate,self.enddate,num)
            #print 'get_cluster_urls sql1: ',sql
            self.conn_local_cursor.execute(sql)
            self.conn_local.commit()
            sql = "select url,keyword,cluster_url from meta_result where state=1 and template_name='%s' and meta_ip='%s';"%(self.conf_source_name,self.meta_ip)
            #print 'get_cluster_urls sql2: ',sql
            self.conn_local_cursor.execute(sql)
            results = self.conn_local_cursor.fetchall()
            return results
        except Exception,e:
            #self.conn_local.rollback()
            print e
            return []
    
    def update_meta_state(self,url):
        try:
            sql = "update meta_result set state=2 where state=1 and template_name='%s' and meta_ip='%s' and url='%s';"%(self.conf_source_name,self.meta_ip,url)
            #print "update_meta_state sql: ",sql
            self.conn_local_cursor.execute(sql)
            self.conn_local.commit()
        except Exception,e:
            print e
        
    def start_requests(self):
        reqs = self.make_cluster_reqs(200)
        return reqs
    
    def make_cluster_reqs(self,num):
        results = self.get_cluster_urls(num)
	while self.total==0 and not results:
	    print 'wait cluster url...'
            time.sleep(60)
            results = self.get_cluster_urls(num)
        reqs = []
        cookie = self.load_cookie()
        searchtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for result in results:
            url = result[0]
            keyword = result[1]
            cluster_url = result[2]
            if cookie:
                req = Request(cluster_url,cookies=cookie,meta={'keyword':keyword.decode('utf-8'),'parent_url':url,'searchtime':searchtime,'cur_page':0})
            else:
                req = Request(cluster_url,meta={'keyword':keyword.decode('utf-8'),'parent_url':url,'searchtime':searchtime,'cur_page':0})
            reqs.append(req)
            self.total += 1
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
        reqs = self.make_cluster_reqs(1)
        if reqs:
            return reqs[0]
    
    def close(self,spider):
        mysql.close(self.conn_local)
    
    def init_redis(self):
        self.redis_conn = redis.redis_connect()
        redis.set_expire_time(self.redis_conn, META_NEXT_URL, EFFECTIVE_TIME)
        
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
    
    def load_conf(self,filename):
        self.conf = receive_conf(filename)
        self.conf_name = self.conf[0]
        self.conf_source_name = self.conf_name.replace('copy','time')
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
        url_tmp = url_tmp.replace(u'&amp;','&')
        url_tmp = url_tmp.replace(u'&quot;','"')
        url_tmp = url_tmp.replace(u'&lt;','<')
        url_tmp = url_tmp.replace(u'&gt;','>')
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
    
    def get_cluster_next_page(self,url,sel):
        domain,_ = get_domain(url)
        if domain=='baidu':
            #page = sel.xpath('//a[@class="n"]').extract()[0]
            page_sel = sel.xpath('//a[@class="n"]').extract()
            page = ''.join(page_sel)
            if page.find(u'\u4e0b\u4e00\u9875')!=-1 or page.find('下一页')!=-1:
                cluster_next_url = sel.xpath('//a[@class="n"]/@href').extract()[len(page_sel)-1]
                #print 'cluster_next_url: ',cluster_next_url
                return cluster_next_url
            else:
                #print 'cluster_next_url is null'
                return ''
        elif domain=='haosou':
            page = sel.xpath('//div[@id="page"]').extract()
            if page:
                page = page[0]
                if page.find(u'\u4e0b\u4e00\u9875')!=-1:
                    cluster_next_url_tmp = sel.xpath('//div[@id="page"]/a/@href').extract()
                    cluster_next_url = cluster_next_url_tmp[len(cluster_next_url_tmp)-1]
                    return cluster_next_url
            else:
                return ''
        next_page_href = sel.xpath(self.Next_Page_Xpath).extract()
        if next_page_href:
            next_page_href = next_page_href[int(self.Next_Page_Xpath_Num)]
        else:
            next_page_href = ''
        return next_page_href
    
    def get_next_page(self,keyword,cur_page):
        cur = (int(cur_page)+1)*int(self.Query_Skip_Items)
        url = self.Url_Front_Part + keyword.encode(self.Query_Encoding) + self.Url_Rear_Part + self.Url_Change_page + str(cur) 
        return url
    
    def next_urls(self,keyword,cur_page):
        url_maps = {}
        if self.Crawle_Total_Pages:
            curpage = 2
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
        url_maps = sorted(url_maps.iteritems(), reverse=False)
        return url_maps
    
    def make_next_request(self,keyword,cur_page):
        next_urls = self.next_urls(keyword, cur_page)
#         print "next_urls: ",next_urls
        cookie = self.load_cookie()
        reqs = []
        for cur_page,next_url in next_urls:
#             print next_url
            if redis.check_set_value(self.redis_conn, META_NEXT_URL, next_url):
                continue
            if cookie:
                req = Request(next_url,cookies=cookie,meta={'keyword':keyword,'cur_page':cur_page})
                redis.add_set_value(self.redis_conn, META_NEXT_URL, next_url)
                reqs.append(req)
            else:
                req =  Request(next_url,meta={'keyword':keyword,'cur_page':cur_page})
                redis.add_set_value(self.redis_conn, META_NEXT_URL, next_url)
                reqs.append(req)
        return reqs
                
    def parse(self,response):
        self.total -= 1
        keyword = response.request.meta.get('keyword')
        cur_page = response.request.meta.get('cur_page')
        searchtime = response.request.meta.get('searchtime')
        parent_url = response.request.meta.get('parent_url')
        url = response.url
        log.msg('response url: %s'%(response.url),log.INFO)
#         print 'cur_page: ',cur_page
#         print url
        try:
            content = response.body_as_unicode()
        except:
            content = response.body
        content = clear_html_comment(content)
        sel = Selector(text=content)
        order_result = self.Result_Order.upper()
#         print 'order_result: ',order_result
        items = sel.xpath(self.Item_Xpath).extract()
	#print 'items: ',items
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
            if order_result.find('U')!=-1:
                url = self.selector(item_sel, item, 'U')
                if not url or url.startswith('#'):
                    continue
                url = self.calculate_url(response.url, url)
                domain = urlparse.urlparse(url).hostname
                metareslt['domain'] = domain
                metareslt['url'] = url
                result_item.append('U')
            if  order_result.find('T')!=-1:
                title = self.selector(item_sel, item, 'T')
                metareslt['title'] = title
                result_item.append('T')
            if  order_result.find('D')!=-1:
                posttime = self.selector(item_sel, item, 'D')
#                 print 'posttime1: ',posttime
                posttime = format_time(posttime, time.time())
#                 print 'posttime2: ',posttime
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
                id = self.selector(item_sel, item, 'S')
                metareslt['id'] = id
                result_item.append('I')
            result_item = '`'.join(result_item)
            metareslt['result_item'] = result_item
            yield metareslt
            
        try:
            next_page_href = self.get_cluster_next_page(response.url,sel)
            if next_page_href:
                next_page_href = self.calculate_url(response.url, next_page_href)
                cookie = self.load_cookie()
                if cookie:
                    yield Request(next_page_href,cookies=cookie,meta={'keyword':keyword,'parent_url':parent_url,'searchtime':searchtime,'cur_page':cur_page+1})
                else:
                    yield Request(next_page_href,meta={'keyword':keyword,'parent_url':parent_url,'searchtime':searchtime,'cur_page':cur_page+1})
            else:
                raise Exception('This cluster url is end...')
        except:
            #若该链接没有下一页，则说明该cluster链接已经抓取完毕
            #判断什么时候发起新的request
            self.total -= 1
            self.update_meta_state(parent_url)
            if self.total<=100:
                reqs = self.make_cluster_reqs(100)
                for req in reqs:
                    yield req
                 
