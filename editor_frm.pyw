########################################################################
# 文件名：editor_frm.pyw
# 作者：  刘明祥
# 功能：  实现VScode中的代码编辑器调用
#        创建一个websocket服务端进程，处理浏览器与本地数据的交互，包括文件的打开与保存等
#        创建一个窗口进程，在窗口中嵌入浏览器，浏览器打开嵌入了monaco.editor的网页，
#        同时，该网页中也创建了一个websocket客户端，负则在浏览器和websocket服务端之间的数据交互
#        
# JSON格式的协议：
# 设置主题
# {"cmd":"settheme", theme":"", "fontsize":12}
# 打开文件
# {"cmd":"openfile", "file":"", "txt":""}
# 保存文件
# {"cmd":"savefile_req", "reqid":0, "file":""}
# {"cmd":"savefile_rsp", "reqid":0, "file":"", "txt":"", "errtxt":""}
########################################################################

import os, json, asyncio, websockets, datetime, multiprocessing, threading, winreg, chardet


########################################################################
# 日志打印
class log(object):
    def __init__(self, logfile, level = 'I'):
        self.__levels = ['D', 'I', 'W', 'E', 'F']
        self.__level = self.__levels.index(level)
        self.__file = open(logfile, 'a')

    def __print(self, level, *args):
        if self.__levels.index(level) < self.__level:
            return
        tim = datetime.datetime.now()
        self.__file.write('[%s][%d%02d%02d.%02d%02d%02d.%06d]%s\r\n' % (level, tim.year, tim.month, tim.day, tim.hour, tim.minute, tim.second, tim.microsecond, ''.join(args[0])))
        self.__file.flush()

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

g_log = log('websvr.log', 'D')

########################################################################
# websocket服务，负责网页和本地数据之间的交互
class websocketsvr(object):    
    def __init__(self, sendqueue):
        self.__log = g_log
        self.__cmds = sendqueue

    async def __filepipe(self, webskt, path):
        self.__log.info("client connected successfully") 
        while True:
            # 等待数据发送完成
            while not self.__cmds.empty():
                try:
                    s_dat = self.__cmds.get(False)
                except:
                    continue
                s_str = json.dumps(s_dat)
                if s_str != "":                    
                    await webskt.send(s_str)
            
            # 接收数据完成或超时
            try:
                # r_str = await webskt.recv()
                r_str = await asyncio.wait_for(webskt.recv(), timeout=0.1)
                r_dat = json.loads(r_str)
                self.__on_recv(r_dat) 
            except:
                pass

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
        self.__log.info("savefile: ", file)
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
        self.__log.info("savefile: ", file)
    

########################################################################
# websocket进程执行函数
def run_websktsvr(sendqueue, ip, port):
    websvr = websocketsvr(sendqueue)
    websvr.start_svr(ip, port)


########################################################################
# editor操作，设置主题、打开文件、保存文件
class editor_action:
    def __init__(self, ip, port):
        self.__log = g_log
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

    # 二进制数据转十六进制字符串
    def str2hex(this, data):
        txt = ""
        i = 0
        for s in data:
            if i % 16 == 0:
                txt += "\n%08xh" % (i)
            txt += " %02x" % (s)
            i += 1

        return txt

    # 打开文件，自动判断文件编码并解析
    def openfile(self, file): 
        try:
            f = open(file, mode = 'rb')
        except:
            self.__log.error("openfile faild, file:", file)
            return
        text = f.read()
        f.close()
        code = chardet.detect(text)['encoding']
        print('****code****:', code)

        txt = ''
        if code in ['ascii', 'utf-8', 'gb2312', 'gbk', 'gb18030', 'hz', 'big5', 'unicode']:
            txt = text.decode(code)
        else:            
            txt = self.str2hex(text)
            print(txt)

        data = {
            'cmd':'openfile',
            'file':file,
            'txt':txt
        }
        self.__senddata(data)
        self.__log.info("openfile: ", file)

    # 保存文件
    def savefile(self, file = ""):
        data = {
            'cmd':'savefile_req',
            'reqid':0,
            'file':file
        }
        self.__senddata(data)




