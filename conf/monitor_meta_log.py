#!/bin/python
#encoding:utf-8
import os
import datetime
import re
import smtplib
from email.mime.text import MIMEText
from email.header import Header
'''
检查日志文件
'''

workspace = '/home/dingyong/meta/conf/'

def send_mail(subject,content):
    sender = 'dingyong881205@126.com'
    receiver = ['yong.ding@maixunbytes.com']
    smtpserver = 'smtp.126.com'
    username = 'dingyong881205@126.com'
    password = 'yong881205'
#    msg = MIMEText(content,'text','utf-8')#中文需参数‘utf-8’，单字节字符不需要
    msg = MIMEText(content,_charset='utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender
    msg['To'] = ';'.join(receiver)
    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    smtp.sendmail(sender, receiver, msg.as_string())

def get_ip(network_card='enp8s0'):
    import socket, fcntl, struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', network_card))
    ip = socket.inet_ntoa(inet[20:24])
    return ip

def checklog():
    os.chdir(workspace)
    files = os.listdir(workspace)
    diff = datetime.timedelta(hours=1)
    datestr = (datetime.datetime.now()-diff).strftime('%Y-%m-%d %H')
    crawler_pattern = re.compile('Crawled \d+ pages \(at (?P<pagenum>\d+) pages/min\), scraped \d+ items \(at (?P<itemnum>\d+) items/min\)')
    ip = get_ip()
    for file in files:
	if file.startswith('babytree_') or file.startswith('mama_') or file.startswith('gmw_') or file.startswith('youdao_'):
	    continue
        if not file.endswith('.log'):
            continue
        #收集0 pages/min
        _pages0 = 0
        #收集非0 pages/min
        _pages1 = 0
        #收集0 items/min
        _items0 = 0
        #收集非0 items/min
        _items1 = 0
        #收集出错量
        errors = 0
        f = open(file,'r')
        while True:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            if line.find('[scrapy] INFO:')!=-1:
                continue
            if line.find(datestr)==-1:
                continue
            if line.find('ERROR: Error processing')!=-1:
                errors += 1
                continue
            _crawler = crawler_pattern.search(line)
            if _crawler:
                result = _crawler.groupdict()
                pagenum = int(result['pagenum'])
                itemnum = int(result['itemnum'])
                if pagenum==0:
                    _pages0 += 1
                else:
                    _pages1 += 1
                if itemnum==0:
                    _items0 += 1
                else:
                    _items1 += 1
        
#         print '==========%s============='%(file) 
#         print '_pages0: ',_pages0
#         print '_pages1: ',_pages1
#         print '_items0: ',_items0
#         print '_items1: ',_items1
#         print 'errors: ',errors
        if errors>10:
            title = 'dangerous error'
            msg = ' ip: %s \n time: %s, \n template: %s, \n error: %s'%(ip,datestr,file,'日志中有大量错误信息，需及时查找原因')
            send_mail(title,msg)
        if _pages1==0 and _pages0>3:
            title = 'dangerous error'
            msg = ' ip: %s \n time: %s, \n template: %s, \n error: %s'%(ip,datestr,file,'该网站已经被ban')
            send_mail(title,msg)
        elif _items1==0 and _items0>3:
            title = 'dangerous error'
            msg = ' ip: %s \n time: %s, \n template: %s, \n error: %s'%(ip,datestr,file,'该网站已经改版，请及时修改网站模板')
            send_mail(title,msg)
        elif _pages1>3 and _pages0/(_pages0+_pages1)>1/3:
            title = 'warning'
            msg = ' ip: %s \n time: %s, \n template: %s, \n error: %s'%(ip,datestr,file,'日志中0 pages/min已经超过1/3,网站抓取可能出错，请查看具体日志')
            send_mail(title,msg)
        elif _items1>3 and _items0/(_items0+_items1)>1/3:
            title = 'warning'
            msg = ' ip: %s \n time: %s, \n template: %s, \n error: %s'%(ip,datestr,file,'日志中0 items/min已经超过1/3,网站抓取可能出错，请查看具体日志')
            send_mail(title,msg)
        
        
if __name__ == '__main__':
    checklog()
        
        
        
