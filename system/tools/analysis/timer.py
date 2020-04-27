from threading import Timer
# 每隔5分钟执行一次任务
import requests
import sqlite3
from bs4 import BeautifulSoup
import jieba
import jieba.posseg as peg
import os
import json
import random
import pickle
import re
import time
from datetime import datetime
from tqdm import tqdm
from lstm_attn_utils import get_topic_senti_att
from topic_utils import test

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
}
 
cop = re.compile("[^\u4e00-\u9fa5^.^,^，^0-9]")
stop = pickle.load(open('./data/stop.txt', 'rb'))



def get_max_page(url, cookies):
    response = requests.get(url, cookies=cookies, headers=headers).text
    # print(response)
    soup = BeautifulSoup(response, 'lxml')
    topic_max_page = list(set(soup.find_all('input', attrs={'data-role': 'goto-input'})))[0]['max']
    return topic_max_page


def post_related_reply(cursor, conn, thread_id):
    search_sql = '''select * FROM system_reply where post_id=?'''
    search_res = cursor.execute(search_sql, (thread_id,)).fetchall()
    reply_records = []
    for record in search_res:
        reply_records.append(record[2])
    return reply_records


def update_keywords(cursor, conn, time_formater, new_words):
    search_sql = '''select * FROM system_info where time=?'''
    search_res = cursor.execute(search_sql, (time_formater,)).fetchall()[0]
    key_words = search_res[-1]

    update_key_words = key_words+new_words
    # print(update_key_words)
    update_sql = '''update system_info set key_words=? where time=?'''
    cursor.execute(update_sql, (update_key_words, time_formater))
    conn.commit()


