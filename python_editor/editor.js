//////////////////////////////////////////////////////////////////////////////
// 文件名：editor.js
// 作者：  刘明祥
// 功能：  实现VScode中的代码编辑器调用, 在网页中嵌入monaco.editor，并在本地进程中嵌入一个浏览器打开该网页
//        在网页中创建websocket客户端和同一本地进程里的websocket服务端通信来完成代码文件的加载与保存
//
// JSON格式的协议：
// 设置主题
// {"cmd":"settheme", "theme":"", "fontsize":12}
// 打开文件
// {"cmd":"openfile", "file":"", "txt":""}
// 保存文件
// {"cmd":"savefile", "file":"", "txt":""}
//////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////////
///代码编辑器 monaco.editor
//////////////////////////////////////////////////////////////////////////////

//当前代码编辑器所打开的文件，为空则为新建文件
var g_model = null;
var g_filename = "";
//编辑器实例
var g_editor = null;


//初始化编辑器
function init_editor(layoutid, code_str) 
{    
    if (g_editor)
        return;
    //初始化编辑器
    require.config(
        {
            paths: { 'vs': 'monaco-editor-0.16.2/package/min/vs' }, 
            'vs/nls': { availableLanguages: {'*': 'zh-cn'} }
        }
    );
    require(['vs/editor/editor.main'], function () 
    {
        g_editor = monaco.editor.create(
            document.getElementById(layoutid), 
            {
                language: 'python',             //程序语言
                theme: 'vs-dark',
                //wordWrap: "on",               //自动换行，注意大小写
                //wrappingIndent: "indent", 
                value: code_str,                //初始文本内容
                automaticLayout: true,          //随布局Element自动调整大小                        
                minimap: {enabled: false},      //代码略缩图
            }
        );
    });

    //自适应大小，可以不要
    window.onresize = editor_layout;
    //编辑器加载成功后创建websocket连接
    window.onload = init_webskt;
}

//自适应窗口大小
function editor_layout()
{
    if (g_editor)
        g_editor.layout()
}

//设置主题风格 theme:vs-dark vs hc-black, fontsize:S M L XL XXL
function set_theme(theme, fontsize) 
{
    monaco.editor.setTheme(theme); 

    const sizes = ['S', 'M', 'L', 'XL', 'XXL'];
    ind = sizes.indexOf(fontsize);
    if (ind < 0)
        return;
    document.getElementsByTagName('body')[0].style.zoom = ind + 1 + ind * 0.5
}

//设置代码文件
function load_file(file, txt)
{
    g_filename = file;
    g_editor.setValue(txt);
}
//保存代码到本地文件, 第一行为文件名, 文件名如果为空在在python端弹出保存对话框
function save_file()
{
    data = {
        'cmd':'savefile',
        'file':g_filename,
        'txt':g_editor.getValue()
    }
    senddata(data);
}


//////////////////////////////////////////////////////////////////////////////
///websocket客户端
//////////////////////////////////////////////////////////////////////////////
var ws = null;
//判断浏览器是否内置了websocket
function init_webskt()
{
    if (ws != null)
        return;
    if ('WebSocket' in window)
        ws = new WebSocket("ws://localhost:8765");
    else{
        alert("error, WebSocket not exist!");
        return;
    }
    
    //连接web socket成功触发
    ws.onopen = function (evt){}
    //断开web socket成功触发
    ws.onclose = function (evt){
        ws = null;
        setTimeout(1000);
        init_webskt();
    }
    //web socket连接失败时触发
    ws.onerror = function (evt){}

    //当窗口关闭时，关闭websocket。防止server端异常
    ws.onbeforeunload = function (evt){
        ws.close();
    }

    //接收web socket服务端数据时触发
    ws.onmessage = function (evt) {
        //alert(evt.data);
        data = JSON.parse(evt.data);
        if (data.cmd == 'openfile')
            load_file(data.file, data.txt);
        else if (data.cmd == 'settheme')
            set_theme(data.theme, data.fontname, data.fontsize)
    };
}


//发送文本到websocket服务端
function senddata(data) {
    init_webskt();
    json_str = JSON.stringify(data);
    //alert(json_str);
    ws.send(json_str);
}
