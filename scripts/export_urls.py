#!/bin/python
import MySQLdb
import datetime
import os

def connect(dbname,host='192.168.241.32'):
    conn = MySQLdb.connect(user='oopin',passwd='OOpin2007Group',db=dbname,host=host);
    return conn

def close(conn):
    conn.cursor().close()
    conn.close()

def get_his_day(days):
    now = datetime.datetime.now()
    diff = datetime.timedelta(days=days)
    his_day = (now-diff).strftime('%Y-%m-%d')
    return his_day

def export_urls():
    his_day = get_his_day(3)
    conn = connect('meta',host='localhost')
    cursor = conn.cursor()
    sql = 'select url from meta_result where metatime>="%s";'%(his_day)
    cursor.execute(sql)
    datas = cursor.fetchall()
    urls = set()
    for data in datas:
        url = data[0]
	urls.add(url)
    filename = '/tmp/URL_exported_%s.dat'%(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
    f = open(filename,'w')
    f.write('\n'.join(urls))
    close(conn)
    f.close()
    cmd = 'mv %s /disk2/crawler/'%(filename)
    os.system(cmd)

if __name__ == '__main__':
    export_urls()
