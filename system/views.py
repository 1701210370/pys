from django.shortcuts import render, render_to_response
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
import json
import re
import pandas as pd
import os
import numpy as np
from django.core.serializers.json import DjangoJSONEncoder

from datetime import date
from datetime import datetime
from datetime import time, timedelta
# import pkuseg
import jieba.analyse
import jieba.posseg as peg
import wordcloud
import matplotlib.pyplot as plt
from matplotlib.font_manager import _rebuild
_rebuild()
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
import warnings

warnings.filterwarnings('ignore')

# seg = pkuseg.pkuseg()
cop = re.compile("[^\u4e00-\u9fa5^.^,^，^a-z^A-Z^]")
labele_dict = {0:'恋爱关系', 1:'学业方面', 2:'职业发展', 3:'心理方面', 4:'其他'}


# from .tools.crawler import crawl


# Create your views here.


def home(request):
    return render_to_response('system/index.html')


def show_trend(request):
    return render_to_response('system/show_trend.html')

def login(request):
    from system.models import users
    print(request.POST)
    name, passwords = request.POST['title'], request.POST['password']
    user_info = users.objects.filter(name=name)
    if user_info.exists():
        return render_to_response('system/index.html')
    else:
        return render_to_response('system/login.html')



def home_welcome(request):
    return render_to_response('system/welcome1.html')


def get_data(request):
    pass

    

def form_trend_data(request):
    from system.models import info 
    start_time = datetime.strptime(request.GET['time1'], '%Y-%m-%d')
    end_time = datetime.strptime(request.GET['time2'], '%Y-%m-%d')

    # start_time = request.GET['time1']
    # end_time = request.GET['time2']

    print(start_time, end_time, type(start_time))
    
    time_range_data = info.objects.filter(Q(time__range=[start_time, end_time])).order_by('time').values()
    ret = {'trend_data':[], 'warning_data':[], 'topic_data': {'学业方面': 0, '心理方面':0, '职业发展':0, '恋爱关系': 0, '其他': 0}}
    previous_senti = []
    for i, record in enumerate(time_range_data):
        #1. 获取当天总体情感值
        senti_value = int(record['senti_value'])
        ret['trend_data'].append(
                {'value': [
                    record['time'].strftime('%Y-%m-%d'),
                    senti_value
                ]}
        )

        previous_senti.append(senti_value)
        # 2.标记当天是否预警
        if i > 3:
            prev_days_senti = previous_senti[i-3:i]
            if previous_senti[i] < np.min(prev_days_senti)*(1+0.6) and previous_senti[i]<-400:
                ret['warning_data'].append({'xAxis':record['time'].strftime('%Y-%m-%d'),'yAxis':senti_value,'value':'预警'})

        #3. 统计当天话题分布
        psy_num, love_num, study_num, career_num, others_num = record['psy_num'], record['love_num'], record['study_num'], record['career_num'], record['others_num']
        ret['topic_data']['学业方面'] = ret['topic_data']['学业方面'] + study_num
        ret['topic_data']['心理方面'] = ret['topic_data']['心理方面'] + psy_num
        ret['topic_data']['职业发展'] = ret['topic_data']['职业发展'] + career_num
        ret['topic_data']['恋爱关系'] = ret['topic_data']['恋爱关系'] + love_num
        ret['topic_data']['其他'] = ret['topic_data']['其他'] + others_num
    return JsonResponse(ret, safe=False)



#去数据库中获取默认情况下的心理健康趋势数据和主题分布数据
def default_trend_data(request):
    from system.models import info 
    cur_year = datetime.now().year  #获取当前的年份日期
    start_time, end_time = datetime(cur_year, 1, 1, 0, 0), datetime.now()  #默认取今年年初到当前时间的数据
    time_range_data = info.objects.filter(Q(time__range=[start_time, end_time])).order_by('time').values()
    #返回给前端的数据有三类，刚开始都是0
    ret = {'trend_data':[], 'warning_data':[], 'topic_data': {'学业方面': 0, '心理方面':0, '职业发展':0, '恋爱关系': 0, '其他': 0}}
    previous_senti = []
    for i, record in enumerate(time_range_data):
        #1. 获取当天总体情感值
        senti_value = int(record['senti_value'])
        ret['trend_data'].append(
                {'value': [
                    record['time'].strftime('%Y-%m-%d'),  #日期
                    senti_value                           #心理健康值
                ]}
        )

        previous_senti.append(senti_value)
        # 2.标记当天是否预警
        if i > 3:
            prev_days_senti = previous_senti[i-3:i] #获取前三天的心理健康值
            if previous_senti[i] <= -400 and previous_senti[i] < np.min(prev_days_senti)*(1+0.6):
                ret['warning_data'].append({'xAxis':record['time'].strftime('%Y-%m-%d'),'yAxis':senti_value,'value':'预警'})

        #3. 统计当天话题分布
        psy_num, love_num, study_num, career_num, others_num = record['psy_num'], record['love_num'], record['study_num'], record['career_num'], record['others_num']
        ret['topic_data']['学业方面'] = ret['topic_data']['学业方面'] + study_num
        ret['topic_data']['心理方面'] = ret['topic_data']['心理方面'] + psy_num
        ret['topic_data']['职业发展'] = ret['topic_data']['职业发展'] + career_num
        ret['topic_data']['恋爱关系'] = ret['topic_data']['恋爱关系'] + love_num
        ret['topic_data']['其他'] = ret['topic_data']['其他'] + others_num

    return JsonResponse(ret, safe=False)
    # os._exit(0)