#bbs爬虫程序
def bbs(cursor, conn, records, cookies):
    
    # topic为需要爬取的版面，以及各个版面的代号，通过代号可以拼接成各版面的首页URL           
    topic = {'secret':'414', 'bridge':'167', 'mental':'690', 'love':'36', 'school':'1431', 'not_mian':'251','job':'99',
             'joke':'72','cov':'1465','stock':'249','water':'103','health':'414','comic':'108',}
    for t in topic:
        finish_flag = False        #爬虫结束条件：主帖ID在数据库中&最后一条回帖ID也在数据库中，满足条件时，finish_flag = ture
        for page in range(3):
            if finish_flag:
                break
            print('************topic {} page {}***********'.format(t, page))  #打印正在爬取哪个板块下的第几页的数据
            # directory_url为拼接各个版面的URL，page指定爬取的是哪一页
            # 每一页中有很多主帖，待会需要对主帖一个个进行爬取
            directory_url = 'https://bbs.pku.edu.cn/v2/thread.php?bid=' + topic[t] + '&mode=topic&page=' + str(page+1)
            #通过requests.get（）方法爬取页面数据
            response = requests.get(directory_url, cookies=cookies, headers=headers).text
            #BeautifulSoup（）构造一个页面解析器
            soup = BeautifulSoup(response, 'html.parser')
            # items为该页所有主帖集合，soup.find_all（）找到list-item-topic list-item下的数据，需要的数据就在这里
            items = soup.find_all('div', {'class': 'list-item-topic list-item'})


            # 对所有帖子进行分析

            for item in items:
                thread_id = item['data-itemid']   #获取主帖ID
                if int(thread_id) < 0:            #存在主帖ID小于0，这类帖子不需要
                    continue

                # 如果该主帖存在于数据库中，那么有两种可能，一种是该主帖里面的回帖量没变，说明已经爬取到上次爬取的地方了，这次不需要再爬取了
                # 第二种可能就是该主帖里面的回帖出现了变化，那说明帖子有了新的回复，被顶上来了，这种情况需要继续爬取
                # thread_finish用于记录第二种情况，有新回复，爬虫爬取完新回复则可以结束
                thread_finish = False
                if thread_id in records:
                    print('**主帖数据库中存在**')
                    # 1.首先获取该帖在数据库中的所有回帖ID
                    reply_records = post_related_reply(cursor, conn, thread_id)
                    # 2.倒序从该主帖的回帖中和reply_records进行对比
                    #   为了倒序爬取，首先需要获得该帖的回复的最后一页，即该帖中的最大页数
                    reply_url = 'https://bbs.pku.edu.cn/v2/post-read.php?bid=' + topic[t] + '&threadid=' + str(thread_id)
                    max_reply_page = get_max_page(reply_url, cookies)

                    # 倒序
                    for reply_page in range(int(max_reply_page), -1, -1)[:-1]:
                        # 构造用于每页回帖的URL
                        page_url = reply_url + '&page=' + str(reply_page)
                        response = requests.get(page_url, cookies=cookies, headers=headers).text
                        soup = BeautifulSoup(response, 'lxml')
                        replies = soup.find_all('div', class_='post-card')
                        for i, content in enumerate(replies[::-1]):
                            try:
                                cid = content.find('div').attrs['id']  #获取回帖ID，倒序进行
                            except Exception as e:
                                continue
                            

                            # i=0，表示这是最后一条回帖，如果该帖的最后一个回帖ID出现在回帖记录中，说明无需继续爬取，就可以去下一个版面
                            if i== 0 and cid in reply_records:
                                print('=所有回帖也都存在，结束！！！')
                                finish_flag = True
                                break
                            # 如果该回帖在数据库中，就可以去爬下一个主帖了
                            if cid in reply_records:
                                print('==爬取到数据库存在的记录，将爬取下一个主帖')
                                thread_finish = True
                                break
                            else:
                                print('===>回帖数据不存在，内容: ',end=' ')
                                # 如果回帖不在回帖记录中，则爬取该回帖的发帖时间，回帖内容等信息
                                post_time = content.find('div', class_='sl-triangle-container').select('span')[-1].get_text()[
                                    3:]
                                post_time = datetime.strptime(post_time, '%Y-%m-%d %H:%M:%S') #处理成需要的时间格式
                                content = content.find('div', class_='body file-read image-click-view').select('p')
                                complete_text = ''
                                #拼接回帖信息（有很多段的那种）
                                for item in content:
                                    if len(item.attrs) != 0:
                                        break
                                    text = str(item.get_text().strip())
                                    if text[:9] == 'Anonymous':
                                        break
                                    complete_text += text
                                #把爬取的文本中非文本信息去除
                                post_content = cop.sub('', complete_text)
                                if len(post_content) > 240 or len(post_content)<=1:
                                    continue
                                print(post_content)

                                # 将分词的结果写入信息表，首先要获取分词结果
                                content_cut = list(jieba.cut(post_content))
                                cut_result = ''
                                for item in content_cut:
                                    try:
                                        tag = list(list(peg.cut(item))[0])[-1]    #获取每个分词的词性
                                    except Exception as e:
                                        print(item)
                                        print('**********8')
                                        os._exit(0)
                                        # continue
                                    if tag != 'n' or item in stop:    #只留下非停用词的名词
                                        continue
                                    cut_result += item


                                post_topic = test(post_content)   #获取文本主题
                                senti, att = get_topic_senti_att(post_content)   #获取情感

                                love_num, others_num, psy_num, study_num, career_num =0, 0, 0, 0, 0
                                if post_topic == '恋爱关系':
                                    love_num += 1
                                elif post_topic == '其他':
                                    others_num += 1
                                elif post_topic == '心理方面':
                                    psy_num += 1
                                elif post_topic == '学业方面':
                                    study_num += 1
                                else:
                                    career_num += 1


                                senti_value = 3-senti if senti >= 4 else senti   #将情感进行为3，4，5的转换成情感得分为-1，-2，-3
                                neg_senti_value = 0 if senti <= 3 else 3-senti

                                if neg_senti_value == -3:          #高危个体，插入高危个体信息表中
                                    insertRisk({
                                        'post_id':thread_id,
                                        'reply_id':cid, 
                                        'content':post_content,
                                        'time':post_time, 
                                        'topic':post_topic, 
                                        'process': 0, 
                                        'url': page_url
                                        }, cursor, conn)


                                insertInfo({                  #将本次爬虫数据的信息插入分类信息统计表中
                                    'post_time': post_time, 
                                    'senti_value':senti_value, 
                                    'post_num': 1,
                                    'career_num': career_num,
                                    'love_num':love_num,
                                    'others_num':others_num,
                                    'psy_num':psy_num,
                                    'study_num':study_num,
                                    'neg_senti_value': neg_senti_value,
                                    'key_words': cut_result
                                    }, cursor, conn)

                                insertPost({                #将回帖信息插入回帖信息表中
                                    'post_id': thread_id,
                                    'cid': cid,
                                    'time': post_time,
                                    'content': post_content,
                                    'source': 1,
                                    'senti': senti,
                                    'topic': post_topic,
                                    'process': 0,
                                    'url': page_url
                                }, cursor, conn, 'reply')

                        if finish_flag or thread_finish:
                            break
                else:
                     # 如果主帖不在数据库记录中，就可以正常爬取
                    # 首先爬取帖子标题，然后爬取帖子下面的回复
                    print('##主帖不存在于数据库',end=' ')
                     #构造回帖URL
                    reply_url = 'https://bbs.pku.edu.cn/v2/post-read.php?bid=' + topic[t] + '&threadid=' + str(thread_id)
                    response = requests.get(reply_url, cookies=cookies).text
                    soup = BeautifulSoup(response, 'lxml')
                    post_time = soup.find('div', class_='sl-triangle-container').select('span')[-1].get_text()[3:]
                    post_time = datetime.strptime(post_time, '%Y-%m-%d %H:%M:%S')

                    max_reply_page = get_max_page(reply_url, cookies)

                    skip = ['封禁', '公告', '恢复']
                     #获取帖子的题目
                    title = cop.sub('', str(soup.find_all('title')[0].get_text()).strip().split('-')[0])
                    if len(title) <= 1:
                            continue
                    print(title)

                    content_cut = list(jieba.cut(title))
                    cut_result = ''
                    for item in content_cut:
                        if list(list(peg.cut(item))[0])[-1] != 'n' or item in stop:
                            continue
                        cut_result += item
                    title_topic = test(title)
                    love_num, others_num, psy_num, study_num, career_num =0, 0, 0, 0, 0
                    if title_topic == '恋爱关系':
                        love_num += 1
                    elif title_topic == '其他':
                        others_num += 1
                    elif title_topic == '心理方面':
                        psy_num += 1
                    elif title_topic == '学业方面':
                        study_num += 1
                    else:
                        career_num += 1
                    if sum([title.find(sign) for sign in skip]) != -3:
                        continue

                    senti, att = get_topic_senti_att(title)
                    senti_value = 3-senti if senti >= 4 else senti
                    neg_senti_value = 0 if senti <= 3 else 3-senti

                    if neg_senti_value == -3:
                        insertRisk({
                            'post_id':thread_id,
                            'reply_id':thread_id, 
                            'content':title,
                            'time':post_time, 
                            'topic':title_topic, 
                            'process': 0, 
                            'url': reply_url
                            }, cursor, conn)


                    insertInfo({
                        'post_time': post_time, 
                        'senti_value':senti_value, 
                        'post_num': 1,
                        'career_num': career_num,
                        'love_num':love_num,
                        'others_num':others_num,
                        'psy_num':psy_num,
                        'study_num':study_num,
                        'neg_senti_value': neg_senti_value,
                        'key_words': cut_result
                        }, cursor, conn)


                    
                    insertPost({
                        'post_id': thread_id,
                        'time': post_time,
                        'content': title,
                        'source': 1,
                        'senti': senti,
                        # 'attention': att,
                        'topic': title_topic,
                        'process': 0,
                        'url': reply_url
                    }, cursor, conn)


                    # 然后爬取帖子下对应的回帖
                    for reply_page in range(int(max_reply_page)):
                        page_url = reply_url + '&page=' + str(reply_page + 1)
                        response = requests.get(page_url, cookies=cookies, headers=headers).text
                        soup = BeautifulSoup(response, 'lxml')
                        replies = soup.find_all('div', class_='post-card')
                        for i, content in enumerate(replies):

                            print('===>爬取回帖信息: 内容:', end=' ')
                            try:
                                cid = content.find('div').attrs['id']
                                post_time = content.find('div', class_='sl-triangle-container').select('span')[-1].get_text()[
                                        3:]
                            except Exception as e:
                                continue
                            
                            post_time = datetime.strptime(post_time, '%Y-%m-%d %H:%M:%S')

                            content = content.find('div', class_='body file-read image-click-view').select('p')
                            complete_text = ''
                            for item in content:
                                if len(item.attrs) != 0:
                                    break
                                text = str(item.get_text().strip())
                                if text[:9] == 'Anonymous':
                                    break
                                complete_text += text
                            post_content = cop.sub('', complete_text)
                            if len(post_content) > 240 or len(post_content)<=1:
                                continue
                            print(post_content)
                            content_cut = list(jieba.cut(post_content))
                            cut_result = ''
                            for item in content_cut:
                                if list(list(peg.cut(item))[0])[-1] != 'n' or item in stop:
                                    continue
                                cut_result += item
                            post_topic = test(post_content)
                            senti, att = get_topic_senti_att(post_content)

                            love_num, others_num, psy_num, study_num, career_num =0, 0, 0, 0, 0
                            if post_topic == '恋爱关系':
                                love_num += 1
                            elif post_topic == '其他':
                                others_num += 1
                            elif post_topic == '心理方面':
                                psy_num += 1
                            elif post_topic == '学业方面':
                                study_num += 1
                            else:
                                career_num += 1
                            # print(love_num, others_num, psy_num, study_num, career_num)


                            senti_value = 3-senti if senti >= 4 else senti
                            neg_senti_value = 0 if senti <= 3 else 3-senti

                            if neg_senti_value == -3:
                                insertRisk({
                                    'post_id':thread_id,
                                    'reply_id':cid, 
                                    'content':post_content,
                                    'time':post_time, 
                                    'topic':post_topic, 
                                    'process': 0, 
                                    'url': page_url
                                    }, cursor, conn)


                            insertInfo({
                                'post_time': post_time, 
                                'senti_value':senti_value, 
                                'post_num': 1,
                                'career_num': career_num,
                                'love_num':love_num,
                                'others_num':others_num,
                                'psy_num':psy_num,
                                'study_num':study_num,
                                'neg_senti_value': neg_senti_value,
                                'key_words': cut_result
                                }, cursor, conn)

                            insertPost({
                                'post_id': thread_id,
                                'cid': cid,
                                'time': post_time,
                                'content': post_content,
                                'source': 1,
                                'senti': senti,
                                # 'attention': att,
                                'topic': post_topic,
                                'process': 0,
                                'url': page_url
                            }, cursor, conn, 'reply')
                    # print('======================================')

                if finish_flag:
                    break

            