########################################################################
# PyQt主窗口，嵌入浏览器, wx组件实现
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *
from urllib import request
 
import sys
import html

class main_frm_qt(QWidget): 
    def __init__(self, ip, port, title, url): 
        super().__init__()

        self.set_reg()
        self.__action = editor_action(ip, port)

        self.setWindowTitle(title)  
        self.resize(1800, 1200)
        self.center()     
                

        btn_open = QPushButton("打开文件", self)
        btn_save = QPushButton("保存文件", self)
        lab_theme = QLabel("主题", self)
        cmb_theme = QComboBox(self)
        browser = QWebEngineView()

        hbox = QHBoxLayout()
        hbox.setSpacing(10)
        hbox.setContentsMargins(10,5,0,5)
        hbox.addWidget(btn_open)
        hbox.addWidget(btn_save)
        hbox.addWidget(lab_theme)
        hbox.addWidget(cmb_theme)
        hbox.addStretch(1)
        
        vbox = QVBoxLayout(self)
        vbox.setSpacing(0)
        vbox.setContentsMargins(0,0,0,0)
        vbox.addLayout(hbox)
        vbox.addWidget(browser, 1)

        self.setLayout(vbox)

        
        btn_open.clicked[bool].connect(self.on_loadclick)
        btn_save.clicked[bool].connect(self.on_saveclick)
        cmb_theme.addItem('浅色')
        cmb_theme.addItem('深色')
        cmb_theme.addItem('高亮')
        cmb_theme.setCurrentIndex(1)
        cmb_theme.currentIndexChanged[int].connect(self.on_changetheme)
        browser.load(QUrl(self.path2url(url)))
    
    def __del__(self):
        self.__action.__del__()
        # 强制结束浏览器进程，程序退出后该进程不会自动退出，且会占满一个逻辑CPU内核
        os.system("taskkill /F /T /IM QtWebEngineProcess.exe")

    def path2url(self, path):
        workdir = os.path.dirname(os.path.realpath(__file__))
        # 设置工程所在目录为当前目录
        os.chdir(workdir) 
        return 'file:' + request.pathname2url(os.path.abspath(path))

    def set_reg(self):
        # 这里需要打开所有权限, 设置注册表python.exe 值为 11000(IE11)
        self.key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION", 0, winreg.KEY_ALL_ACCESS)
        try:            
            winreg.SetValueEx(self.key, 'python.exe', 0, winreg.REG_DWORD, 0x00002af8)
            winreg.CloseKey(self.key)
        except:
            print('set default browser version faild!')

    def resizeEvent(self, evt):
        pass

    #控制窗口显示在屏幕中心的方法
    def center(self):        
        #获得窗口
        qr = self.frameGeometry()
        #获得屏幕中心点
        cp = QDesktopWidget().availableGeometry().center()
        #显示到屏幕中心
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # 析构action
    def closeEvent(self, evt):        
        self.__action.__del__()

    def on_loadclick(self, val):
        fname, ftype = QFileDialog.getOpenFileName(self, "打开...", "F:/Work/py", "python文件(*.py *pyw);;其他文件(*.*)")
        if fname != "":
            self.__action.openfile(fname)  
    
    def on_saveclick(self, val):
        self.__action.savefile()

    def on_changetheme(self, val):
        theme = 'vs' if val == 0 else ('vs-dark' if val == 1 else 'hc-black')
        self.__action.settheme(theme)  

    # 如果当前标签页只剩下一个则不关闭
    def close_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

########################################################################
if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainfrm = main_frm_qt("localhost", 8765, "pyeditor", "./python_editor/editor.htm")
    mainfrm.show()

    sys.exit(app.exec_())




'''
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
# wxPython主窗口，嵌入浏览器, wx组件实现
import wx, wx.html2
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
        #browser.setJavascriptEnabled(True)
        #browser.setDomStorageEnabled(True)
        
        # 界面布局：按钮、风格选项、浏览器
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
'''