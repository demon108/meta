#!/usr/local/bin/python
# -*- coding: utf-8 -*---

import os
import time
import string
import MySQLdb
from datetime import datetime

if __name__ == "__main__":
    import socket, fcntl, struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', 'eth1'))
    ip = socket.inet_ntoa(inet[20:24])

    hour = datetime.now().strftime("%H")
    day = string.atoi(datetime.now().strftime("%d"))

    cmd = "ps -ef |grep conf |grep baidu_news |wc -l"
    baidu_count = string.atoi(os.popen(cmd).read())
    cmd = "ps -ef |grep conf |grep qihoo|wc -l"
    qihoo_count = string.atoi(os.popen(cmd).read())
    cmd = "ps -ef |grep conf |grep soso_news|wc -l"
    soso_count = string.atoi(os.popen(cmd).read())

    try:
        conn=MySQLdb.connect(host='192.168.241.7',user='oopin',passwd='OOpin2007Group',db='bsppr')
        cur=conn.cursor()

        sql = "update meta_load set baidu=%d,qihoo=%d,sousou=%d where ip='%s' and DR=%d and time = '%s'"%(baidu_count,qihoo_count,soso_count,ip,day%3,hour)
        cur.execute(sql)
        conn.commit()
        cur.close()
        conn.close()

    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])

