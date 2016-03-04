#!/bin/python
import sys
import os

def get_patterns():
    PROJECT_PATH = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
    work_path = '/home/dingyong/meta/conf/'
    os.chdir(work_path)
    conf_path = os.path.join(PROJECT_PATH,'pattern')
    conf_files = os.listdir(conf_path)
    patterns = []
    for conf_file in conf_files:
        if not conf_file.endswith('.conf'):
            continue
        patterns.append(conf_file)
    return patterns

if __name__ == '__main__':
    try:
        param1 = sys.argv[1]
        if param1=='all':
            patterns = get_patterns()
            for pattern in patterns:
                stop_crawler = '''ps -efw |grep scrapy |grep dingyong|grep %s|awk '{print "kill -9 "$2}' |bash'''%(pattern)
                os.system(stop_crawler)
        else:
            for pattern in sys.argv[1:]:
                stop_crawler = '''ps -efw |grep scrapy |grep dingyong|grep %s|awk '{print "kill -9 "$2}' |bash'''%(pattern)
		print stop_crawler
                os.system(stop_crawler)  
    except:
        raise 'Need One Param At Last!!!'


#ps -efw |grep scrapy |grep dingyong|grep $1|awk '{print "kill -9 "$2}' |bash
