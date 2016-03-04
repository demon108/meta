#!/usr/bin/python
import commands
import os
import time

def get_cluster_status(template):
    process = commands.getoutput('ps aux|grep scrapy|grep cluster_meta|grep %s|grep -v "grep"|wc -l'%(template))
    if int(process)==0:
        return False
    return True

def process(template):
    path = '/home/dingyong/meta/conf/'
    os.chdir(path)
    if not get_cluster_status(template):
	cmd = '/bin/python start_crawler.py mode=cluster config=../pattern/%s'%(template)
	os.system(cmd)
    else:
	open('check_cluster.tmp','w').write('The deamon is runing...')

#process('baidu_news_copy.conf')
if __name__ == '__main__':
    #process('baidu_news_copy.conf')
    PROJECT_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    conf_path = os.path.join(PROJECT_PATH,'pattern')
    conf_files = os.listdir(conf_path) 
    for cfile in conf_files:
        if not cfile.endswith('copy.conf'):
            continue
	print cfile
        process(cfile)
	time.sleep(10)

