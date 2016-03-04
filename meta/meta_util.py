#encoding:utf-8
import os
import json
import datetime
import time
import re
import urlparse
import hashlib

from config import *

def load_cookie(conf_name):
    cookie_file_name = conf_name.split('.')[0]+'.cookie'
    cookie_path = os.path.join(PROJECT_PATH,'cookie',cookie_file_name)
#         print cookie_path
    try:
        f = open(cookie_path,'r')
        tmp = f.read().strip()
        f.close()
        try:
            cookie = json.loads(tmp)
        except:
            cookie = dict()
            items = tmp.split(';')
            for item in items:
                kv = item.split('=')
                if len(kv)>2:
                    for i in range(len(kv)-2):
                        kv[1] = kv[1] + '=' + kv[i+2]
                cookie[kv[0].strip()] = kv[1]
        return cookie
    except:
        return None

# def get_cur_item(results=[],res_num=''):
#     if not results:
#         return ''
#     reses = []
#     res_num_list = str(res_num).split(',')
#     for num in res_num_list:
#         if not num.strip():
#             continue
#         if res_num=='all':
#             #print results
#             for res in results:
#                 reses.append(res)
#             return ''.join(reses)
#         reses.append(results[int(num)])
#     return ''.join(reses)
def get_cur_item(results=[],res_num=''):
    if not results:
        return ''
    reses = []
    if res_num=='all':
        #print results
        for res in results:
            reses.append(res)
        return ''.join(reses)
    res_num_list = str(res_num).split(',')
    for num in res_num_list:
        if not num.strip():
            continue
        num = int(num)
        if int(num)<0:
            num = len(results)+num
        if int(num)>len(results)-1:
            num = len(results)-1
        reses.append(results[int(num)])
    return ''.join(reses)

# print get_cur_item(['a','b'],res_num='all')

def get_timestamp():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    todaystr = time.strptime(today,'%Y-%m-%d')
    d = datetime.datetime(* todaystr[:6])
    today_timestamp = time.mktime(d.timetuple())
    
    one_day = datetime.timedelta(days=1)
    yesterday = datetime.datetime.now()-one_day
    yesterdaystr = time.strptime(yesterday.strftime('%Y-%m-%d'),'%Y-%m-%d')
    d = datetime.datetime(* yesterdaystr[:6])
    yesterday_timestamp = time.mktime(d.timetuple())
    
    two_day = datetime.timedelta(days=2)
    yesterday = datetime.datetime.now()-two_day
    yesterdaystr = time.strptime(yesterday.strftime('%Y-%m-%d'),'%Y-%m-%d')
    d = datetime.datetime(* yesterdaystr[:6])
    twodaysago_timestamp = time.mktime(d.timetuple())
    return today_timestamp,yesterday_timestamp,twodaysago_timestamp

#清除html中的注释标签
COMMENT1_RE = '<!--[\s\S]*?-->'
JS_SCRIPT_RE = r'<\s*script[\s\S]*?</script>'
def clear_html_comment(content):
    content = re.sub(COMMENT1_RE, '', content, flags=re.I)
    content = re.sub(JS_SCRIPT_RE, '', content, flags=re.I)
    #content = content.replace('<!--','').replace('-->','')
    return content

# html = '''
# <!--tetsgakbkhkhkhska-->
# jjlajlelnljnklj'l'lkjklj'lkjklj
# tetsgakbkhkhkhska-->
# '''
# print clear_html_comment(html).strip()


#针对不同模板对content做特殊处理
def special_require_content(content,template_name):
    if template_name.find('yaolan_')!=-1:
        content = content.replace('<div id="box_9">','')
    return content

def get_domain(url_input):
    source = urlparse.urlparse(url_input).hostname
    if not source:
        return 'None','None'
    list_host = source.split('.')
    domain = ''
    if list_host[-1] == 'cn' and list_host[-2] in ('com','net','gov','org'):
        domain = '.'.join(source.split('.')[-3:-2])
    else:
        domain = '.'.join(source.split('.')[-2:-1])
    return domain,source

# print get_domain('http://www.chinanews.com.cn/gj/2015/06-10/7333248.shtml')

def get_tencent_id(url):
    tmps = url.split('?')[1].split('&')
    for tmp in tmps:
        t = tmp.split('=')
        if t[0]=='__biz':
            num = 0
            if len(t)>2:
                num = len(t) - 2 
            return t[1]+num*'='
# print get_tencent_id('http://mp.weixin.qq.com/s?__biz=MzA4NTQ5NzQ5OA==&mid=205993679&idx=2&sn=628cafe39d1c0d579a174f74f1b75c0c&3rd=MzA3MDU4NTYzMw==&scene=6#rd')

def get_meta_ip(network_card='enp7s0'):
    import socket, fcntl, struct
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', network_card))
    ip = socket.inet_ntoa(inet[20:24])
    return ip

def meta_redis_key():
    tiemflag = datetime.datetime.now().strftime('%m%d%H')
    meta_next_url = 'meta'+tiemflag
    return meta_next_url

def md5(str):
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()

