#!/usr/bin/python
# -*- coding: utf-8 -*---

import sys
import os
import time
import codecs
import string
import random
import MySQLdb
from collections import Counter
from datetime import datetime

import redis_api as redis


# META_PATH="/home/zzg/coopinion/opin_monitor/"
# META_PATH="/home/guanglei/meta_tools/"
META_PATH="/home/dingyong/meta"

today = datetime.now().date()

def get_redis_key(template_name):
    template_name = os.path.basename(template_name)
    redis_keyword = template_name.split('.')[0]
    time_flag = datetime.now().strftime('%m%d%H')
    return redis_keyword+time_flag

def check_meta_expire(conn,userid):
    sql = "select end_date,state from pm.project where bsppr_id = %d"%(userid)
    cursor=conn.cursor()
    cursor.execute(sql)
    flag = False
    for row in cursor.fetchall():
        state = row[1]
        if state == 0 or state == 1:
            if row[0] >= today:
                flag = True

    if flag == False:
        sql = "update meta_list set state = 0 where userid = %d"%(userid)
        cursor.execute(sql)
    cursor.close()
    return flag

def get_datas(host='192.168.241.32'):
    tasks = dict()
    tasks_H = dict()
    tasks_L = dict()
    try:
        conn=MySQLdb.connect(host=host,user='oopin',passwd='OOpin2007Group',db='bsppr')
        cursor=conn.cursor()
        cursor.execute("set names utf8")
        sql = "select ip_count from meta_ip_list where ip='%s'"%(ip)
        rst = cursor.execute(sql)
        ip_count = -1
        for row in cursor.fetchall():
            ip_count = row[0]

        if ip_count == -1:
            raise
        sql = "select time,freq,word_list,word_list_H,word_list_L,detail_ip,userid from meta_list where meta_ip='%s' and state=1"%(ip)
        rst = cursor.execute(sql)
        for row in cursor.fetchall():
            userid = row[6]
            if not check_meta_expire(conn,userid):
                continue
            try:
                tm = row[0].split(",");
                #print tm
                #tm = ['09','10','13','15','16','17','18']
                detail_ip = row[5]
                if hour in tm:
                    #freq = row[1]
                    if row[2]:
                        words = row[2].split("#$!#")
                        for word in words:
                            if word in tasks:
                                if tasks[word] != -1:
                                    tasks[word] = detail_ip
                            else:
                                tasks[word] = detail_ip

                    if row[3]:
                        words = row[3].split("#$!#")
                        for word in words:
                            if word in tasks_H:
                                if tasks_H[word] != -1:
                                    tasks_H[word] = detail_ip
                            else:
                                tasks_H[word] = detail_ip
                    if row[4]:
                        words = row[4].split("#$!#")
                        for word in words:
                            if word in tasks_L:
                                if tasks_L[word] != -1:
                                    tasks_L[word] = detail_ip
                            else:
                                tasks_L[word] = detail_ip
            except Exception:
                continue
        cursor.close()
        conn.commit()
        conn.close()
    except:
        pass
    return tasks_H,tasks,tasks_L

if __name__ == "__main__":
    if len(sys.argv)!=2:
        raise Exception('Need the template_name!!!')
    template_name = sys.argv[1]
    import socket, fcntl, struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', 'enp8s0'))
    except:
        inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', 'eth1'))
    ip = socket.inet_ntoa(inet[20:24])
    #print ip
    hour = datetime.now().strftime("%H")
    day = string.atoi(datetime.now().strftime("%d"))

    if hour < '10':
        days = 1
    else:
        days = 0

    tasks_H,tasks,tasks_L = get_datas(host='192.168.241.32')
    tasks_H_b7,tasks_b7,tasks_L_b7 = get_datas(host='192.168.241.7')
    tasks_H.update(tasks_H_b7)
    tasks.update(tasks_b7)
    tasks_L.update(tasks_L_b7)
    #print 'tasks_H: ',tasks_H
    #print 'tasks: ',tasks
    #print 'tasks_L: ',tasks_L
    
    os.chdir(META_PATH)
    score = 1000
    redis_key = get_redis_key(template_name)
    redis_conn = redis.connect()
    redis.delete_keys(redis_conn, redis_key)
    words = Counter()
    for word,_ in tasks_H.iteritems():
        redis.add_zset(redis_conn,redis_key, score, word)
        score -= 0.1
        words.update({word:4})
    for word,_ in tasks.items():
        redis.add_zset(redis_conn,redis_key, score, word)
        score -= 0.1
        words.update({word:2})
        
    _hour = string.atoi(hour)
    if _hour < 6 or _hour > 18:
        for word,_ in tasks_L.iteritems():
            redis.add_zset(redis_conn,redis_key, score, word)
            score -= 0.1
            words.update({word:1})
            
    word_collections = []
    for word in words.most_common():
        word_collections.append(word[0])
    
    fp = open('keywords.%s.dat'%(hour),'w')
    fp.write('\n'.join(word_collections))
    fp.close()
        

#         sql = "select * from meta_back_list where meta_ip='%s' and state=0"%(ip)
#         rst = cursor.execute(sql)
#         update_task = list()
#         for row in cursor.fetchall():
#             _id = row[0]
#             _ip = row[3]
#             if _ip == -1:
#                 _ip = random.randint(0,ip_count-1)
#             days = row[4]
#             #fn = "./query.auto_meta.%s.%d"%(hour,_ip)
#             fn = "./query.auto_meta.u%s.%d"%(_id,_ip)
#             fp = codecs.open(fn,'w','gbk')
#             for word in row[7].split("#$!#"):
#                 try:
#                     fp.write(word.decode('utf-8'))
#                     fp.write("\n".decode("utf-8"))
#                 except Exception:
#                     print word 
#                     pass
#             fp.close()
#             update_task.append(_id)
# 
#     
#         _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         
#         for _id in update_task:
#             sql = "update meta_back_list set state=1,meta_time='%s' where id = %d "%(_ts,_id)
#             cursor.execute(sql)

        #update table

#     except MySQLdb.Error,e:
#         print "Mysql Error :" ,e


