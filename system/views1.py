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
            if previous_senti[i] < np.mean(prev_days_senti)*(1+0.6):
                ret['warning_data'].append({'xAxis':record['time'].strftime('%Y-%m-%d'),'yAxis':senti_value,'value':'预警'})

        #3. 统计当天话题分布
        psy_num, love_num, study_num, career_num, others_num = record['psy_num'], record['love_num'], record['study_num'], record['career_num'], record['others_num']
        ret['topic_data']['学业方面'] = ret['topic_data']['学业方面'] + study_num
        ret['topic_data']['心理方面'] = ret['topic_data']['心理方面'] + psy_num
        ret['topic_data']['职业发展'] = ret['topic_data']['职业发展'] + career_num
        ret['topic_data']['恋爱关系'] = ret['topic_data']['恋爱关系'] + love_num
        ret['topic_data']['其他'] = ret['topic_data']['其他'] + others_num
    return JsonResponse(ret, safe=False)



    
def default_trend_data(request):
    from system.models import info 
    cur_year = datetime.now().year
    start_time, end_time = datetime(cur_year, 1, 1, 0, 0), datetime.now()     
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
        if i > 5:
            prev_days_senti = previous_senti[i-5:i]
            if previous_senti[i] <= -400 and previous_senti[i] < np.mean(prev_days_senti)*(1+0.8):
                ret['warning_data'].append({'xAxis':record['time'].strftime('%Y-%m-%d'),'yAxis':senti_value,'value':'预警'})

        #3. 统计当天话题分布
        psy_num, love_num, study_num, career_num, others_num = record['psy_num'], record['love_num'], record['study_num'], record['career_num'], record['others_num']
        ret['topic_data']['学业方面'] = ret['topic_data']['学业方面'] + study_num
        ret['topic_data']['心理方面'] = ret['topic_data']['心理方面'] + psy_num
        ret['topic_data']['职业发展'] = ret['topic_data']['职业发展'] + career_num
        ret['topic_data']['恋爱关系'] = ret['topic_data']['恋爱关系'] + love_num
        ret['topic_data']['其他'] = ret['topic_data']['其他'] + others_num

    # return render(request, 'system/sh.html', {
    #     'topic': ret['topic_data'],
    #     'trend': ret['trend_data']
    # })

    return JsonResponse(ret, safe=False)
    # os._exit(0)



#关键词提取
def gen_wordcloud_pic(request):
    from system.models import info
    font = '/Applications/anaconda3/lib/python3.7/site-packages/matplotlib/mpl-data/fonts/ttf/SimHei.ttf'
    time1, time2 = request.GET['time1'], request.GET['time2']
    if request.GET['time2'] == '1':
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
        sentences += record['key_words']+'\n'

    keywords = jieba.analyse.extract_tags(sentences, topK=200, withWeight=True, allowPOS=())
    print(keywords)

    for item in keywords:
        print(item[0])
        if item[0] in ['楼主','男生','女生','有点','时候','感觉','贵校','帖子','父母','同学']:
            continue
        # words = peg.cut(item[0])
        # for word, flag in words:
        #     if flag[0]!='n':
        #         continue
        #     else:
        cloud_record[item[0]] = 10000*item[1]
    wc = wordcloud.WordCloud(
        max_words=50,  # 最多显示词数
        max_font_size=100,  # 字体最大值
        font_path=font,
        background_color='white'
    )

    wc.generate_from_frequencies(cloud_record)
    plt.imshow(wc)  # 显示词云
    plt.axis('off')
    save_path = './system/static/images/test1.jpg'
    plt.savefig(save_path)

    return JsonResponse({'src':save_path}, safe=False)




def get_topic_data(request):
    start_time = request.POST['time']
    year, month, day = int(start_time.split('-')[0]), int(start_time.split('-')[1]), int(start_time.split('-')[2])
    start, end = datetime(year, month, day),  datetime(year, month, day+1)
    from system.models import reply
    one_day_data = reply.objects.filter(Q(time__range=[start, end]) & Q(senti__range=[4, 6]))
    one_day_data = json.loads(json.dumps(list(one_day_data.values()), cls=DjangoJSONEncoder))

    ret = {'学业方面': 0, '心理方面': 0, '职业发展': 0, '恋爱关系': 0, '其他': 0}
    for item in one_day_data:
        ret[item['topic']] += 1
    ret_str = ''
    for topic in ret:
        ret_str = ret_str + topic+ ':' + str(ret[topic])+' '

    return JsonResponse({'data': ret_str})
    # end_time = end_time


