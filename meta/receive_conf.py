#encoding:utf-8
import os

#['conf',{'m1':'v1'}]
def receive_conf(filename):
    #print 'filename: ',filename
    f = open(filename,'r')
    datas = f.readlines()
    f.close()
    params = {}
    for data in datas:
        data = data.strip()
        #data = data.replace('@@SPACE',' ')
        if not data:
            continue
        if data.startswith('#'):
            continue
        item = data.split(':')
        if len(item)>2:
            for i in range(len(item)-2):
                item[1] = item[1]+':'+item[i+2]
        if not item[1].strip() and item[0].endswith('_Num'):
            item[1] = 0
        elif not item[1].strip():
            item[1] = None
        if item[1] and item[0].endswith('_Split'):
            item[1] = item[1].decode('utf-8')
            item[1] = item[1].replace(u'&nbsp;',u'\xa0')
            item[1] = item[1].replace(u'@@SPACE',' ')
        params[item[0]] = item[1]
    
    basename = os.path.basename(filename)
    return [basename,params]
    
if __name__ == '__main__':
    filename = 'D:\workspace\meta\pattern\sogou_weixin_day.conf'
    filename = r'D:\workspace\meta\pattern\baidu_wenda_time.conf'
    filename = r'D:\workspace\meta\pattern\baidu_news_time.conf'
    filename = r'D:\workspace\meta\pattern\sina_news_time.conf'
    confs = receive_conf(filename)
    print confs[1]['Date_Xpath_RE']
#  
# {'Cluster_Url_Xpath_Num': '', 'Click_Xpath_Num': '', 'Url_Rear_Part': '&tsn=1&type=2&ie=utf8', 'Url_Front_Part': 'http', 'Author_Xpath_Num': '0', 'Author_Xpath': 'div[@class="s-p"]/a/@title', 'Reply_Xpath': '', 'Items_Per_Page': '10', 'ID_Xpath_Num': '', 'ID_Xpath': '', 'Skip_Blanks': 'TBA', 'Url_XPath_Num': '0', 'Title_Xpath_Num': 'all', 'Text_Encoding': 'utf-8', 'Date_Xpath': 'div[@class="s-p"]/@t', 'Date_Xpath_Num': '0', 'Cluster_Url_Xpath': '', 'Abstarct_Xpath': 'p/text()', 'Url_Change_page': '&page=', 'Name_Xpath': '', 'Item_Xpath': '//div[@class="results"]/div[@class="wx-rb wx-rb3"]/div[@class="txt-box"]', 'Sleep_Flag': 'SEARCH_ENGINE_SLEEP', 'Abstarct_Xpath_Num': 'all', 'Url_XPath': 'h4/a/@href', 'Query_Skip_Items': '1', 'Click_Xpath': '', 'Escape_Encoding': 'UPB', 'Site_Type': 'weixin', 'SE_Sleep_Base': '30', 'Query_Encoding': 'utf-8', 'Title_Xpath': 'h4/a/text()', 'Result_Order': 'UTBAID', 'SE_Sleep_Rand': '60'}
