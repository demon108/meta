#!/bin/python
#encoding:utf-8
import commands
import time
import os

def get_pids():
    processes = commands.getoutput('ps x|grep scrapy|grep meta|grep -v "grep"')
    if processes:
        processes = processes.split('\n')    
    pids = []
    for process in processes:
        pids.append(process.strip().split(' ')[0])
    return pids

month_map = {'Jan':'01','Feb':'02','Mar':'03','Apr':'04','May':'05','Jun':'06',\
             'Jul':'07','Aug':'08','Sep':'09','Oct':'10','Nov':'11','Dec':'12'}

def get_starttime_by_pid(pids=[]):
    now = time.time()
    for pid in pids:
        status = commands.getoutput('ps -eo pid,lstart|grep %s'%(pid)).split('\n')[0].strip()
        tmps = status.split(' ')
	lentmps = len(tmps)
        year = tmps[lentmps-1]
        month = month_map[tmps[2]]
        day = tmps[lentmps-3]
        detail_time = tmps[lentmps-2]
        
        process_time = year+'-'+month+'-'+day+' '+detail_time
        t = time.strptime(process_time, "%Y-%m-%d %H:%M:%S")
        greenwichtime = time.mktime(t)
        difftime = now - greenwichtime
        #print difftime
        if difftime>3600*24*2:
	    print pid
            os.system('kill -9 %s'%(pid))
        
get_starttime_by_pid(pids=get_pids())
        
    