#默认的关键词词云展示和指定范围内的词云图
def gen_wordcloud_pic(request):
    from system.models import info
    font ='/Applications/anaconda3/lib/python3.7/site-packages/matplotlib/mpl-data/fonts/ttf/SimHei.ttf'
    time1, time2 = request.GET['time1'], request.GET['time2']
    if request.GET['time2'] == '1':       #默认展示一周的关键词
        cur_year = datetime.now().year
        end_time = datetime.now() 

        monday = date.today()
        one_day = timedelta(days=1)
        while monday.weekday()!=0:
            monday -= one_day
        
        start_time = monday
    else:
        start_time = datetime.strptime(time1, '%Y-%m-%d')
        end_time = datetime.strptime(time2, '%Y-%m-%d')
    time_range_data = info.objects.filter(Q(time__range=[start_time, end_time])).values()
    sentences = ''
    cloud_record = {}
    for record in time_range_data:
        sentences += record['key_words']+'\n'      #sentences是所有候选关键词的集合（已去除停用词，留下的都是名词）

    keywords = jieba.analyse.extract_tags(sentences, topK=200, withWeight=True, allowPOS=()) #通过jieba工具获取真正的关键词

    for item in keywords:   #通过jieba工具后得到的关键词，第一项是词语，第二项是词语的TF-IDF值
        print(item[0])
        if item[0] in ['楼主','男生','女生','有点','时候','感觉','贵校','帖子','父母','同学','未名站']:
            continue
        cloud_record[item[0]] = 10000*item[1]   #把IF-DIF值放大
    wc = wordcloud.WordCloud(
        max_words=50,  # 最多显示词数
        max_font_size=100,  # 字体最大值
        font_path=font,
        background_color='white'
    )

    # generate_from_frequencies（）方法默认是根据词频来决定关键词的大小，这里用词语的TF-IDF值来代替词频
    wc.generate_from_frequencies(cloud_record)
    plt.imshow(wc)  # 显示词云
    plt.axis('off')

    import random
    num = random.randint(1, 50)
    save_path = './system/static/images/test'+str(num)+'.jpg'
    plt.savefig(save_path)     #存储词云图片

    img_path = '../..'+save_path[8:]
    print(img_path)

    return JsonResponse({'src':img_path}, safe=False)    #返回给前端词云图的地址



def get_topic_data(request):
    from system.models import info

    start_time = request.POST['time']
    year, month, day = int(start_time.split('-')[0]), int(start_time.split('-')[1]), int(start_time.split('-')[2])
    start = datetime(year, month, day)
    
    one_day_data = info.objects.filter(Q(time=start))
    one_day_data = json.loads(json.dumps(list(one_day_data.values()), cls=DjangoJSONEncoder))[0]

    ret = {'学业方面': 0, '心理方面': 0, '职业发展': 0, '恋爱关系': 0, '其他': 0}
    ret['学业方面'], ret['心理方面'], ret['职业发展'], ret['恋爱关系'] = one_day_data['study_num'], one_day_data['psy_num'], one_day_data['career_num'], one_day_data['love_num']
    ret_str = ''
    for topic in ret:
        ret_str = ret_str + topic+ ':' + str(ret[topic])+' '

    return JsonResponse({'data': ret_str})


def highlight(word, attn):
    html_color = '#%02X%02X%02X' % (255, int(255 * (1 - attn)), int(255 * (1 - attn)))
    return '<span style="background-color: {}">{}</span>'.format(html_color, word)


def make_process_status(process):
    return '<i class="layui-icon layui-icon-circle-dot" style="font-size: 20px; color: #FF6600;"></i>' if not process else '<i class="layui-icon layui-icon-ok-circle" style="font-size: 20px; color: #3CC457;"></i>'


def mark_process(request):
    # pid = request.POST['pid']
    cid = request.POST['cid']
    from system.models import high_risk
    high_risk.objects.filter(reply_id=cid).update(process=1)
    print('ok')
    return JsonResponse({'code':'ok'})



def del_error(request):
    cid = request.GET['cid']
    from system.models import high_risk
    high_risk.objects.filter(reply_id=cid).delete()
    return JsonResponse({'status':'success'})


def show_data(request):
    from system.models import high_risk

    page, limit = int(request.GET['page']), int(request.GET['limit'])

    start_time, end_time = datetime.combine(date.today() - timedelta(days=7),time.min).strftime('%Y-%m-%d %H:%M:%S'), datetime.combine(date.today() - timedelta(days=1),time.max).strftime('%Y-%m-%d %H:%M:%S')
    all_post = json.loads(json.dumps(list(high_risk.objects.filter(Q(time__range=[start_time, end_time])).order_by("-time").values()), cls=DjangoJSONEncoder))
    return_data = []

    cloud_word = {}
    for item in all_post:        
        pid, cid, process, mark_data, url = item['post_id'], item['reply_id'], make_process_status(item['process']), item['content'], make_url(item['url'])
        return_data.append({
            'cid': cid,
            'text': mark_data,
            'url': url,
            'process': process
        })

    page_data = return_data[(page-1)*limit:page*limit]
    return JsonResponse(
        {"code": 0, "msg": "", "count": len(return_data), "data": page_data}
    )

def make_url(url):
    return '<a href="{}">{}</a>'.format(url, url)
