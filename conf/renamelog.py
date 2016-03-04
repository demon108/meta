#!/bin/python
#encoding:utf-8
import os
import datetime
import re
import time
'''
更改日志文件名字
一周运行一次
'''

workspace = '/home/dingyong/meta/conf/'

def rename_log_weekly():
    os.chdir(workspace)
    files = os.listdir(workspace)
    datestr = datetime.datetime.now().strftime('%Y-%m-%d')
    for file in files:
        if not file.endswith('.log') and not file.endswith('.urls'):
            continue
        cmd = 'mv %s %s.%s'%(file,file,datestr)
        os.system(cmd)
        cmd = 'touch %s'%(file)
        os.system(cmd)

def rm_history_log():
    '''删除3个月前的日志'''
    os.chdir(workspace)
    history_log_re = re.compile('\d{4}-\d{2}-\d{2}$')
    files = os.listdir(workspace)
    now = time.time()
    for file in files:
        if not history_log_re.search(file):
            continue
        filetime = history_log_re.search(file).group()
        struct_time = time.strptime(filetime, "%Y-%m-%d")
        greentime = time.mktime(struct_time)
        difftime = now - greentime
        if difftime>91*3600:
            os.remove(file)
    
rm_history_log()
rename_log_weekly()
