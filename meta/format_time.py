#encoding:utf-8
import re
import time
import datetime

#09-16
time_patt1 = '^\s*\d{1,2}\s*-\s*\d{1,2}\s*$'
pattern1 = re.compile(time_patt1)
#13:47 或者 13:47:01
time_patt2 = '(^\s*\d{1,2}\s*:\s*\d{1,2})|(^\s*\d{1,2}\s*:\s*\d{1,2}:\s*\d{1,2})'
pattern2 = re.compile(time_patt2)
# 2014-09-16 13:47:05
pattern5 = '^\s*\d{4}-\s*\d{1,2}\s*-\s*\d{1,2}\s*\d{1,2}\s*:\s*\d{1,2}:\d{1,2}'
pattern5 = re.compile(pattern5)
# 2014-09-16 13:47
time_patt3 = '^\s*\d{4}-\s*\d{1,2}\s*-\s*\d{1,2}\s*\d{1,2}\s*:\s*\d{1,2}$'
pattern3 = re.compile(time_patt3)
#09-16 13:47
time_patt4 = '^\s*\d{1,2}\s*-\s*\d{1,2}\s*\d{1,2}\s*:\s*\d{1,2}'
pattern4 = re.compile(time_patt4)
#昨天 13:47
time_patt6 = 'yeserday\s*\d{1,2}\s*:\s*\d{1,2}'
pattern6 = re.compile(time_patt6)
#5分钟前
time_patt7 = '^\s*\d{1,2}\s*minute$'
pattern7 = re.compile(time_patt7)
#1小时前
time_patt9 = '^\s*\d{1,2}\s*hour$'
pattern9 = re.compile(time_patt9)
#1423476240 时间戳
time_patt8 = '^\s*(\d+|\d+\.\d+)\s*$'
pattern8 = re.compile(time_patt8)
#2014-09-16
time_patt10 = '^\d{4}-\s*\d{1,2}\s*-\s*\d{1,2}$'
pattern10 = re.compile(time_patt10)
#15-10-08
time_patt11 = '^\d{2}-\s*\d{1,2}\s*-\s*\d{1,2}'
pattern11 = re.compile(time_patt11)

#2013年2月18日 17:53
#1月14日 10:52
#今天 10:30

def format_time(article_time,tg):
    article_time = str(article_time).strip()
    article_time = article_time.replace('今天'.decode('utf-8'),'').strip()
    article_time = article_time.replace('昨天'.decode('utf-8'),'yeserday').strip()
    article_time = article_time.replace('分钟前'.decode('utf-8'),'minute').strip()
    article_time = article_time.replace('小时前'.decode('utf-8'),'hour').strip()
    article_time = article_time.replace('年'.decode('utf-8'),'-').replace('月'.decode('utf-8'), '-').replace('日'.decode('utf-8'), ' ').strip()
    article_time = article_time.replace(u'\xa0',' ').strip()
    article_time = article_time.replace('[','').strip()
    article_time = article_time.replace(']','').strip()
    article_time = article_time.replace('.','-').strip()
    article_time = article_time.replace('/','-').strip()
    if pattern11.search(article_time):
	article_time = '20'+article_time
    if pattern1.search(article_time):
        localtime = time.localtime(float(tg))
        localtime = datetime.datetime(* localtime[:6])
        year = localtime.year
        tmp = article_time.split('-')
        month = tmp[0].strip()
        day = tmp[1].strip()
        timestr = str(year)+'-'+str(month)+'-'+str(day)
        t = time.strptime(timestr, "%Y-%m-%d")
        res_time = datetime.datetime(* t[:6])
        return res_time
    elif pattern2.search(article_time):
        localtime = time.localtime(float(tg))
        localtime = datetime.datetime(* localtime[:6])
        year = localtime.year
        month = localtime.month
        day = localtime.day
        timestr = str(year)+'-'+str(month)+'-'+str(day)
        article_time = article_time.replace(' ','')
        article_time = timestr+' '+article_time
        try:
            localtime = time.strptime(article_time, "%Y-%m-%d %H:%M")
        except:
            localtime = time.strptime(article_time, "%Y-%m-%d %H:%M:%S")
        localtime = datetime.datetime(* localtime[:6])
        return localtime
    elif pattern3.search(article_time):
#         article_time = str(article_time).replace(' ', '')
        t = time.strptime(article_time, "%Y-%m-%d %H:%M")
        res_time = datetime.datetime(* t[:6])
        return res_time
    elif pattern5.search(article_time):
#         article_time = str(article_time).replace(' ', '')
        t = time.strptime(article_time, "%Y-%m-%d %H:%M:%S")
        res_time = datetime.datetime(* t[:6])
        return res_time
    elif pattern4.search(article_time):
        localtime = time.localtime(float(tg))
        localtime = datetime.datetime(* localtime[:6])
        year = localtime.year
        tmp = article_time.split('-')
        month = tmp[0].strip()
        day = tmp[1].strip()
        timestr = str(year)+'-'+str(month)+'-'+str(day)
#         timestr = str(timestr).replace(' ', '')
        t = time.strptime(timestr, "%Y-%m-%d %H:%M")
        res_time = datetime.datetime(* t[:6])
        return res_time
    elif pattern6.search(article_time):
        localtime = time.localtime(float(tg))
        localtime = datetime.datetime(* localtime[:6])
        s = datetime.timedelta(hours=24)
        localtime = localtime -s
        return localtime
    elif pattern8.search(article_time):
	length = len(str(article_time))
	if length==8:
	    t = time.strptime(article_time, "%Y%m%d")
	    res_time = datetime.datetime(* t[:6])
	    return res_time
        localtime = time.localtime(float(article_time))
        localtime = datetime.datetime(* localtime[:6])
        return localtime
    elif pattern7.search(article_time):
        cur = tg - int(article_time.replace('minute','').strip())*60
        localtime = time.localtime(cur)
        localtime = datetime.datetime(* localtime[:6])
        return localtime
    elif pattern9.search(article_time):
        cur = tg - int(article_time.replace('hour','').strip())*3600
        localtime = time.localtime(cur)
        localtime = datetime.datetime(* localtime[:6])
        return localtime
    elif pattern10.search(article_time):
        t = time.strptime(article_time, "%Y-%m-%d")
        res_time = datetime.datetime(* t[:6])
        return res_time
    article_time = str(article_time).replace(' ', '')
    try:
        t = time.strptime(article_time, "%Y-%m-%d")
        res_time = datetime.datetime(* t[:6])
    except ValueError:
        res_time = ''
    return res_time

if __name__ == '__main__':
    st = '2013-12-25 08:15'
    st = '2014年04月15日13:43'
    st = '2014年04月15日'
    st = time.time()
    st = '24分钟前'
    st = '1小时前'
    st = '12:12:13'
    st = '2015-05-22 15:48:08'
    st = ' 2015-05-22 '
    st = '15-05-22 15:48:08'
    st = '20130708'
    tg = time.time()
    res = format_time(st,tg)
    print res
    print type(res)
    
