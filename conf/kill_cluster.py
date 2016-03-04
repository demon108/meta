#!/bin/python
import os
import datetime
# cd /home/dingyong/meta/conf/
# /bin/python stop_crawler.py baidu_news_copy.conf
# date=`date +%F`
# mv baidu_news_copy.log "baidu_news_copy.log.$date"


PROJECT_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
conf_path = os.path.join(PROJECT_PATH,'pattern')
conf_files = os.listdir(conf_path)
work = '/home/dingyong/meta/conf/'
os.chdir(work) 
for cfile in conf_files:
    if not cfile.endswith('copy.conf'):
        continue
    stop_crawler = '''ps -efw |grep scrapy |grep dingyong|grep %s|awk '{print "kill "$2}' |bash'''%(cfile)
    os.system(stop_crawler)
    logfile = cfile.replace('.conf','.log')
    cmd = 'mv %s %s.%s'%(logfile,logfile,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    os.system(cmd)
