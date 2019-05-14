#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib2
import re
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

corp_id = "ww5e2b73cf090191a9"
agent_id = "1000002"
secret = "4PT63xZksOFe7Si087pRVaHEwLKLAV2GTgLCoetzf0c"

wen = {'red': [7,12,16,21,27,31], 'blue': '13'}
yue = {'red': [3,7,8,16,18,29], 'blue': '6'}
chen = {'red': [6,7,9,18,19,27], 'blue': '7'}
peng = {'red': [4,12,19,26,28,31], 'blue': '5'}
jian = {'red': [2,9,16,20,21,31], 'blue': '11'}

duliu = {'red': [1,3,5,8,22,23], 'blue': '14'}
shisan = {'red': [8,10,20,21,22,23], 'blue': '9'}
fan = {'red': [4,7,11,13,16,25], 'blue': '1'}
yong = {'red': [8,18,19,25,29,30], 'blue': '3'}
wen2 = {'red': [1,7,8,9,17,23], 'blue': '10'}

team_one = {"wen": wen, "yue": yue, "chen": chen, "peng": peng, "jian": jian}
team_two = {"duliu": duliu, "shisan": shisan, "fan": fan, "yong": yong, 'wen2': wen2}
#teams = {"team_one": team_one, "team_two": team_two}

index_team_one = {"wen": "八戒", "yue": "月月", "chen": "刘晨", "peng": "人生", "jian": "坚哥哥"}
index_team_two = {"duliu": "毒瘤", "shisan": "十三", "fan": "33", "yong": "阿诗", "wen2": "八戒"}

def get_token():
	get_token_url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s" % (corp_id,secret)
	request = urllib2.Request(get_token_url)
	try:
		result = urllib2.urlopen(request)
		response = json.loads(result.read())
		token = response['access_token']
	except Exception as e:
		print e
	return token

def get_ssq_result():
	ssq_query_url = "http://www.cwl.gov.cn/cwl_admin/kjxx/findDrawNotice?name=ssq&issueCount=30"
	
	request = urllib2.Request(ssq_query_url)
	request.add_header('Referer','http://www.cwl.gov.cn/kjxx/ssq/kjgg/')
	
	try:
		result = urllib2.urlopen(request)
		response = json.loads(result.read())
		
		latest = response["result"][0]
		open_date = latest["date"]
		code = latest["code"]
		red_num = latest["red"]
		blue_num = latest["blue"]
		first_prize = latest["prizegrades"][0]["typemoney"]
		second_prize = latest["prizegrades"][1]["typemoney"]
	except Exception as e:
		print e
	
	return open_date,code,red_num,blue_num,first_prize,second_prize

def calcucate():
	open_date,code,red_num,blue_num,first_prize,second_prize = get_ssq_result()
	
	first_prize = int(first_prize)
	second_prize = int(second_prize)
	third_prize = 3000
	fourth_prize = 200
	fifth_prize = 10
	sixth_prize = 5
	red_num = red_num.split(',')
	red_num = map(int,red_num)
	
	award_one = 0
	awards_one = []
	winners_one = []
	
	for winner in team_one:
		r_red = team_one[winner]['red']
		r_blue = team_one[winner]['blue']
		check = list(set(r_red).intersection(set(red_num)))
		right_red_num = len(check)
		if r_blue == blue_num:
			if right_red_num == 3:
				awards_one.append(fifth_prize)
				winners_one.append(winner)
			elif right_red_num == 4:
				awards_one.append(fourth_prize)
				winners_one.append(winner)
			elif right_red_num == 5:
				awards_one.append(third_prize)
				winners_one.append(winner)
			elif right_red_num == 6:
				awards_one.append(first_prize)
				winners_one.append(winner)
			else:
				awards_one.append(sixth_prize)
				winners_one.append(winner)
		else:
			if right_red_num == 4:
				awards.append(fifth_prize)
				winners.append(winner)
			elif right_red_num == 5:
				awards.append(fourth_prize)
				winners.append(winner)
			elif right_red_num == 6:
				awards.append(second_prize)
				winners.append(winner)
		
	for i in awards_one:
		award_one = award_one + i
			
	award_two = 0
	awards_two = []
	winners_two = []
	
	for winner in team_two:
		r_red = team_two[winner]['red']
		r_blue = team_two[winner]['blue']
		check = list(set(r_red).intersection(set(red_num)))
		right_red_num = len(check)
		if r_blue == blue_num:
			if right_red_num == 3:
				awards_two.append(fifth_prize)
				winners_two.append(winner)
			elif right_red_num == 4:
				awards_two.append(fourth_prize)
				winners_two.append(winner)
			elif right_red_num == 5:
				awards_two.append(third_prize)
				winners_two.append(winner)
			elif right_red_num == 6:
				awards_two.append(first_prize)
				winners_two.append(winner)
			else:
				awards_two.append(sixth_prize)
				winners_two.append(winner)
		else:
			if right_red_num == 4:
				awards_two.append(fifth_prize)
				winners_two.append(winner)
			elif right_red_num == 5:
				awards_two.append(fourth_prize)
				winners_two.append(winner)
			elif right_red_num == 6:
				awards_two.append(second_prize)
				winners_two.append(winner)

	for i in awards_two:
		award_two = award_two + i		

	return award_one,award_two,winners_one,winners_two

def send_to_wechat():
	token = get_token()
	open_date,code,red_num,blue_num,first_prize,second_prize = get_ssq_result()
	award_one,award_two,winners_one,winners_two = calcucate()
	header = {"Content-type": "application/json", "charset": "utf-8"}
	
	user_one = ""
	user_two = ""
	if winners_one:
		for user in winners_one:
			user_one = index_team_one[user] + "," + user_one	
	else:
		user_one = "无"
		
	if winners_two:
		for user in winners_two:
			user_two = index_team_two[user] + "," + user_two
	else:
		user_two = '无'
	
	to_user = '@all'
	messages = """开奖日期: %s,
开奖期号:  %s,
红球编号:  %s,
蓝球编号:  %s,
本期一等奖奖金:  %s,
本期二等奖奖金:  %s,
一号小分队奖金: %s 元,
二号小分队奖金: %s 元,
一号小分队中奖者: %s
二号小分队中奖者: %s""" % (open_date,code,red_num,blue_num,first_prize,second_prize,award_one,award_two,user_one,user_two)
	send_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s" % (token)
	
	data = json.dumps(
		{
		"touser": to_user,
		"msgtype": "text",
		"agentid": agent_id,
		"text": {
			"content": messages
		},
		"safe": 0	
	})

	request = urllib2.Request(send_url,data)
	for key in header:
		request.add_header(key,header[key])
	try:
		result = urllib2.urlopen(request)
		response = json.loads(result.read())
		print response
	except Exception as e:
		print e

def main():
	send_to_wechat()
		
if __name__ == '__main__':
	main()