def get_full_topic_data(request):
    from system.models import reply
    start_time, end_time = datetime.strptime("2020-1-01 00:00:00", "%Y-%m-%d %H:%M:%S"), datetime.strptime("2020-3-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    time_range_data = reply.objects.filter(Q(time__range=[start_time, end_time]))
    time_range_data = json.loads(json.dumps(list(time_range_data.values()), cls=DjangoJSONEncoder))
    topic_res = topic_info(time_range_data)
    print(topic_res)
    return JsonResponse(topic_res, safe=False)



def highlight(word, attn):
    html_color = '#%02X%02X%02X' % (255, int(255 * (1 - attn)), int(255 * (1 - attn)))
    return '<span style="background-color: {}">{}</span>'.format(html_color, word)


def make_url(url):
    return '<a href="{}">{}</a>'.format(url, url)

def make_process_status(process):
    return '<i class="layui-icon layui-icon-circle-dot" style="font-size: 20px; color: #FF6600;"></i>' if not process else '<i class="layui-icon layui-icon-ok-circle" style="font-size: 20px; color: #3CC457;"></i>'


def mk_html(seq, attns):
    html = ""
    for ix, attn in zip(seq, attns):
        html += ' ' + highlight(
            ix,
            attn
        )
    return html + "<br>"

#更改高危个体文本的处理状态
def mark_process(request):
    cid = request.POST['cid']         #获取已处理的文本的ID
    from system.models import high_risk
    high_risk.objects.filter(reply_id=cid).update(process=1)  #将数据库high_risk表中的已处理的文本的处理状态改为1
    print('ok')
    return JsonResponse({'code':'ok'})


#删除高危个体
def del_error(request):
    cid = request.GET['cid']
    from system.models import high_risk
    high_risk.objects.filter(reply_id=cid).delete()
    return JsonResponse({'status':'success'})


#show_data()函数去数据库中获取高危个体的数据
def show_data(request):
    from system.models import high_risk    #使用system.models组件（Djago提供）链接数据库中的high_risk表

    page, limit = int(request.GET['page']), int(request.GET['limit']) #点击了哪一页，一页要显示多少条数据，默认显示30条
    monday = date.today()
    one_day = timedelta(days=1)    #timedelta时间跨度为1天
    while monday.weekday() != 0:   #weekday()表示今天是本周的第几天
        monday -= one_day
    start_time = monday
    end_time =  datetime.combine(date.today() - timedelta(days=1),time.max).strftime('%Y-%m-%d %H:%M:%S')  #获取当天当前时刻的时间
    #获取指定时间段内的高危个体信息，并按照时间从大到小进行排序
    all_post = json.loads(json.dumps(list(high_risk.objects.filter(Q(time__range=[start_time, end_time])).order_by("-time").values()), cls=DjangoJSONEncoder))
    return_data = []

    for item in all_post:        
        pid, cid, process, mark_data, url = item['post_id'], item['reply_id'], make_process_status(item['process']), item['content'], make_url(item['url'])
        return_data.append({
            'cid': cid,
            'text': mark_data,
            'url': url,
            'process': process
        })

    page_data = return_data[(page-1)*limit:page*limit] #每一页进行展示的数据范围

    return JsonResponse(              #给前端返回数据
        {"code": 0, "msg": "", "count": len(return_data), "data": page_data}
    )


def get_form(request):
    from system.models import reply
    topic = request.POST.get('topic')
    intensity = request.POST.get('intensity')
    polarity = request.POST.get('polarity')
    source = request.POST.get('source')
    start_time = datetime.strptime(request.POST.get('start_time'), '%Y-%m-%d')
    end_time = datetime.strptime(request.POST.get('end_time'), '%Y-%m-%d')
    print(topic, intensity, polarity, source, start_time, end_time)

    polarity_time_range_data = [
        reply.objects.filter(Q(time__range=[start_time, end_time]) & Q(senti=0)),
        reply.objects.filter(Q(time__range=[start_time, end_time]) & Q(senti__range=[1, 3])),
        reply.objects.filter(Q(time__range=[start_time, end_time]) & Q(senti__range=[4, 6])),
    ]

    intensity_time_range_data = [
        reply.objects.filter(
            Q(time__range=[start_time, end_time]) & (Q(senti=1) | Q(senti=4))),
        reply.objects.filter(
            Q(time__range=[start_time, end_time]) & (Q(senti=2) | Q(senti=5))),
        reply.objects.filter(
            Q(time__range=[start_time, end_time]) & (Q(senti=3) | Q(senti=6))),
    ]

    time_range_data = reply.objects.filter(Q(time__range=[start_time, end_time]))
    time_range_data = json.loads(json.dumps(list(time_range_data.values()), cls=DjangoJSONEncoder))

    topic_res = topic_info(time_range_data)
    polarity_data = polarity_info(polarity_time_range_data, start_time, end_time)
    intensity_data = polarity_info(intensity_time_range_data, start_time, end_time)
    # show_word_cloud()

    return render(request, 'system/welcome.html', {
        'topic_data': topic_res,
        'intensity_cnt': [sum([item['value'][1] for item in intensity_data[0]]), 
                          sum([item['value'][1] for item in intensity_data[1]]), 
                          sum([item['value'][1] for item in intensity_data[2]])],
        'neutral': polarity_data[0],
        'positive': polarity_data[1],
        'negative': polarity_data[2],
        'low': intensity_data[0],
        'mid': intensity_data[1],
        'high': intensity_data[2],
    })


def polarity_info(data, start, end):
    ret = []
    import datetime, os
    for i, item in enumerate(data):
        time_data = []
        for i in range((end - start).days + 1):
            day, end_day = start + datetime.timedelta(days=i), start + datetime.timedelta(days=i + 1)
            day_data = item.filter(Q(time__range=[day, end_day]))
            time_data.append(
                {'value': [
                    day.strftime('%Y-%m-%d'),
                    len(day_data)
                ]}
            )
        ret.append(time_data)
    return ret


def topic_info(data):
    topic_res = {'学业方面': 0, '心理方面':0, '职业发展':0, '恋爱关系': 0, '其他': 25620}
    for record in data:
        if record['topic'] == '-1':
            continue
        else:
            topic_res[record['topic']] += 1
    # topic_res = [v // 10 for v in topic_res]
    return topic_res

