#预警功能
from threading import Timer
import os
import sqlite3
import pandas as pd
import numpy as np
import datetime 
import jieba.analyse



def monitor(ratio):
	conn = sqlite3.connect('../../../db.sqlite3')
	cursor = conn.cursor()
	today = datetime.datetime.now()
	last_five_day = today-datetime.timedelta(days=4)
	search_sql = '''select * FROM system_info where time>=? and time<=?'''   #去信息表中获取前三天的心理健康值
	search_res = cursor.execute(search_sql, (last_five_day,today)).fetchall()

	senti = []
	for record in search_res:
		senti.append(record[2])
	if senti[-1] <= -400 and senti[-1] < np.mean(senti[:-1])*(1+ratio):
		send_email()
	else:
		print('暂时没有危机风险')

def main():
	monitor(0.6)
	t = Timer(60, main)  # 间隔一分钟检查一次
	t.start()
	# send_email()

#发送预警邮件
def send_email():
	import smtplib     #与发送邮件相关的包
	from email.mime.text import MIMEText
	from email.header import Header

	conn = sqlite3.connect('../../../db.sqlite3')
	cursor = conn.cursor()
	today = datetime.datetime.now()
	last_day = today-datetime.timedelta(days=2)
	# print(last_day, today)
	search_sql = '''select * FROM system_info where time>=? and time<=?'''
	search_res = cursor.execute(search_sql, (last_day,today)).fetchall() #获取当天和前一天的数据

	analysis_text = ''
	career,love, others,psy,study=0,0,0,0,0
	for record in search_res:
		print(record)
		analysis_text+=record[-1]   #累加候选关键词
		career += record[4]
		love += record[5]
		others += record[6]
		psy += record[7]
		study += record[8]

	keywords = jieba.analyse.extract_tags(analysis_text, topK=100, withWeight=True, allowPOS=())
	keywords_text = ''
	for item in keywords:
		print(item[0])
		if item[0] in ['楼主','男生','女生','有点','时候','感觉','贵校','帖子','父母','同学']:
			continue
		keywords_text += item[0]
		keywords_text += ','
	
	send_text = '尊敬的心理健康中心的老师:\n您好！\n系统监测到{}，校园心理健康到达危机预警值。\n具体相关主题分布为：职业发展相关：{}，恋爱关系：{}，心理方面:{},学业方面:{}\n相关主题词为：\n{}'.format(str(today), career, love, psy, study,keywords_text)

	mail_host="mail.pku.edu.cn"  #设置服务器
	mail_user="1701210366@pku.edu.cn"    #用户名
	mail_pass="wangchao1995"   #口令 
	 
	sender = '1701210366@pku.edu.cn'
	receivers = ['1701210370@pku.edu.cn']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
	 
	# 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
	message = MIMEText(send_text, 'plain', 'utf-8')
	message['From'] = Header("高校心理健康监测模块", 'utf-8')   # 发送者
	message['To'] =  Header("工作人员", 'utf-8')        # 接收者
	 
	subject = '学生心理健康预警信息'
	message['Subject'] = Header(subject, 'utf-8')
	 
	 
	try:
	    smtpObj = smtplib.SMTP()
	    print('ok')
	    smtpObj.connect(mail_host, 25)

	    smtpObj.login(mail_user,mail_pass)  
	    print('ok')
	    smtpObj.sendmail(sender, receivers, message.as_string())
	    print("邮件发送成功")
	except smtplib.SMTPException:
	    print("Error: 无法发送邮件")



if __name__ == '__main__':
	main()

