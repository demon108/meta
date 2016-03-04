#encoding:utf-8
import json
import sys
import datetime
reload(sys)
sys.setdefaultencoding('utf-8')

from item import *
import mysql_api as mysql
from meta_util import *

def get_domainID(handle,cursor,domain,source):
    sql = "select DomainID from domain where name='%s' and url='%s';"%(source,domain)
    cursor.execute(sql)
    domainID = cursor.fetchone()
    if not domainID:
        sql = "insert into domain(name,url) values('%s','%s');"%(source,domain)
        cursor.execute(sql)
        mysql.commit(handle)
        sql = "select DomainID from domain where name='%s' and url='%s';"%(source,domain)
        cursor.execute(sql)
        domainID = cursor.fetchone()
    return domainID[0]

def get_authorID(handle,cursor,domainID,author):
    sql = "select AuthorID from author where nickname='%s' and domain='%s';"%(author,domainID)
#    print sql
    cursor.execute(sql)
    authorID = cursor.fetchone()
    if not authorID:
        sql = "insert into author(nickname,domain) values('%s','%s');"%(author,domainID)
        cursor.execute(sql)
        mysql.commit(handle)
        sql = "select AuthorID from author where nickname='%s' and domain='%s';"%(author,domainID)
        cursor.execute(sql)
        authorID = cursor.fetchone()
    return authorID[0]

def process_openid(openid):
    #/gzh?openid=oIWsFt46Rpc5V5xvKBQZkavBWq-4
    return openid.split('?')[1][7:]
    

class MetaPipeline(object):
    def __init__(self):
        self.conn = mysql.connect('coopinion',host='192.168.241.31')
        self.cursor = self.conn.cursor()
        self.conn.set_character_set('utf8')
        self.cursor.execute('set names utf8mb4')
        self.cursor.execute('SET CHARACTER SET utf8;')
        self.cursor.execute('SET character_set_connection=utf8;')
        self.cursor.execute('set interactive_timeout=24*3600;')
	self.cursor.execute('set wait_timeout=24*3600;')
        self.conn_weixin = ''
        self.conn_local = mysql.connect('meta',host='localhost')
        self.conn_local_cursor = self.conn_local.cursor()
        self.conn_local.set_character_set('utf8')
        self.conn_local_cursor.execute('set names utf8mb4')
        self.conn_local_cursor.execute('SET CHARACTER SET utf8;')
        self.conn_local_cursor.execute('SET character_set_connection=utf8;')
        self.conn_local_cursor.execute('set interactive_timeout=24*3600;')
        self.conn_local_cursor.execute('set wait_timeout=24*3600;')
        self.conn_local_cursor.execute('set innodb_lock_wait_timeout=1000;')
