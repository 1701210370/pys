rom system.models import high_risk
    from system.models import info
    from system.models import new_reply

    start_time, end_time = datetime.combine(date.today() - timedelta(days=836),time.min).strftime('%Y-%m-%d %H:%M:%S'), datetime.combine(date.today(),time.max).strftime('%Y-%m-%d %H:%M:%S')
    all_post = json.loads(json.dumps(list(reply.objects.filter(Q(time__range=[start_time, end_time])).values()), cls=DjangoJSONEncoder))
    for item in all_post:
        cid, content, senti = item['reply_id'], item['content'], int(item['senti'])
        topic = test(content)
        item['topic'] = topic
        # print(content, senti, topic)
        reply.objects.filter(reply_id=cid).update(topic=topic)

        if senti == 6:
            high_risk.objects.create(post_id=item['post_id'], reply_id=cid, content=content, time=item['time'], process=item['process'], url=item['url'])

        senti = 3-senti if senti>=4 else senti

        post_time = item['time']
        print(post_time)
        day_time_format = datetime.strptime(post_time.split('T')[0], '%Y-%m-%d')
        day_record = info.objects.filter(time=day_time_format).values()
        if len(day_record) == 0:
            post_num, love_num, study_num, career_num, psy_num, others_num = 0, 0, 0, 0, 0, 0
            if topic == '恋爱关系':
                love_num = 1
            if topic == '学业方面':
                study_num = 1
            if topic == '职业发展':
                career_num = 1
            if topic == '心理方面':
                psy_num = 1
            if topic == '其他':
                others_num = 1
            info.objects.create(time=day_time_format, senti_value=senti, post_num=1,neg_senti_value=senti if senti<0 else 0, 
                psy_num=psy_num, study_num=study_num, career_num=career_num, love_num=love_num, others_num=others_num)
        else:
            record = day_record[0]
            senti_value, neg_senti_value, post_num, psy_num, study_num, career_num, love_num, others_num = record['senti_value'], record['neg_senti_value'], record['post_num'],record['psy_num'], record['study_num'], record['career_num'], record['love_num'], record['others_num']
            senti_value += senti
            post_num += 1
            if senti < 0:
                neg_senti_value += senti
            if topic == '恋爱关系':
                love_num += 1
            if topic == '学业方面':
                study_num += 1
            if topic == '职业发展':
                career_num += 1
            if topic == '心理方面':
                psy_num += 1
            if topic == '其他':
                others_num += 1
            info.objects.filter(time=day_time_format).update(senti_value=senti, neg_senti_value=neg_senti_value, post_num=post_num,psy_num=psy_num, study_num=study_num, career_num=career_num, love_num=love_num, others_num=others_num)
    # os._exit(0)

    print('finish')
    os._exit(0)