def insertInfo(data, cursor, conn):
    search_time = data['post_time']
    y, m, d = search_time.year, search_time.month, search_time.day
    time_formater = datetime(y, m, d, 0, 0)
    data['time'] = time_formater
    search_sql = '''select * FROM system_info where time=?'''
    search_res = cursor.execute(search_sql, (time_formater,)).fetchall()

    if len(search_res) == 0:
        # print(time_formater, 'insert')
        insert_data_sql = '''insert into system_info (time, senti_value, post_num, career_num, love_num, others_num, psy_num, study_num, neg_senti_value, key_words) values (:time, :senti_value, :post_num, :career_num, :love_num, :others_num, :psy_num, :study_num, :neg_senti_value,:key_words)'''
        cursor.execute(insert_data_sql, data)
    else:
        # print(time_formater, 'update')
        search_res = search_res[0]
        idx, time, senti_value, post_num, career_num, love_num, others_num, psy_num, study_num, neg_senti_value, key_words = search_res[0], search_res[1], search_res[2], search_res[3], search_res[4], search_res[5], search_res[6], search_res[7], search_res[8], search_res[9], search_res[-1]
        update_sql = '''update system_info set senti_value=?, post_num=?, career_num=?, love_num=?,others_num=?, psy_num=?, study_num=?, neg_senti_value=?, key_words=? where time=?'''
        cursor.execute(update_sql, (data['senti_value']+senti_value, post_num+1, career_num+data['career_num'], love_num+data['love_num'], others_num+data['others_num'], psy_num+data['psy_num'], study_num+data['study_num'], neg_senti_value+data['neg_senti_value'], key_words+data['key_words'], time))