#        self.conn_local_cursor.execute('set global autocommit=1')
	try:
            self.meta_ip = get_meta_ip(network_card='enp7s0')
	except:
	    self.meta_ip = get_meta_ip(network_card='eth0')
        
    def coopinion(self,url,source,domain,author,site_type,title,comment_count,click_count,posttime):
        domainID = get_domainID(self.conn,self.cursor,domain,source)
        if site_type!='news':
            authorID = get_authorID(self.conn,self.cursor,domainID,author)
        if site_type=='forum':
            sql = "insert into post(authorID,domain,title,replies,clicks,posttime,url) values('%s','%s','%s',%d,%d,'%s','%s');"
            sql = sql%(authorID,domainID,title,comment_count,click_count,posttime,url)
            self.cursor.execute(sql)
        elif site_type=='blog':
            sql = "insert into blogpost(authorID,domainID,blogname,replies,clicks,posttime,url) values('%s','%s','%s',%d,%d,'%s','%s');"
            sql = sql%(authorID,domainID,title,comment_count,click_count,posttime,url)
            self.cursor.execute(sql)
        elif site_type=='news':
            sql = "insert into news(DomainID,title,replies,clicks,posttime,url) values('%s','%s',%d,%d,'%s','%s');"
            sql = sql%(domainID,title,comment_count,click_count,posttime,url)
	    #print sql
            self.cursor.execute(sql)
        elif site_type=='weixin':
            sql = "insert into weixin_post(authorID,domain,title,replies,clicks,posttime,url) values('%s','%s','%s',%d,%d,'%s','%s');"
            sql = sql%(authorID,domainID,title,comment_count,click_count,posttime,url)
            self.cursor.execute(sql)
        self.conn.commit()
        
    def mx_kol(self,result):
        if not self.conn_weixin:
            self.conn_weixin = mysql.connect('mx_kol', host='192.168.241.29')
            self.weixin_cousor = self.conn_weixin.cursor()
            self.conn_weixin.set_character_set('utf8')
            self.weixin_cousor.execute('set names utf8mb4')
            self.weixin_cousor.execute('SET CHARACTER SET utf8;')
            self.weixin_cousor.execute('SET character_set_connection=utf8;')
        openid = process_openid(result['id'])
        url = result['url']
        author = result.get('author','')
        tencent_id = get_tencent_id(url)
        is_v = 0
        sql = "insert into weixin_user_info(userid,openid,tencent_id,screen_name,is_v) values('%s','%s','%s','%s',%d) on duplicate key update screen_name='%s';"
        sql = sql%(openid,openid,tencent_id,author,is_v,author)
        self.weixin_cousor.execute(sql)
        self.conn_weixin.commit()
        
    def meta(self,title,comment_count,click_count,domain,author,item):
	#print 'comment_count: ',comment_count
	#print type(comment_count)
	#print 'click_count: ',click_count
	#print type(click_count)
        template_name = item['template_name'] 
        template_type = item['template_type']
        keyword = item['keyword']
        keyword = self.conn_local.escape_string(keyword.encode('utf-8','ignore'))
        meta_pages = item['meta_pages']
	#print 'meta_pages: ',meta_pages
        metatime = item['metatime']
        searchtime = item['searchtime']
        
        abstract = item.get('abstract','')
        abstract = self.conn_local.escape_string(abstract.encode('utf-8','ignore'))
        posttime = item.get('posttime','')
        url = item['url']
        cluster_url = item.get('copy_url','')
        like_count = 0
        state = 0
        meta_ip = self.meta_ip
        sql = "insert ignore into meta_result(template_name,template_type,keyword,meta_pages,title,abstract,posttime,url,cluster_url,author,repost_count,comment_count,click_count,like_count,read_count,domain,metatime,searchtime,state,meta_ip) values('%s','%s','%s',%d,'%s','%s','%s','%s','%s','%s',%d,%d,%d,%d,%d,'%s','%s','%s','%s','%s');"
        sql = sql%(template_name,template_type,keyword,int(meta_pages),title,abstract,posttime,url,cluster_url,author,comment_count,comment_count,click_count,like_count,click_count,domain,metatime,searchtime,state,meta_ip)
	#print sql
        self.conn_local_cursor.execute(sql)
        self.conn_local.commit()
	#f2 = open(template_name.replace('.conf','.meta'),'a+')
	#timestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	#f2.write('%s\t%s\n'%(timestr,url))
	#f2.flush()
    
    def process_item(self, item, spider):
	#print '....pipline...'
	#print 'item: ',item
        url = item['url']
        template_name = item['template_name']
        f = open(template_name.replace('.conf','.urls'),'a+')
        timestr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write('%s\t%s\n'%(timestr,url))
        f.flush()
        domain,tmp_source = get_domain(url)
        source = tmp_source
        if 'source' in item:
            source = item['source']
        source = self.conn_local.escape_string(source.encode('utf-8','ignore'))
        author = item.get('author','')
        author = self.conn_local.escape_string(author.encode('utf-8','ignore'))
        site_type = item['template_type']
        title = self.conn_local.escape_string(item.get('title',''))
        comment_count = 0
        if 'comment_count' in item:
            try:
                comment_count = int(item['comment_count'].strip())
            except:
                comment_count = 0
        click_count = 0
        if 'click_count' in item:
            try:
                click_count = int(item['click_count'].strip())
            except:
                click_count = 0
        posttime = item.get('posttime')
        #存入本地meta库
        self.meta(title,comment_count,click_count,tmp_source,author,item)
        #存入cyberin后台数据库
        #self.coopinion(url,source,domain,author,site_type,title,comment_count,click_count,posttime) 
        #存入mx_kol库的微信user表
        if site_type=='weixin':
            self.mx_kol(item)
        
    def close_spider(self,spider):
#        mysql.close(self.conn)
        mysql.close(self.conn_local)
        if self.conn_weixin:
            mysql.close(self.conn_weixin)
        
        
       


