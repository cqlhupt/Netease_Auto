#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests, json, re, os
from user import User
from wecom import WeComtAlert


def start():
    with open('./config.json','r',encoding='utf-8') as f:
        config = json.loads(re.sub(r'\/\*[\s\S]*?\/', '', f.read()))
    setting = config['setting']
    
    user_count = 0

    SCKEYs = {}
    Skeys = {}

    for user_config in config['users']:
        user_count += 1
        
        user_setting = setting
        if "setting" in user_config:
            for key in user_config['setting']:
                user_setting[key] = user_config['setting'][key]

        user = User()
        #user.setUser(username=user_config['username'], password=user_config['password'],isMd5=user_config['md5'],user_setting=user_setting,No=user_count)  
        user.setUser(username=os.getenv('ACCOUNT'), password=os.getenv('PASSWORD'),isMd5=user_config['md5'],user_setting=user_setting,No=user_count)
        if user.isLogined:  
            user.userInfo()   

            if user_setting['follow']:
                user.follow() 

            if user_setting['sign']:
                user.sign()
            if user.userType == 4:
                user.musician_task()                       

            task_on = False
            tasks = user_setting['yunbei_task']
            for task in user_setting['yunbei_task']:
                task_on = task_on or tasks[task]['on']
            if task_on:
                user.yunbei_task() 

            user.get_yunbei()    

            if user_setting['daka']['on']:
                user.daka()

            if user_setting['other']['play_playlists']['on']:
                user.play_playlists()                   

        user.msg = user.msg.strip()
        #sckey = user_setting['serverChan']['SCKEY']
        sckey = os.getenv('PUSH_KEY')
        if user_setting['serverChan']['on'] and sckey != '':
            if sckey in SCKEYs:                
                SCKEYs[sckey]['msg'] += user.msg
            else:
                SCKEYs[sckey] = {'title': user.title, 'msg': user.msg}

        skey = user_setting['CoolPush']['Skey']
        if user_setting['CoolPush']['on'] and skey != '':
            if skey in Skeys:
                Skeys[skey]['msg'] += user.msg
            else:
                Skeys[skey] = {'title': user.title, 'method': user_setting['CoolPush']['method'], 'msg': user.msg}

        if user_setting['WeCom']['on'] and user_setting['WeCom']['corpid'] != "" and user_setting['WeCom']['secret'] != "" and user_setting['WeCom']['agentid'] != "":
            alert = WeComtAlert(user_setting['WeCom']['corpid'],user_setting['WeCom']['secret'],user_setting['WeCom']['agentid'])
            alert.send_msg(user_setting['WeCom']['userid'],user_setting['WeCom']['msgtype'],user.msg,"网易云音乐打卡",'https://music.163.com/#/user/home?id='+str(user.uid))


    for sckey in SCKEYs:
        serverChan_url = 'http://sc.ftqq.com/'+sckey+'.send'
        requests.post(serverChan_url, data={"text": SCKEYs[sckey]['title'], "desp": SCKEYs[sckey]['msg']})

    for skey in Skeys:
        for method in Skeys[skey]['method']:
            CoolPush_url = "https://push.xuthus.cc/{}/{}".format(method, skey)
            if method == "email":
                requests.post(CoolPush_url, data={"t":Skeys[skey]['title'] , "c": Skeys[skey]['msg']})
            else:
                requests.get(CoolPush_url, params={"c": Skeys[skey]['msg']})

def main_handler(event, context):
    return start()

if __name__ == '__main__':
    start()
