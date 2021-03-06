#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, platform, os, time, requests
from http.cookiejar import Cookie, LWPCookieJar
from encrypt import encrypted_request

DEFAULT_TIMEOUT = 10

BASE_URL = "https://music.163.com"

class NetEase(object):
    def __init__(self, username=''):
        self.header = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate,sdch",
            "Accept-Language": "zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "music.163.com",
            "Referer": "http://music.163.com",
            "X-Real-IP": "118.88.88.88",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
        }
        username = str(username)
        self.username = username
        self.session = requests.Session()
        if username =="":
            return
        cookie_file = self.cookiefile(username)
        if cookie_file:
            cookie_jar = LWPCookieJar(cookie_file)
            cookie_jar.load()
            self.session.cookies = cookie_jar
            self.session.cookies.load()

    def cookiefile(self, filename):
        data_dir = os.path.join(os.path.expanduser("."), ".user_data")
        user_path = os.path.join(data_dir, filename)
        cookie_file = os.path.join(user_path, "cookie")
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
            except:
                return ""
        if not os.path.exists(user_path):
            try:
                os.makedirs(user_path)
            except:
                return ""   
        
        if not os.path.exists(cookie_file):
            try:
                f = open(cookie_file, "w", encoding="utf-8")
                f.write('#LWP-Cookies-2.0\nSet-Cookie3:')
                f.close()                
            except:
                return ""
        
        return cookie_file

    def _raw_request(self, method, endpoint, data=None):
        if method == "GET":
            resp = self.session.get(
                endpoint, params=data, headers=self.header, timeout=DEFAULT_TIMEOUT
            )
        elif method == "POST":
            resp = self.session.post(
                endpoint, data=data, headers=self.header, timeout=DEFAULT_TIMEOUT
            )
        return resp

    # ??????Cookie??????
    def make_cookie(self, name, value):
        return Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain="music.163.com",
            domain_specified=True,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest={},
        )

    def request(self, method, path, params={}, base_url=BASE_URL,default={"code": -1}, custom_cookies={'os':'pc'}):
        endpoint = "{}{}".format(BASE_URL, path)
        csrf_token = ""
        for cookie in self.session.cookies:
            if cookie.name == "__csrf":
                csrf_token = cookie.value
                break
        params.update({"csrf_token": csrf_token})
        data = default

        for key, value in custom_cookies.items():
            cookie = self.make_cookie(key, value)
            self.session.cookies.set_cookie(cookie)

        params = encrypted_request(params)
        try:
            resp = self._raw_request(method, endpoint, params)
            data = resp.json()
        except requests.exceptions.RequestException as e:
            print(e)
        except ValueError as e:
            print("Path: {}, response: {}".format(path, resp.text[:200]))
        finally:
            return data

    def login(self, username, password):    
        cookie_file = self.cookiefile(str(username))
        if cookie_file:
            if self.username != str(username):
                cookie_jar = LWPCookieJar(cookie_file)
                cookie_jar.load()
                self.session.cookies = cookie_jar
                self.session.cookies.load()
                self.session.cookies.save()
                self.username = str(username)   

        if username.isdigit():
            path = "/weapi/login/cellphone"
            params = dict(phone=username, password=password, rememberLogin="true")
        else:
            # magic token for login
            # see https://github.com/Binaryify/NeteaseCloudMusicApi/blob/master/router/login.js#L15
            client_token = (
                "1_jVUMqWEPke0/1/Vu56xCmJpo5vP1grjn_SOVVDzOc78w8OKLVZ2JH7IfkjSXqgfmh"
            )
            path = "/weapi/login"
            params = dict(username=username, password=password,rememberLogin="true",clientToken=client_token)
        data = self.request("POST", path, params)

        if cookie_file:
            self.session.cookies.save()
        return data

    # ????????????
    def daily_task(self, is_mobile=True):
        path = "/weapi/point/dailyTask"
        params = dict(type=0 if is_mobile else 1)
        return self.request("POST", path, params)

    # ????????????
    def user_playlist(self, uid, offset=0, limit=50,includeVideo=True):
        path = "/weapi/user/playlist"
        params = dict(uid=uid, offset=offset, limit=limit, includeVideo=includeVideo)
        return self.request("POST", path, params)

    # ???????????? privacy:0 ??????????????????10 ??????????????????type:NORMAL|VIDEO
    def playlist_create(self, name, privacy=0, ptype='NORMAL'):
        path = "/weapi/playlist/create"
        params = dict(name=name,privacy=privacy,type=ptype)
        return self.request("POST", path, params)    

    # ??????/?????????????????????
    # op:'add'|'del'
    def playlist_tracks(self, pid, ids,op='add'):
        path = "/weapi/playlist/manipulate/tracks"        
        params = {'op':op,'pid':pid,'trackIds': json.dumps(ids),'imme':'true'}
        result = self.request("POST", path, params)              
        if result['code'] == 512:
            ids.extend(ids)
            params = {'op':op,'pid':pid,'trackIds': json.dumps(ids),'imme':'true'}
            result = self.request("POST", path, params)            
        return result   

    # ??????????????????
    def playlist_desc_update(self,id,desc):
        path="/weapi/playlist/desc/update"
        params=dict(id=id,desc=desc)
        return self.request("POST", path,params)         

    # ??????????????????
    def recommend_resource(self):
        path = "/weapi/v1/discovery/recommend/resource"
        return self.request("POST", path).get("recommend", [])

    # ????????????
    def personalized_playlist(self,limit=9):
        path = "/weapi/personalized/playlist"
        params = dict(limit=limit)
        return self.request("POST", path,params).get("result", [])        

    # ??????FM
    def personal_fm(self):
        path = "/weapi/v1/radio/get"
        return self.request("POST", path)#.get("data", [])        

    # ????????????
    def playlist_detail(self, playlist_id):
        path = "/weapi/v3/playlist/detail"
        params = dict(id=playlist_id, total="true", limit=1000, n=1000, offest=0)
        # cookie??????os??????
        custom_cookies = dict(os=platform.system())
        return self.request("POST", path, params, {"code": -1}, custom_cookies)

    # ????????????
    def album(self, album_id):
        path = "/weapi/v1/album/{}".format(album_id)
        return self.request("POST", path)#.get("songs", [])

    # ????????????
    def songs_detail(self, ids):
        path = "/weapi/v3/song/detail"
        params = dict(c=json.dumps([{"id": _id} for _id in ids]), ids=json.dumps(ids))
        return self.request("POST", path, params).get("songs", [])

    #????????????
    def user_follow(self, id):
        path = "/weapi/user/follow/{}".format(id)
        return self.request("POST", path)      
         
    # ???????????? type: 0 ???????????? 1????????????
    def play_record(self, uid, time_type=0,limit=1000,offset=0,total=True):
        path = "/weapi/v1/play/record"
        params = dict(uid=uid,type=time_type,limit=limit,offset=offset,total=total)
        return self.request("POST", path, params)#.get("allData", [])   #weekData      

    # ???????????? privacy:0 ??????????????????10 ??????????????????type:NORMAL|VIDEO
    def playlist_creat(self, name, privacy=0, ptype='NORMAL'):
        path = "/weapi/playlist/create"
        params = dict(name=name,privacy=privacy,type=ptype)
        return self.request("POST", path, params)        

    # ??????
    def daka(self, song_datas):
        path = "/weapi/feedback/weblog"
        songs = []
        for i in range(len(song_datas)):
            song = {
                'action': 'play',
                'json': song_datas[i]
            }
            songs.append(song)
        params = {'logs': json.dumps(songs)}
        return self.request("POST", path, params)

    # ????????????
    def user_detail(self, uid):  
        path = "/weapi/v1/user/detail/{}".format(uid)
        return self.request("POST", path)         

    def user_level(self):
        path = "/weapi/user/level"
        return self.request("POST", path)
   

    # ??????????????????
    def yunbei_task(self):
        path = "/weapi/usertool/task/list/all"
        return self.request("POST", path)#.get("data", [])

    # ??????todo??????
    def yunbei_task_todo(self):
        path = "/weapi/usertool/task/todo/query"
        return self.request("POST", path)#.get("data", [])

    # ??????????????????
    def yunbei_task_finish(self, userTaskId, depositCode):
        path = "/weapi/usertool/task/point/receive"        
        params = dict(userTaskId=userTaskId,depositCode=depositCode)
        return self.request("POST", path, params) 

    def share_resource(self, type='playlist',msg='',id=''):
        path = "/weapi/share/friends/resource"        
        params = dict(type=type,msg=msg,id=id)
        return self.request("POST", path, params)            
    
    # ????????????
    def event_delete(self, id):
        path = "/weapi/event/delete"        
        params = dict(id=id)
        return self.request("POST", path, params)

    # ????????????
    def playlist_delete(self, ids):
        path = "/weapi/playlist/remove"        
        params = dict(ids=ids)
        return self.request("POST", path, params)        

    ###########################
    # ?????????

    # ??????
    def musician_data(self):        
        path='/weapi/creator/musician/statistic/data/overview/get'
        return self.request("POST", path)     

    # ????????????
    def mission_cycle_get(self,actionType='',platform=''):        
        path='/weapi/nmusician/workbench/mission/cycle/list'
        if actionType=='' and platform == '':
            return self.request("POST", path)
        else:
            params=dict(actionType=actionType,platform=platform)
            return self.request("POST", path,params)

    # ????????????
    def reward_obtain(self,userMissionId,period):        
        path='/weapi/nmusician/workbench/mission/reward/obtain/new'
        params=dict(userMissionId=userMissionId,period=period)
        return self.request("POST", path,params)

    # ???????????????
    def cloudbean(self):
        path = "/weapi/cloudbean/get"
        return self.request("POST", path)      

    def user_access(self):        
        path='/weapi/creator/user/access'
        return self.request("POST", path)

    # ??????????????????: ????????????
    def visit_mall(self):
        path = "/weapi/yunbei/task/visit/mall"        
        return self.request("POST", path)    

    # ?????????????????????
    def comments_add(self, song_id, content):
        path = "/weapi/resource/comments/add"
        params = dict(threadId='R_SO_4_'+str(song_id), content=content)
        return self.request("POST", path, params)     

    # ??????????????????
    def comments_reply(self, song_id,commentId, content):
        path = "/weapi/v1/resource/comments/reply"
        params = dict(commentId=commentId,threadId='R_SO_4_'+str(song_id), content=content)
        return self.request("POST", path, params)

    # ????????????
    def comments_delete(self, song_id,commentId):
        path = "/weapi/resource/comments/delete"
        params = dict(commentId=commentId,threadId='R_SO_4_'+str(song_id))
        return self.request("POST", path, params)

    # ????????????
    def msg_send(self, msg,userIds,type='text'):
        path = "/weapi/msg/private/send"
        params = dict(type=type,msg=msg,userIds=userIds)
        return self.request("POST", path, params)
        
    def update_playcount(self,id):
        path="/weapi/playlist/update/playcount"
        params=dict(id=id)
        return self.request("POST", path,params)

    # ????????????
    def yunbei_rcmd_submit(self,songId,yunbeiNum=10,reason='????????????????????????????????????????????????',scene='',fromUserId=-1):        
        path = "/weapi/yunbei/rcmd/song/submit"
        params = dict(songId=songId,reason=reason,scene=scene,yunbeiNum=yunbeiNum,fromUserId=fromUserId)
        return self.request("POST", path,params)   
          
