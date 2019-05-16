import os, json, asyncio, websockets, datetime, multiprocessing, threading

# JSON格式的协议：
# 设置主题
# {"cmd":"settheme", theme":"", "fontsize":12}
# 打开文件
# {"cmd":"openfile", "file":"", "txt":""}
# 保存文件
# {"cmd":"savefile_req", "reqid":0, "file":""}
# {"cmd":"savefile_rsp", "reqid":0, "file":"", "txt":"", "errtxt":""}


########################################################################
# 日志打印
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


########################################################################
# websocket服务，负责网页和本地数据之间的交互
class websocketsvr(object):    
    def __init__(self, sendqueue):
        self.__cmds = sendqueue
        self.__log = log('D')

    async def __filepipe(self, webskt, path):
        self.__log.info("client connected successfully") 
        while True:
            # 等待数据发送完成
            while not self.__cmds.empty():
                try:
                    s_dat = self.__cmds.get(False)
                except:
                    break
                s_str = json.dumps(s_dat)
                if s_str != "":                    
                    await webskt.send(s_str)
            
            # 接收完成
            try:
                r_str = await webskt.recv()
                r_dat = json.loads(r_str)
                self.__on_recv(r_dat) 
            except:
                await asyncio.sleep(0.01)

    # 启动服务
    def start_svr(self, ip, port):
        try:
            start_server = websockets.serve(self.__filepipe, ip, port)
        except:
            self.__log.error("websocket service start faild in %s:%d" % (ip, port))
            return
        self.__log.info("websocket service startted successfully  in %s:%d" % (ip, port))
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    # 数据接收
    def __on_recv(self, data):
        if data['cmd'] == 'savefile_rsp':
            self.__on_savefile_rsp(data['file'], data['txt'], data['errtxt'])

    # 保存文件应答
    def __on_savefile_rsp(self, file, txt, errtxt): 
        if errtxt:
            self.__log.error('save file faild, err:%d file:%s' % (errtxt, file))
            return
        try:
            f = open(file, mode ='w', encoding = 'utf8')
        except:            
            self.__log.error("save file faild, file:", file)           
            return       
        f.write(txt)
        f.close()
        print("save file ", file)
    

########################################################################
# websocket进程执行函数
def run_websktsvr(sendqueue, ip, port):
    websvr = websocketsvr(sendqueue)
    websvr.start_svr(ip, port)


########################################################################
# editor操作，设置主题、打开文件、保存文件
class editor_action:
    def __init__(self, ip, port):
        self.__log = log('D')
        self.__cmds = multiprocessing.Queue(100)

        # 在子进程中启动websocket服务
        self.__websvr = multiprocessing.Process(target=run_websktsvr, args=(self.__cmds, ip, port,))
        self.__websvr.start()

    def __del__(self):
        # 结束websocket服务
        self.__cmds.cancel_join_thread()
        self.__websvr.terminate()

    # 数据发送,加入发送队列,发送队列中每个命令下只保存最新的一条数据, 是否加超时
    def __senddata(self, data):        
        self.__cmds.put(data)

    # 设置主题风格 theme:vs vs-dark hc-black, fontsize:S M L XL XXL
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
            self.__log.error("openfile faild, file:", file)
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
    def savefile(self, file = ""):
        data = {
            'cmd':'savefile_req',
            'reqid':0,
            'file':file
        }
        self.__senddata(data)



########################################################################
# httpsvr进程, 设置工程所在目录为当前目录，因为httpsvr使用当前目录对外服务
# from http.server import HTTPServer, SimpleHTTPRequestHandler
# def run_websvr():
#     workdir = os.path.dirname(os.path.realpath(__file__)) + "\python_editor"
#     print("workdir: ", workdir)
#     os.chdir(workdir) 
#     server = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
#     print("Starting server, listen at: %s:%s" % ('localhost', 8000))
#     server.serve_forever()


########################################################################
# 主窗口，嵌入浏览器
import wx, wx.html2, winreg
class main_frm(wx.Frame):  
    def __init__(self, parent, ip, port, title, url): 
        wx.Frame.__init__(self, parent, -1, title, size=(1024, 768))
        self.__action = editor_action(ip, port)

        # 这里需要打开所有权限, 设置注册表python.exe 值为 11000(IE11)
        self.key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION", 0, winreg.KEY_ALL_ACCESS)
        try:            
            winreg.SetValueEx(self.key, 'python.exe', 0, winreg.REG_DWORD, 0x00002af8)
        except:
            print('set default browser version faild!')
        
        self.Bind(wx.EVT_CLOSE, self.on_close) 
        
        pan = wx.Panel(self) 
        btn_load = wx.Button(pan, label = "打开文件")
        btn_load.Bind(wx.EVT_LEFT_DOWN, self.on_loadclick) 
        
        btn_save = wx.Button(pan, label = "保存文件")
        btn_save.Bind(wx.EVT_LEFT_DOWN, self.on_saveclick) 
        
        lb_theme = wx.StaticText(pan, label = "主题", style = wx.ALIGN_CENTER)        
        self.__cbx_theme = wx.ComboBox(pan, choices = ['浅色', '深色', '高对比'], value = '深色', style = wx.ALIGN_CENTER | wx.CB_READONLY)
        self.__cbx_theme.Bind(wx.EVT_COMBOBOX, self.on_changetheme) 

        browser = wx.html2.WebView.New(pan, pos=wx.Point(0, 30), style=0, url=os.path.realpath(url))
        
        # 界面布局
        actbox = wx.BoxSizer(wx.HORIZONTAL)      
        actbox.Add(btn_load, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 4) 
        actbox.Add(btn_save, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 8) 
        actbox.Add(lb_theme, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 8) 
        actbox.Add(self.__cbx_theme, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL | wx.TOP | wx.BOTTOM, 4) 
        
        vbox = wx.BoxSizer(wx.VERTICAL)    
        vbox.Add(actbox, 0, wx.LEFT)   
        vbox.Add(browser, 1, wx.EXPAND)  
        pan.SetSizer(vbox) 

    
    # 用完取消注册表设置, 关闭打开的注册表
    def on_close(self, evt):
        #winreg.DeleteValue(self.key, 'python.exe')
        winreg.CloseKey(self.key)
        evt.Skip()
        # 析构action
        self.__action.__del__()

    def on_loadclick(self, evt):
        self.__action.openfile("F:\Work\py\\nacui.py")  
    
    def on_saveclick(self, evt):
        self.__action.savefile()  

    def on_changetheme(self, evt):
        val = self.__cbx_theme.GetValue()
        theme = 'vs-dark'
        if val == '浅色':
            theme = 'vs'
        elif val == '高对比':
            theme = 'hc-black'

        self.__action.settheme(theme)  


########################################################################
if __name__ == '__main__':
    app = wx.App() 

    mainfrm = main_frm(None, "localhost", 8765, "editor", "F:/Work/py/python_editor/editor.html")
    mainfrm.Show()

    app.MainLoop()
