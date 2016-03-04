#!/bin/python
#encoding:utf-8
import os
import time
import sys

'''
    README:
python start_crawler.py  #启动全部的非cluster  crawler

python start_crawler.py mode=cluster  #启动全部的cluster crawler

python start_crawler.py  config=../pattern/sogou_weixin_day.conf  启动单个非cluster crawler

python start_crawler.py mode=cluster config=../pattern/baidu_news_copy.conf  启动单个cluster crawler
'''


#work
work_path = r'/home/dingyong/meta/conf/'
auto_meta_path = r'/home/dingyong/meta/auto_meta/'

#test
#work_path = r'D:\workspace\meta\conf'
#auto_meta_path = r'D:\workspace\meta\auto_meta'

PROJECT_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
conf_path = os.path.join(PROJECT_PATH,'pattern')
def start_all_crawler():
    conf_files = os.listdir(conf_path)
    for conf_file in conf_files:
        if not conf_file.endswith('.conf') or conf_file.endswith('copy.conf'):
            continue
	print conf_file
        #初始化redis，讲meta关键词放入对应的redis库
        os.chdir(auto_meta_path)
        push_keyword_to_redis = '/bin/python meta_new.py %s'%(conf_file)
        print push_keyword_to_redis
        os.system(push_keyword_to_redis)
        #启动crawler
        os.chdir(work_path)
        configfile = os.path.join(conf_path,conf_file)
        start_crawler = '/usr/local/bin/scrapy crawl meta -a config=%s &'%(configfile)
        print start_crawler
        os.system(start_crawler)
        time.sleep(3)


def start_single_crawler(pattern_name):
    basename = os.path.basename(pattern_name)
    curpattern = os.path.join(conf_path,basename)
    #初始化redis，讲meta关键词放入对应的redis库
    os.chdir(auto_meta_path)
    push_keyword_to_redis = '/bin/python meta_new.py %s'%(basename)
    print push_keyword_to_redis
    os.system(push_keyword_to_redis)
    
    #启动crawler
    os.chdir(work_path)
    start_crawler = '/usr/local/bin/scrapy crawl meta -a config=%s &'%(curpattern)
    print start_crawler
    os.system(start_crawler)

def start_single_cluster_crawler(pattern_name):
    basename = os.path.basename(pattern_name)
    curpattern = os.path.join(conf_path,basename)
    
    #启动crawler
    os.chdir(work_path)
    start_crawler = '/usr/local/bin/scrapy crawl cluster_meta -a config=%s &'%(curpattern)
    print start_crawler
    os.system(start_crawler)

def start_all_cluster_crawler():
    conf_files = os.listdir(conf_path)
    for conf_file in conf_files:
        if not conf_file.endswith('copy.conf'):
            continue
	print conf_file
        #启动crawler
        os.chdir(work_path)
        configfile = os.path.join(conf_path,conf_file)
        start_crawler = '/usr/local/bin/scrapy crawl cluster_meta -a config=%s &'%(configfile)
        print start_crawler
        os.system(start_crawler)
        time.sleep(3)


def formart_params(params):
    #['pattern=a.conf', 'mode=b']
    params_dict = {}
    for parma in params:
        parma_spl = parma.split('=')
        params_dict.update({parma_spl[0]:parma_spl[1]})
    return params_dict
    
if __name__ == '__main__':
    if len(sys.argv)<2:
        config = 'all'
        mode = 'normal'
    elif len(sys.argv)>=2:
        params = formart_params(sys.argv[1:])
        config = params.get('config','all')
        mode = params.get('mode','normal')
    
    print 'mode: ',mode
    print 'config: ',config 
    if mode=='cluster':
        if config=='all':
            start_all_cluster_crawler()
        else:
            start_single_cluster_crawler(config)
    else:
        if config=='all':
            start_all_crawler()
        else:
            start_single_crawler(config)
        
    
    
    
    
    
    
    
    
    
