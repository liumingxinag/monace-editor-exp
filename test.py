import json, asyncio, websockets, datetime

# JSON格式的协议：
# 设置主题
# {"cmd":"settheme", "theme":"", "fontsize":12}
# 打开文件
# {"cmd":"openfile", "file":"", "txt":""}
# 保存文件
# {"cmd":"savefile", "file":"", "txt":""}

class log(object):
    def __init__(self, level = 'I'):
        self.__levels = ['D', 'I', 'W', 'E', 'F']
        self.__level = self.__levels.index(level)

    def __print(self, level, *args):
        if self.__levels.index(level) < self.__level:
            return
        tim = datetime.datetime.now()
        print('[%s][%d%02d%02d.%02d%02d%02d.%06d]%s' % (level, tim.year, tim.month, tim.day, tim.hour, tim.minute, tim.second, tim.microsecond, ''.join(args[0])))

    def debug(self, *args):
        self.__print('D', args)
    def info(self, *args):
        self.__print('I', args)
    def warn(self, *args):
        self.__print('W', args)
    def error(self, *args):
        self.__print('E', args)
    def fatal(self, *args):
        self.__print('F', args)



class websocketsvr(object):    
    def __init__(self):
        self.__sendlist = {}
        self.__log = log('D')

    async def __filepipe(self, connect, path):
        # 客户端登录成功
        self.__log.info("client connected successfully")
        # 初始打开的文件，测试用
        self.openfile("F:\Work\py\\nacui.py")   
        while True:
            # 等待数据发送完成
            for s_dat in self.__sendlist.values():
                s_str = json.dumps(s_dat)
                if s_str != "":                    
                    await connect.send(s_str)
            self.__sendlist.clear()
            
            # 等待数据接收完成
            r_str = await connect.recv()
            r_dat = json.loads(r_str)
            self.__on_recv(r_dat) 

    #启动服务
    def start(self, ip, port):
        try:
            start_server = websockets.serve(self.__filepipe, ip, port)
        except:
            self.__log.error("websocket service start faild in %s:%d" % (ip, port))
            return
        self.__log.info("websocket service startted successfully  in %s:%d" % (ip, port))
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    #####################################################################
    # 数据接收
    def __on_recv(self, data):
        if data['cmd'] == 'savefile':
            self.__savefile(data['file'], data['txt'])

    # 数据发送,加入发送队列,发送队列中每个命令下只保存最新的一条数据
    def __senddata(self, data):
        self.__sendlist[data['cmd']] = data

    #####################################################################
    # 设置主题风格 theme:vs-dark vs hc-black, fontsize:S M L XL XXL
    def settheme(self, theme = "vs-dark", fontsize = 'S'):
        data = {
            'cmd':'settheme', 
            'theme':theme, 
            'fontsize':fontsize
        }
        self.__senddata(data)

    # 打开文件
    def openfile(self, file):  
        try:
            f = open(file, mode = 'r', encoding = 'utf-8')
        except:
            self.__log.error("openfile falid, file:", file)
            return
        txt = f.read()
        f.close()

        data = {
            'cmd':'openfile',
            'file':file,
            'txt':txt
        }
        self.__senddata(data)

    # 保存文件
    def __savefile(self, file, txt): 
        try:
            f = open(file, mode ='w', encoding = 'utf8')
        except:            
            self.__log.error("savefile falid, file:", file)           
            return       
        f.write(txt)
        f.close()


# websvr = websocketsvr()
# websvr.start("localhost", 8765)

# 打开浏览器
import wx, wx.html2, winreg

class web_fream(wx.Frame):  
    def __init__(self, parent, title): 
        wx.Frame.__init__(self, parent, -1, title, size=(1024, 768))
        # 这里需要打开所有权限, 设置注册表python.exe 值为 11000(IE11)
        self.key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION", 0, winreg.KEY_ALL_ACCESS)
        try:            
            winreg.SetValueEx(self.key, 'python.exe', 0, winreg.REG_DWORD, 0x00002af8)
        except:
            print('set default browser version faild!')
        self.browser = wx.html2.WebView.New(self, style=0)
        self.Bind(wx.EVT_CLOSE, self.on_close)                        
    
    # 用完取消注册表设置, 关闭打开的注册表
    def on_close(self, evt):
        #winreg.DeleteValue(self.key, 'python.exe')
        winreg.CloseKey(self.key)
        evt.Skip()

app = wx.App() 
frame = web_fream(None, "editor")
# frame.browser.LoadURL("https://microsoft.github.io/monaco-editor/") 
frame.browser.LoadURL("file:///F:/Work/py/python%20editor/editor.html") 
frame.Show() 
app.MainLoop()
