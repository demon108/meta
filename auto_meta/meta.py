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

META_PATH="/home/zzg/coopinion/opin_monitor/"
#META_PATH="/home/guanglei/meta_tools/"
WORDS_PER_FILE=20

conn = False

today = datetime.now().date()

def check_meta_expire(userid):
    global conn
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

if __name__ == "__main__":
    import socket, fcntl, struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', 'enp8s0'))
    ip = socket.inet_ntoa(inet[20:24])

    hour = datetime.now().strftime("%H")
    day = string.atoi(datetime.now().strftime("%d"))

    if hour < '10':
        days = 1
    else:
        days = 0

    try:
        conn=MySQLdb.connect(host='192.168.241.32',user='oopin',passwd='OOpin2007Group',db='bsppr')
        cursor=conn.cursor()
        cursor.execute("set names utf8")

        sql = "select ip_count from meta_ip_list where ip='%s'"%(ip)
        rst = cursor.execute(sql)
        ip_count = -1
        for row in cursor.fetchall():
            ip_count = row[0]

        if ip_count == -1:
            sys.exit(0)

        sql = "select time,freq,word_list,word_list_H,word_list_L,detail_ip,userid from meta_list where meta_ip='%s' and state=1"%(ip)
        rst = cursor.execute(sql)

        tasks = dict()
        tasks_H = dict()
        tasks_L = dict()
        for row in cursor.fetchall():
            userid = row[6]
            if not check_meta_expire(userid):
                continue
            try:
                tm = row[0].split(",");
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


        #generate the meta_file
        os.chdir(META_PATH)

        word_list = dict()
        word_count = Counter()
        for i in range(ip_count):
            word_list[i] = list()
            word_count.update({"%d"%(i):0})

        keys = dict() #for duplicate keys
        for word,v in tasks_H.items():
            if word in keys:
                continue
            else:
                keys[word] = 1

            if v != -1:
                word_list[v].append(word)
                word_count.update({'%s'%(v):1})
            else:
                t = word_count.most_common()[:-2:-1]
                _ip = string.atoi(t[0][0])
                word_list[_ip].append(word)
                word_count.update({'%s'%(_ip):1})

        for word,v in tasks.items():
            if word in keys:
                continue
            else:
                keys[word] = 1

            if v != -1:
                word_list[v].append(word)
                word_count.update({'%s'%(v):1})
            else:
                t = word_count.most_common()[:-2:-1]
                _ip = string.atoi(t[0][0])
                word_list[_ip].append(word)
                word_count.update({'%s'%(_ip):1})

        _hour = string.atoi(hour)
        if _hour < 6 or _hour > 18:
            for word,v in tasks_L.items():
                if word in keys:
                    continue
                else:
                    keys[word] = 1

                if v != -1:
                    word_list[v].append(word)
                    word_count.update({'%s'%(v):1})
                else:
                    t = word_count.most_common()[:-2:-1]
                    _ip = string.atoi(t[0][0])
                    word_list[_ip].append(word)
                    word_count.update({'%s'%(_ip):1})

        command_list = list()
        for _ip,w_list in word_list.items():
            fn = "./query.auto_meta.%s.%d"%(hour,_ip)
            fp = codecs.open(fn,'w','gbk')
            for word in w_list:
                fp.write(word.decode("utf-8"))
                fp.write("\n".decode("utf-8"))
            fp.close()
            command_list.append("./simu_meta.script auto_meta.%s.%d %d %s"%(hour,_ip,days,_ip))

        sql = "select * from meta_back_list where meta_ip='%s' and state=0"%(ip)
        rst = cursor.execute(sql)
        update_task = list()
        for row in cursor.fetchall():
            _id = row[0]
            _ip = row[3]
            if _ip == -1:
                _ip = random.randint(0,ip_count-1)
            days = row[4]
            #fn = "./query.auto_meta.%s.%d"%(hour,_ip)
            fn = "./query.auto_meta.u%s.%d"%(_id,_ip)
            fp = codecs.open(fn,'w','gbk')
            for word in row[7].split("#$!#"):
                try:
                    fp.write(word.decode('utf-8'))
                    fp.write("\n".decode("utf-8"))
                except Exception:
                    print word 
                    pass
            fp.close()
            update_task.append(_id)
            command_list.append("./simu_meta.script auto_meta.u%s.%d %d %s"%(_id,_ip,days,_ip))

    
        _ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for _id in update_task:
            sql = "update meta_back_list set state=1,meta_time='%s' where id = %d "%(_ts,_id)
            cursor.execute(sql)

        #update table
        cursor.close()

        conn.commit()
        conn.close()

        for command in command_list:
            #print "invoke: ",command
            os.system(command)
            #os.system("sleep 5")

    except MySQLdb.Error,e:
        print "Mysql Error :" ,e