def insertRisk(data, cursor, conn):
    search_sql = '''select * FROM system_high_risk where post_id=? and reply_id=?'''
    search_res = cursor.execute(search_sql, (data['post_id'], data['reply_id'],)).fetchall()
    if len(search_res) == 0:
        insert_data_sql = '''insert into system_high_risk (post_id, reply_id, content, time, topic, process, url) values (:post_id, :reply_id, :content, :time, :topic, :process, :url)'''
        cursor.execute(insert_data_sql, data)
    else:
        return


def insertPost(data, cursor, conn, which='post'):
    # print(data)
    if which == 'post':
        insert_data_sql = '''insert into system_post (post_id, time, content, source, senti, topic, process, url)
        values (:post_id, :time, :content, :source, :senti, :topic, :process, :url)'''
    else:
        insert_data_sql = '''insert into system_reply (post_id, reply_id, time, content, source, senti, topic, process, url)
            values (:post_id, :cid, :time, :content, :source, :senti, :topic, :process, :url)'''
    cursor.execute(insert_data_sql, data)
    conn.commit()


def get_bbs_cookie():
    import json
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver import ActionChains

    # 1. 获取树洞首页的

    driver = webdriver.Firefox(executable_path=r'F:\软件\安装包\geckodriver-v0.26.0-win64\geckodriver.exe')
    driver.get("https://bbs.pku.edu.cn/v2/thread.php?bid=414")
    time.sleep(3)
    username = driver.find_element_by_id('username')
    username.send_keys('CNNman')
    
    passwords = driver.find_element_by_class_name('not-login').find_elements_by_tag_name('input')[1]
    passwords.clear()
    passwords.send_keys('wangchao1995')

    auto_login = driver.find_elements_by_tag_name('label')[0]
    auto_login.click()
    
    submit = driver.find_element_by_id('btn-login')
    submit.click()

    driver.get("https://bbs.pku.edu.cn/v2/thread.php?bid=414")
    cookie_items = driver.get_cookies()
    post = {}
    for cookie_item in cookie_items:
        post[cookie_item['name']] = cookie_item['value']
    cookie_str = json.dumps(post)
    with open('cookie.txt', 'w', encoding='utf-8') as f:
        f.write(cookie_str)
    print('ok')


#爬虫主程序
def crawl():
    # get_bbs_cookie用于获取已登录信息的cookie，某些版面需要登陆才能访问，需要通过cookie去登陆
    # get_bbs_cookie()    
    # os._exit(0)
    with open('cookie.txt', 'r', encoding='utf-8') as f:
        cookie = f.read()
        cookies = json.loads(cookie)
    print(cookies)
    # os._exit(0)

    # 连接数据库
    conn = sqlite3.connect('../../../db.sqlite3')
    cursor = conn.cursor()

    # records用于记录已爬取的主帖ID
    records = {}

    items_post = cursor.execute('''select post_id from system_post''')  #获取数据库中所有的主帖ID
    for v in items_post:
        records[v[0]] = 1

    bbs(cursor, conn, records, cookies)  #调用bbs()方法开始爬取bbs上的数据

    t = Timer(60, crawl)  #间隔一分钟爬取一次
    t.start()
    

if __name__ == "__main__":
    crawl()