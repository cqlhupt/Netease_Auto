#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests, json, time, random, math, re, datetime
from hashlib import md5
from api import NetEase

class User(object):
    def __init__(self):
        self.music = None
        self.user_setting = {}
        self.title = '网易云音乐'
        self.msg = ''
        self.isLogined = False
        self.No = 0
        self.nickname = ''
        self.uid = 0
        self.userType = 0
        self.level = 0
        self.full = False
        self.full_level = 10
        self.songFull = False
        self.listenSongs = 0
        self.vipType = 0


    def setUser(self, username, password, isMd5=False, user_setting={}, No=0):
        # self.music = NetEase(username)
        # if not isMd5:
        #     password = self.getMd5(password)
        self.music = self.login_check(username, password, isMd5)
        # login_resp = self.music.login(username, password)
        self.taskUser(No)
        if self.music.uid != 0:
            self.isLogined = True
            self.user_setting = user_setting
            self.uid = self.music.uid
            self.userType = self.music.userType
        else:
            self.title += ': 登录失败,请检查账号、密码'
            self.taskTitle('用户信息')
            self.taskInfo('登录失败，请检查账号、密码')
            self.finishTask()
        

    def login_check(self, username, pwd='', is_md5=True):
        music = NetEase(username)
        resp = music.user_level()
        if resp['code'] == 200:
            music.uid = resp['data']['userId']
            user_resp = music.user_detail(music.uid)
            music.nickname = user_resp['profile']['nickname']
            music.userType = user_resp['profile']['userType']
        else:
            if not is_md5:
                pwd = md5(pwd.encode(encoding='UTF-8')).hexdigest()
            login_resp = music.login(username,pwd)
            if login_resp['code'] == 200:
                music.uid = login_resp['profile']['userId']
                music.nickname = login_resp['profile']['nickname']
                music.userType = login_resp['profile']['userType']
            else:
                music.uid = 0
                music.nickname = ''
        return music           

    # def getMd5(self, str):
    #     return hashlib.md5(str.encode(encoding='UTF-8')).hexdigest()

    def taskUser(self, No):
        self.msg += '### 用户' + str(No) + '\n'
        #print('### 用户' + str(No))
    def taskTitle(self, title):
        self.msg += '#### ' + title + '\n'
        #print('#### ' + title)
    def taskInfo(self, key, value=''):
        if value == '':
            self.msg += '- ' + str(key) + '\n'
            #print('- ' + str(key))
        else:
            self.msg += '- ' + str(key) + ': ' + str(value) + '\n'            
            #print('- ' + str(key) + ': ' + str(value))
    def finishTask(self):
        self.msg += '\n'
        print()
    
    def userInfo(self):
        resp = self.music.user_detail(self.uid)
        self.level = resp['level']
        self.vipType = resp['profile']['vipType']
        self.listenSongs = resp['listenSongs']
        self.taskTitle('用户信息')
        self.taskInfo('用户名称', resp['profile']['nickname'])
        self.taskInfo('用户ID', self.uid)
        self.taskInfo('用户等级', resp['level'])
        self.taskInfo('用户村龄', str(resp['createDays']) + '天')
        self.taskInfo('云贝数量', resp['userPoint']['balance'])
        self.taskInfo('粉丝数量', resp['profile']['followeds'])
        self.taskInfo('听歌总数', self.listenSongs)
                   
        resp = self.music.user_level()
        self.full=resp['full']
        if not self.full:
            self.taskInfo('距离下级还需播放', str(resp['data']['nextPlayCount'] - resp['data']['nowPlayCount']) + '首歌')
            self.taskInfo('登录天数', resp['data']['nowLoginCount'])
            self.taskInfo('距离下级还需登录', str(resp['data']['nextLoginCount'] - resp['data']['nowLoginCount']) + '天')
            # if resp['data']['progress'] > 0:                
            #     full_level = round(resp['data']['level'] / resp['data']['progress'])
            #     # 判断是否只差登录天数就满级
            #     if (full_level-resp['data']['level']) == 1 and (resp['data']['nextPlayCount'] - resp['data']['nowPlayCount']) == 0:
            #         self.songFull = True
            # self.songFull = False
            if (self.full_level - resp['data']['level'] == 1) and (resp['data']['nextPlayCount'] - resp['data']['nowPlayCount'] == 0):
                self.songFull = True
        self.finishTask() 
       
    def daka(self):
        self.taskTitle('打卡信息')
        user_setting = self.user_setting        
       
        if user_setting['daka']['full_stop']:
            if self.full:
                self.taskInfo('打卡', '您的等级已经爆表了，无需再打卡')
                self.finishTask()
                return
            elif self.songFull:
                self.taskInfo('打卡', '距离满级还差登录天数，无需再打卡')
                self.finishTask()
                return

        playlists = self.music.personalized_playlist(limit=20)
        #推荐歌单id列表
        playlist_ids = [playlist["id"] for playlist in  playlists]
        song_ids = []
                
        total = user_setting['daka']['song_number']
        song_datas = []
        #打乱歌单id
        random.shuffle(playlist_ids)  
        for playlist_id in playlist_ids:
            #获得歌单中歌曲的信息
            songs = self.music.playlist_detail(playlist_id).get("playlist", {}).get("tracks", [])
            for song in songs:
                if song['id'] in song_ids:
                    break
                song_data={
                    "type": 'song',
                    "wifi": 0,
                    "download": 0,
                    "id": song['id'],
                    "time": math.ceil(song['dt']/1000),
                    "end": 'playend',                 
                    "source":'list',
                    "sourceId": playlist_id,                                                
                }
                song_datas.append(song_data)
            if len(song_datas)>=total:
                song_datas = song_datas[0:total]
                break

        num = user_setting['daka']['upload_num']
        for i in range(0, len(song_datas), num):
            self.music.daka(song_datas[i:i+num])
            time.sleep(user_setting['daka']['sleep_time'])
            resp = self.music.user_detail(self.uid)
            if (resp['listenSongs'] - self.listenSongs) >= 300:
                self.title = self.title + '本次听歌'+str(resp['listenSongs']-self.listenSongs)+'首，累计听歌'+str(resp['listenSongs'])+'首'
                self.taskInfo('本次打卡', str(resp['listenSongs'] - self.listenSongs) + '首')
                self.taskInfo('听歌总数', str(resp['listenSongs']) + '首')
                # self.taskInfo('温馨提示', '数据更新有延时，请到网易云音乐APP中查看准确信息')                    
                self.taskInfo('温馨提示', '数据更新可能有延时，[点击查看最新数据](https://music.163.com/#/user/home?id='+str(self.uid)+')')                    
                return
        
        time.sleep(user_setting['daka']['sleep_time'] + 5)
        resp = self.music.user_detail(self.uid)
        self.title = self.title + '本次听歌'+str(resp['listenSongs']-self.listenSongs)+'首，累计听歌'+str(resp['listenSongs'])+'首'
        self.taskInfo('本次打卡', str(resp['listenSongs'] - self.listenSongs) + '首')
        self.taskInfo('听歌总数', str(resp['listenSongs']) + '首')
        # self.taskInfo('温馨提示', '数据更新有延时，请到网易云音乐APP中查看准确信息')
        self.taskInfo('温馨提示', '数据更新可能有延时，[点击查看最新数据](https://music.163.com/#/user/home?id='+str(self.uid)+')')
        self.finishTask()

    def play_playlists(self):
        user_setting = self.user_setting
        self.taskTitle('播放歌单')
        playlist_ids = user_setting['other']['play_playlists']['playlist_ids']
        if len(playlist_ids) == 0:
            self.taskInfo('无可播放歌单')
            return
        count = user_setting['other']['play_playlists']['times']
  
        song_datas = [] 
        for playlist_id in playlist_ids:
            #获得歌单中歌曲的信息
            result = self.music.playlist_detail(playlist_id)
            if result['code'] != 200:
                self.taskInfo('歌单id', str(playlist_id) + '错误')
                break
            songs = result.get("playlist", {}).get("tracks", [])
            self.taskInfo(result["playlist"]['name'], '播放' + str(count) + '次')

            for song in songs:
                song_data={
                    "type": 'song',
                    "wifi": 0,
                    "download": 0,
                    "id": song['id'],
                    "time": math.ceil(song['dt']/1000),
                    "end": 'playend',                  
                    "source":'list',
                    "sourceId": playlist_id,                                                
                }
                song_datas.append(song_data)
        for i in range(count): 
            for playlist_id in playlist_ids:
                self.music.update_playcount(playlist_id)
            self.play(song_datas)   
            time.sleep(1)        

        self.finishTask()     
  

    def taskPublish(self, task):
        if len(task['id'])>0:
            playlist_id = random.choice(task['id'])
        else:
            playlists = self.music.personalized_playlist(limit=10)
            playlist_ids = [playlist["id"] for playlist in playlists]
            playlist_id = random.choice(playlist_ids)
        
        if len(task['msg'])>0:
            event_msg = random.choice(task['msg'])
        else:
            event_msg = '每日分享'

        result = self.music.share_resource(type='playlist',msg=event_msg,id=playlist_id)
        if result['code']==200:
            event_id = result['id']
            if task['delete']:
                time.sleep(0.5)
                delete_result = self.music.event_delete(event_id)
                self.taskInfo(task['taskName'], '发布成功，已删除动态')
            else:
                self.taskInfo(task['taskName'], '发布成功')
        else:
            self.taskInfo(task['taskName'], '发布失败')              
        time.sleep(2)         

    def taskMall(self,task):
        resp = self.music.visit_mall()
        if resp['code'] == 200:
            self.taskInfo(task['taskName'], '访问成功')
        else:
            self.taskInfo(task['taskName'], '访问失败')

    def taskRcmdSong(self, task):
        if len(task['songId']) == 0:
            self.taskInfo(task['taskName'], '请填写歌曲id')
            return
        songId = random.choice(task['songId'])
        yunbeiNum = task['yunbeiNum']
        reason = random.choice(task['reason'])
        resp = self.music.yunbei_rcmd_submit(songId,yunbeiNum,reason)
        if resp['code'] == 200:
            self.taskInfo(task['taskName'], '推歌成功，歌曲id为'+str(songId))
        elif resp['code'] == 400:
            self.taskInfo(task['taskName'], '推歌失败，歌曲id为'+str(songId)+'，失败原因为'+resp.get('message','未知'))
        else:
            self.taskInfo(task['taskName'], '推歌失败，歌曲id为'+str(songId))

    def yunbei_task(self):
        user_setting = self.user_setting

        self.taskTitle('云贝任务')        
        count = 0
        resp = self.music.yunbei_task()
        tasks = user_setting['yunbei_task']
        for t in resp['data']:
            desp = t['taskName']
            if t['userTaskId'] == 0 and desp in tasks and tasks[desp]['on']:                
                if desp == '发布动态':
                    self.taskPublish(tasks[desp])
                    count += 1
                if desp == '访问云音乐商城':
                    self.taskMall(tasks[desp])
                    count += 1
                if desp == '云贝推歌':
                    self.taskRcmdSong(tasks[desp])
                    count += 1
               
        if count == 0:
            self.taskInfo('无可执行的任务')

        self.finishTask()
        time.sleep(0.5)

    def get_yunbei(self):
        self.taskTitle('领取云贝')        
        resp = self.music.yunbei_task_todo()
        count = 0
        for task in resp['data']:
            if task['userTaskId'] > 0:
                self.music.yunbei_task_finish(task['userTaskId'], task['depositCode'])
                self.taskInfo(task['taskName'], '云贝+' + str(task['taskPoint']))
                count += 1
        if count == 0:
            self.taskInfo('无可领取的云贝')

        self.finishTask()

    def play(self,song_datas,sleep_time=3):
        if "upload_num" in self.user_setting['daka']:
            num = self.user_setting['daka']['upload_num']
        else:
            num = 300
        for i in range(0, len(song_datas), num):
            self.music.daka(song_datas[i:i+num])
            time.sleep(sleep_time)
        

    def follow(self):
        author_uid = 347837981
        if self.uid == author_uid:
            return
        resp = self.music.user_detail(author_uid)
        author_nickname = resp['profile']['nickname']
        if not resp['profile']['followed']:            
            follow_resp = self.music.user_follow(author_uid)
            if follow_resp['code'] == 200:
                self.taskTitle('关注作者')
                self.taskInfo('感谢关注', author_nickname)
                # self.taskInfo('如果不想关注，请在配置文件里修改，并在官方客户端里取消关注')
                self.taskInfo('如果不想关注，请在配置文件里修改，并在[主页](https://music.163.com/#/user/home?id='+str(author_uid)+')里取消关注')
                self.finishTask()


    def sign(self):
        self.taskTitle('签到信息')                        
        #手机端签到
        sign_phone = self.music.daily_task(True)
        code_phone = sign_phone["code"]
        if code_phone == 200:
            self.taskInfo('手机端', '云贝+' + str(sign_phone["point"]))
        elif code_phone == -2:
            self.taskInfo('手机端', '重复签到')        
        else:
            self.taskInfo('手机端', '未登录')         

        #桌面端签到
        sign_pc = self.music.daily_task(False)
        code_pc = sign_pc["code"]
        if code_pc == 200:
            self.taskInfo('PC端', '云贝+' + str(sign_pc["point"]))            
        elif code_pc == -2:
            self.taskInfo('PC端', '重复签到')            
        else:
            self.taskInfo('PC端', '未登录')
        
        self.finishTask()    


    def musician_task(self):
        self.taskTitle('音乐人信息')   

        tasks = self.user_setting["musician_task"]
        descriptions = [task for task in tasks]
             
        result = self.music.mission_cycle_get()

        if result['code'] == 200:
            mission_list = result.get('data',{}).get('list',[])
            comments=[]
            replies=[]
            for mission in mission_list:
                desp = mission['description']
                if (mission['status'] == 0 or mission['status'] == 10) and desp in tasks and tasks[desp]['on']==True:
                    num = mission['targetCount'] - mission['progressRate']
                    if desp == "登录音乐人中心":
                        self.music.user_access()
                    elif desp == "发布动态":
                        
                        ids = []
                        if len(tasks[desp]['id'])>0:
                            for i in range(num):
                                ids.append(random.choice(tasks[desp]['id']))
                        else:
                            playlists = self.music.personalized_playlist(limit=10)
                            playlist_ids = [playlist["id"] for playlist in playlists]
                            for i in range(num):
                                ids.append(playlist_ids[i])
                        
                        if len(tasks[desp]['msg'])>0:
                            event_msg = random.choice(tasks[desp]['msg'])
                        else:
                            event_msg = '每日分享'

                        for i in range(num):
                            result = self.music.share_resource(type='playlist',msg=event_msg,id=ids[i])
                            if result['code']==200:
                                event_id = result['id']
                                if tasks[desp]['delete']:
                                    time.sleep(0.5)
                                    self.music.event_delete(event_id)             
                            time.sleep(1)
                    elif desp == "发布主创说":
                        if len(tasks[desp]['id'])>0 and len(comments)==0:
                            songId = random.choice(tasks[desp]['id'])
                            if len(tasks[desp]['msg']) > 0 :
                                msg = random.choice(tasks[desp]['msg'])
                            else:
                                msg = '感谢大家收听'

                            resp = self.music.comments_add(songId,msg)
                            if resp['code'] == 200:
                                comments.append({'commentId':resp['comment']['commentId'],'songId':songId})
                            else:
                                #print(resp)
                                continue

                    elif desp == "回复粉丝评论":
                        if len(comments)>0:
                            commentId = comments[0]['commentId']
                            songId = comments[0]['songId']
                        else:
                            if len(tasks[desp]['id'])>0:
                                songId = random.choice(tasks[desp]['id'])
                                if len(tasks['发布主创说']['msg']) > 0 :
                                    msg = random.choice(tasks['发布主创说']['msg'])
                                else:
                                    msg = '感谢大家收听'

                                resp = self.music.comments_add(songId,msg)
                                if resp['code'] == 200:
                                    commentId = resp['comment']['commentId']
                                    comments.append({'commentId':commentId,'songId':songId})
                                else:
                                    #print(resp)
                                    continue
                            else:
                                continue
                        time.sleep(5)
                        # 改成只执行一次
                        if num>0:
                            loop_num=1
                        for i in range(loop_num):
                            if len(tasks[desp]['msg']) > 0 :
                                msg = random.choice(tasks[desp]['msg'])
                            else:
                                msg = '感谢收听'
                            resp = self.music.comments_reply(songId,commentId,msg)
                            if resp['code'] == 200:
                                replies.append({'commentId':resp['comment']['commentId'],'songId':songId})
                            else:
                                #print('回复错误，错误详情:'+str(resp))
                            	 # time.sleep(152)
                                time.sleep(1)

                    elif desp == "回复粉丝私信":
                        if len(tasks[desp]['id'])>0:
                            user_id = random.choice(tasks[desp]['id'])                            
                            
                            for i in range(num):
                                if len(tasks[desp]['msg']) > 0 :
                                    msg = random.choice(tasks[desp]['msg'])
                                else:
                                    msg = '你好'
                                resp = self.music.msg_send(msg,[user_id])
                                time.sleep(2)
            if tasks['回复粉丝评论']['delete'] and len(replies)>0:
                for reply in replies:
                    resp = self.music.comments_delete(reply['songId'],reply['commentId'])
            if tasks['发布主创说']['delete'] and len(comments)>0:
                for comment in comments:
                    resp = self.music.comments_delete(comment['songId'],comment['commentId'])

        time.sleep(5)
        result = self.music.mission_cycle_get()
        if result['code'] == 200:
            mission_list = result.get('data',{}).get('list',[])
            for mission in mission_list:
                if mission['status'] == 0 and mission['description'] in  descriptions:
                    self.taskInfo(mission['description'], '未完成')
                elif mission['status'] == 10:
                    self.taskInfo(mission['description'], '进行中' + '(' + str(mission['progressRate']) + '/' + str(mission['targetCount']) +  ')')
                elif mission['status'] == 20:
                    description = mission['description']
                    userMissionId = mission['userMissionId']
                    period = mission['period']
                    rewardWorth = mission['rewardWorth']
                        
                    reward_result = self.music.reward_obtain(userMissionId=userMissionId,period=period)
                    if reward_result['code'] == 200:
                        self.taskInfo(description, '云豆+' + str(rewardWorth))                        
                                    
                elif mission['status'] == 100 and mission['description'] in  descriptions:
                    self.taskInfo(mission['description'], '云豆已经领取过了')                    
        else:
            self.taskInfo('任务获取失败')
        info_result = self.music.musician_data()      
        data = info_result.get('data',{})  

        if data['playCount'] is None:
            self.taskInfo('昨日播放量', '--')                
        else:
            self.taskInfo('昨日播放量', data['playCount'])                

        if data['followerCountIncrement'] is None:
            self.taskInfo('昨日新增粉丝(人)', '--')                
        else:
            self.taskInfo('昨日新增粉丝(人)', data['followerCountIncrement'])                

        if data['productionTotal'] is None:
            self.taskInfo('作品(首)', '--')
        else:
            self.taskInfo('作品(首)', data['productionTotal'])                

        if data['availableExtractIncomeTotal'] is None:
            self.taskInfo('可提现余额', '--')
        else:
            self.taskInfo('可提现余额', data['availableExtractIncomeTotal'])            

        if data['musicianLevelScore'] is None:
            self.taskInfo('音乐人指数', '--')                
        else:
            self.taskInfo('音乐人指数', data['musicianLevelScore'])                

        self.finishTask()
        
