import requests
import sqlite3
from bs4 import BeautifulSoup
import os
import json
import random
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




def get_max_page(url, cookies):
    response = requests.get(url, cookies=cookies, headers=headers).text
    # print(response)
    soup = BeautifulSoup(response, 'lxml')
    topic_max_page = list(set(soup.find_all('input', attrs={'data-role': 'goto-input'})))[0]['max']
    return topic_max_page


def bbs(cursor, conn, records, cookies):
           
    res = {'post': [], 'reply': []}
    topic = {'secret':'414', 'bridge':'167', 'mental':'690', 'love':'36', 'school':'1431', 'not_mian':'251'}
    for t in topic:
        directory_url = 'https://bbs.pku.edu.cn/v2/thread.php?bid=' + topic[t]
        max_page = get_max_page(directory_url, cookies)
        # max_page = 10
        for page in range(2):
            print('topic {} page {}'.format(t, page))
            # if page != 0 and page % 5 == 0:      
            #     wait_sec = random.randint(180, 240)
            #     print('**** wait for {} s ****'.format(wait_sec))
            #     time.sleep(wait_sec)
            directory_url = 'https://bbs.pku.edu.cn/v2/thread.php?bid=' + topic[t] + '&mode=topic&page=' + str(page)
            response = requests.get(directory_url, cookies=cookies, headers=headers).text
            
            soup = BeautifulSoup(response, 'html.parser')
            items = soup.find_all('div', {'class': 'list-item-topic list-item'})

            # 页面中有的发帖
            for item in items:
                thread_id = item['data-itemid']
                if int(thread_id) < 0:
                    continue
                reply_url = 'https://bbs.pku.edu.cn/v2/post-read.php?bid=' + topic[t] + '&threadid=' + str(thread_id)
                # if thread_id in records:
                #     continue
                response = requests.get(reply_url, cookies=cookies).text
                # print(response)
                # os._exit(0)
                soup = BeautifulSoup(response, 'lxml')
                post_time = soup.find('div', class_='sl-triangle-container').select('span')[-1].get_text()[3:]
                post_time = datetime.strptime(post_time, '%Y-%m-%d %H:%M:%S')

                max_reply_page = get_max_page(reply_url, cookies)
                skip = ['封禁', '公告', '恢复']
                title = cop.sub('', str(soup.find_all('title')[0].get_text()).strip().split('-')[0])
                if len(title) <= 1:
                        continue
                print(title)
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
                print(love_num, others_num, psy_num, study_num, career_num)


                if sum([title.find(sign) for sign in skip]) != -3:
                    continue

                senti, att = get_topic_senti_att(title)
                senti_value = 3-senti if senti >= 4 else senti
                neg_senti_value = 0 if senti <= 3 else 3-senti

                print(senti)
                os._exit(0)

                # if neg_senti_value == -3:
                #     insertRisk({
                #         'post_id':thread_id,
                #         'reply_id':thread_id, 
                #         'content':title,
                #         'time':post_time, 
                #         'topic':title_topic, 
                #         'process': 0, 
                #         'url': reply_url
                #         }, cursor, conn)


                # insertInfo({
                #     'post_time': post_time, 
                #     'senti_value':senti_value, 
                #     'post_num': 1,
                #     'career_num': career_num,
                #     'love_num':love_num,
                #     'others_num':others_num,
                #     'psy_num':psy_num,
                #     'study_num':study_num,
                #     'neg_senti_value': neg_senti_value
                #     }, cursor, conn)


                
                # insertPost({
                #     'post_id': thread_id,
                #     'time': post_time,
                #     'content': title,
                #     'source': 1,
                #     'senti': senti,
                #     # 'attention': att,
                #     'topic': title_topic,
                #     'process': 0,
                #     'url': reply_url
                # }, cursor, conn)
            

                # 进入主题帖后的子帖
                for reply_page in range(int(max_reply_page)):
                    page_url = reply_url + '&page=' + str(reply_page + 1)
                    if page_url in records:
                        continue
                    response = requests.get(page_url, cookies=cookies, headers=headers).text
                    soup = BeautifulSoup(response, 'lxml')

                    replies = soup.find_all('div', class_='post-card')
                    for i, content in enumerate(replies):
                        # print(content)
                        cid = content.find('div').attrs['id']
                        post_time = content.find('div', class_='sl-triangle-container').select('span')[-1].get_text()[
                                    3:]
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

                        # if neg_senti_value == -3:
                        #     insertRisk({
                        #         'post_id':thread_id,
                        #         'reply_id':cid, 
                        #         'content':post_content,
                        #         'time':post_time, 
                        #         'topic':post_topic, 
                        #         'process': 0, 
                        #         'url': page_url
                        #         }, cursor, conn)


                        insertInfo({
                            'post_time': post_time, 
                            'senti_value':senti_value, 
                            'post_num': 1,
                            'career_num': career_num,
                            'love_num':love_num,
                            'others_num':others_num,
                            'psy_num':psy_num,
                            'study_num':study_num,
                            'neg_senti_value': neg_senti_value
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
                print('======================================')
                # os._exit(0)
    return res


def insertInfo(data, cursor, conn):
    search_time = data['post_time']
    y, m, d = search_time.year, search_time.month, search_time.day
    time_formater = datetime(y, m, d, 0, 0)
    data['time'] = time_formater
    search_sql = '''select * FROM system_info where time=?'''
    search_res = cursor.execute(search_sql, (time_formater,)).fetchall()

    if len(search_res) == 0:
        print(time_formater, 'insert')
        insert_data_sql = '''insert into system_info (time, senti_value, post_num, career_num, love_num, others_num, psy_num, study_num, neg_senti_value) values (:time, :senti_value, :post_num, :career_num, :love_num, :others_num, :psy_num, :study_num, :neg_senti_value)'''
        cursor.execute(insert_data_sql, data)
    else:
        print(time_formater, 'update')
        search_res = search_res[0]
        idx, time, senti_value, post_num, career_num, love_num, others_num, psy_num, study_num, neg_senti_value = search_res[0], search_res[1], search_res[2], search_res[3], search_res[4], search_res[5], search_res[6], search_res[7], search_res[8], search_res[9]
        update_sql = '''update system_info set senti_value=?, post_num=?, career_num=?, love_num=?,others_num=?, psy_num=?, study_num=?, neg_senti_value=? where time=?'''
        cursor.execute(update_sql, (data['senti_value']+senti_value, post_num+1, career_num+data['career_num'], love_num+data['love_num'], others_num+data['others_num'], psy_num+data['psy_num'], study_num+data['study_num'], neg_senti_value+data['neg_senti_value'], time))


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



def insertHole(data, cursor, conn):
    insert_data_sql = '''insert into system_hole (post_id, time, content, source, senti, topic, process, page)
        values (:post_id, :time, :content, :source, :senti, :topic, :process, :page)'''
    cursor.execute(insert_data_sql, data)
    conn.commit()


def hole(cursor, conn):
    import json
    from selenium import webdriver
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver import ActionChains




    # 1. 获取树洞首页的


    driver = webdriver.Firefox(executable_path=r'F:\软件\安装包\geckodriver-v0.26.0-win64\geckodriver.exe')
    driver.get("https://pkuhelper.pku.edu.cn/hole/")
    time.sleep(3)
    login = driver.find_element_by_link_text('登录到 PKU Helper')
    time.sleep(3)
    form = login.click()
    token = driver.find_elements_by_tag_name('input')[-1]
    token.clear()
    token.send_keys('nb06ek1p9epw38y4sv9w59qkw2u2v1js')
    submit = driver.find_elements_by_tag_name('button')[-2]
    submit.click()

    start_pid = '1273265'
    while int(start_pid)>1000000:
        search = driver.find_element_by_class_name('control-search')
        search.clear()
        search.send_keys(start_pid)
        search.send_keys(Keys.ENTER)
        time.sleep(8)


        ac = driver.find_element_by_xpath("//div[@class='flow-item']")
        ActionChains(driver).move_to_element(ac).click(ac).perform()
        # os._exit(0)

        reply_time_boxes = driver.find_elements_by_class_name('box-header')
        reply_content_boxes = driver.find_elements_by_class_name('box-content')
        # print(reply_boxes)
        records_pid = []
        for i, box in enumerate(reply_time_boxes):
            pid = box.text.strip().replace('\n', '').split(' ')[0][1:]

            post_time = box.find_elements_by_tag_name('time')[0].get_attribute('title')
            if i == 0:
                # post_time = ' '.join(time_data[2:])
                pid = box.text.strip().replace('\n', '').split(' ')[2][1:]
                if len(pid) != 7:
                    continue
                post_content = cop.sub('', reply_content_boxes[i].text.strip())
            else:
                # post_time = ' '.join(time_data[:])
                if len(pid) != 7:
                    continue
                post_content_first_split = reply_content_boxes[i].text.strip().split('] ')[1:]
                # print(post_time, post_content_first_split)
                if len(post_content_first_split) > 0:
                    second_split = post_content_first_split[0].split(': ')
                    if len(second_split) > 1:
                        post_content = cop.sub('', second_split[1:][0])
                    else:
                        post_content = cop.sub('', second_split[:][0])
            if pid not in records_pid:
                records_pid.append(pid)
                print(pid, post_time, post_content)

                senti, att = get_topic_senti_att(post_content)
                topic = test(post_content)

                if senti <= 3:
                    post_content = ''
                reply_content = {}
                reply_content['post_id'], reply_content['time'], reply_content[
                    'content'], reply_content['source'], reply_content['senti'], \
                reply_content['topic'], reply_content['process'], reply_content['page'] = \
                    pid, post_time, post_content, 0, senti, topic, 0, pid

                

                #写入数据库
                insertHole(reply_content, cursor, conn)

        start_pid = str(int(start_pid)-1)
        # content = driver.find_elements_by_class_name('box-content')
        # records = []
        # for i, reply in enumerate(content):
        #     item = reply.text.strip()
        #     if i == 0:
        #         res = cop.sub('', item)
        #     else:
        #         first_split = item.split('] ')[1:]
        #         if len(first_split)>0:
        #             second_split = first_split[0].split(': ')
        #             if len(second_split) > 1:
        #                 res = cop.sub('', second_split[1:][0])   
        #             else:
        #                 res = cop.sub('', second_split[:][0])
        #         if res in records:
        #             continue
        #         print(res)
        #         records.append(res)
        # os._exit(0)


    # print(driver)

    # os._exit(0)
    # page = 102
    # # res = {'post': [], 'reply': []}
    # while page < 5000:
    #     if page != 1 and page % 50 == 0:      
    #             wait_sec = random.randint(180, 240)
    #             print('**** wait for {} s ****'.format(wait_sec))
    #             time.sleep(wait_sec)
    #     first_page = 'https://pkuhelper.pku.edu.cn/services/pkuhole/' \
    #                  'api.php?action=getlist&p=' + str(page) + \
    #                  '&PKUHelperAPI=3.0&jsapiver=200212152617-439546&' \
    #                  'user_token=nb06ek1p9epw38y4sv9w59qkw2u2v1js'
    #     first_page_articls = requests.get(first_page, headers=headers).text
    #     print(first_page_articls)
    #     first_page_articls = json.loads(first_page_articls)['data']
    #     print(first_page_articls)
    #     os._exit(0)
    #     # page_posts = []
    #     title = {}
    #     for data in first_page_articls:
    #         item = {}
    #         if data['text'][:3] == '【更新':
    #             continue
    #         else:
    #             content = cop.sub('', data['text'].strip())
    #             if len(content) <= 1 or len(content) >= 240:
    #                 continue
    #             print(content)
    #             s, a = get_topic_senti_att(content)
    #             if s<=3:
    #                 content = ''
    #             topic = test(content)
    #             pid, post_time, content, source = data['pid'], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(data['timestamp']))), content, 0
    #             title[pid] = [post_time, content, source, s, topic, page]
    #     post_ids = [item for item in title]

    #     print('********************************')
    #     for post_id in post_ids:
    #         reply_url = 'https://pkuhelper.pku.edu.cn/services/pkuhole/api.php?action=getcomment&pid=' \
    #                     + str(post_id) + '&PKUHelperAPI=3.0&jsapiver=200204234837-439282&' \
    #                                      'user_token=nb06ek1p9epw38y4sv9w59qkw2u2v1js'
    #         reply_page = json.loads(requests.get(reply_url, headers=headers).text)['data']
            
    #         title_content = {}
    #         title_content['post_id'], title_content['time'], title_content['content'], title_content['source'], title_content['senti'], title_content['topic'], title_content['process'], title_content['page'] = \
    #                         post_id, title[post_id][0], title[post_id][1], title[post_id][2], title[post_id][3], title[post_id][4], 0, title[post_id][5]
    #         insertHole(title_content, cursor, conn)
    #         print(title_content['content'])
            
    #         for reply in reply_page:
    #             reply_content = {}
    #             content = cop.sub('', reply['text'].strip())
    #             if len(content) > 240 or len(content) <= 1:
    #                 continue
    #             print(content)
    #             senti, att = get_topic_senti_att(content)
    #             topic = test(content)
    #             if senti <= 3:
    #                 content = ''
    #             reply_content['post_id'], reply_content['time'], reply_content[
    #                 'content'], reply_content['source'], reply_content['senti'], \
    #             reply_content['topic'], reply_content['process'], reply_content['page'] = \
    #                 reply['cid'], time.strftime("%Y-%m-%d %H:%M:%S",
    #                                                           time.localtime(int(reply['timestamp']))), \
    #                 content, 0, senti, topic, 0, page
                
    #             insertHole(reply_content, cursor, conn)
    #         print('********************************')
    #     # os._exit(0)
    #     page += 1
    # return res


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




def crawl():
    # get_bbs_cookie()
    # os._exit(0)
    with open('cookie.txt', 'r', encoding='utf-8') as f:
        cookie = f.read()
        cookies = json.loads(cookie)

    conn = sqlite3.connect('../../../db.sqlite3')
    cursor = conn.cursor()
    records = []

    # items_post = cursor.execute('''select post_id from system_post''')
    # for v in items_post:
    #     records.append(v[0])
    # items_reply = cursor.execute('''select reply_id from system_reply''')
    # for v in items_reply:
    #     records.append(v[0])

    bbs(cursor, conn, records, cookies)
    
    # hole(cursor, conn)
    
    # res['hole'] = hole(cursor, conn)
    # # res['bbs'] = bbs(cursor, conn)
    # return res


def save_data_to_excel():
    import pandas as pd
    from tqdm import tqdm
    conn = sqlite3.connect('../../../db.sqlite3')
    cursor = conn.cursor()
    items_reply = cursor.execute('''select content, topic from system_reply''')
    d = {'content':[], 'topic':[]}
    i = 0
    for v in items_reply:
        if i >= 50000:
            break
        print(i)
        d['content'].append(v[0])
        d['topic'].append(v[1])
        i += 1
    pd.DataFrame(d).to_excel('excel_output111.xls')



def insert_data_into_info():
    import pandas as pd
    conn = sqlite3.connect('../../../db.sqlite3')
    cursor = conn.cursor()
    source = r'C:\Users\king\Documents\code\data\labeled\excel_output2018_负向-已改.xls'
    df_2019 = pd.read_excel(source, sheet_name='2019整体')
    df_2020 = pd.read_excel(source, sheet_name='2020-1-4整体')

    year_data = df_2020
    all_time, all_senti, all_num = year_data['time'], year_data['senti'], year_data['num']
    for i, v in tqdm(enumerate(all_time)):
        y, m, d = int(v.split('-')[0]), int(v.split('-')[1]), int(v.split('-')[2])
        v = str(datetime(y, m, d, 0, 0, 0))
       
        try:
            time, senti_value, post_num = datetime.strptime(str(v), '%Y-%m-%d %H:%M:%S'), all_senti[i], int(all_num[i])
        except:
            continue
        
        data = {'time':time, 'senti_value':senti_value,'post_num':post_num}
        insert_data_sql = '''insert into system_info (time, senti_value, post_num) values (:time, :senti_value, :post_num)'''
        cursor.execute(insert_data_sql, data)
        conn.commit()



def re_label_data():
    conn = sqlite3.connect('../../../db.sqlite3')
    cursor = conn.cursor()
    all_data = cursor.execute('''select * from system_reply''').fetchall()
    for record in all_data:
        post_id, reply_id, content, time, senti, source, process, url = record[1], record[2], record[3], record[4], record[5], record[6], record[8], record[9]
        topic = test(content)
        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')

        data = {'post_id': post_id, 'reply_id':reply_id, 'content': content, 'time':time, 'topic':topic, 'process':process, 'url':url}
        if int(senti) == 6:
            insert_data_sql = '''insert into system_high_risk (post_id, reply_id, content, time, topic, process, url) values (:post_id, :reply_id, :content, :time, :topic, :process, :url)'''
            cursor.execute(insert_data_sql, data)
            conn.commit()
        

        y, m, d = time.year, time.month, time.day
        time_formater = datetime(y, m, d, 0, 0)
        search_sql = '''select * FROM system_info where time=?'''
        search_res = cursor.execute(search_sql, (time_formater,)).fetchall()

        love_num, others_num, psy_num, study_num, career_num =0, 0, 0, 0, 0
        if topic == '恋爱关系':
            love_num += 1
        elif topic == '其他':
            others_num += 1
        elif topic == '心理方面':
            psy_num += 1
        elif topic == '学业方面':
            study_num += 1
        else:
            career_num += 1
        senti_value = 3-senti if senti >= 4 else senti
        neg_senti_value = 0 if senti <= 3 else 3-senti
        
        data = {'time':time_formater, 'senti_value':senti_value, 'post_num':1, 'career_num':career_num, 'love_num':love_num,'others_num':others_num, 'psy_num':psy_num, 'study_num':study_num, 'neg_senti_value':neg_senti_value}

        if len(search_res) == 0:
            # print(time_formater, 'insert')
            insert_data_sql = '''insert into system_info (time, senti_value, post_num, career_num, love_num, others_num, psy_num, study_num, neg_senti_value) values (:time, :senti_value, :post_num, :career_num, :love_num, :others_num, :psy_num, :study_num, :neg_senti_value)'''
            cursor.execute(insert_data_sql, data)
        else:
            # print(time_formater, 'update')
            search_res = search_res[0]
            idx, time, senti_value, post_num, career_num, love_num, others_num, psy_num, study_num, neg_senti_value = search_res[0], search_res[1], search_res[2], search_res[3], search_res[4], search_res[5], search_res[6], search_res[7], search_res[8], search_res[9]
            update_sql = '''update system_info set senti_value=?, post_num=?, career_num=?, love_num=?,others_num=?, psy_num=?, study_num=?, neg_senti_value=? where time=?'''
            cursor.execute(update_sql, (data['senti_value']+senti_value, post_num+1, career_num+data['career_num'], love_num+data['love_num'], others_num+data['others_num'], psy_num+data['psy_num'], study_num+data['study_num'], neg_senti_value+data['neg_senti_value'], time))

        



def update_info():
    import jieba
    import pickle
    import jieba.posseg as peg
    stop = pickle.load(open('./data/stop.txt', 'rb'))
    conn = sqlite3.connect('../../../db.sqlite3')
    cursor = conn.cursor()
    all_data = cursor.execute('''select * from system_reply''').fetchall()
    for record in tqdm(all_data):
        content, time =record[3], record[4]
        # print(content)
        time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')      
        y, m, d = time.year, time.month, time.day
        time_formater = datetime(y, m, d, 0, 0)

        content_cut = list(jieba.cut(content))
        cut_result = ''
        for item in content_cut:
            if list(list(peg.cut(item))[0])[-1] != 'n' or item in stop:
                continue
            cut_result += item
        search_sql = '''select * FROM system_info where time=?'''
        search_res = cursor.execute(search_sql, (time_formater,)).fetchall()[0]
        key_words = search_res[-1]

        update_key_words = key_words+cut_result
        # print(update_key_words)
        update_sql = '''update system_info set key_words=? where time=?'''
        cursor.execute(update_sql, (update_key_words, time_formater))
        conn.commit()




def bbs_crawler():
    topic = {'secret':'414', 'bridge':'167', 'mental':'690', 'love':'36', 'school':'1431', 'not_mian':'251'}



if __name__ == '__main__':
    update_info()
