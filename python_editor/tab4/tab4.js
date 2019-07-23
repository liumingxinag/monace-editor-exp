// == 值比较  === 类型比较 $(id) ---->  document.getElementById(id)
function $(id){
    return typeof id === 'string' ? document.getElementById(id):id;
}
 
//全局字典
var datas = new Array();

// 当前标签
var currtab = ""

// 切换标签
function switch_tab(newtab){   
    if (newtab == currtab)
        return;

    var tab = $(newtab.toString());
    if (!tab && newtab != "")
        return;

    if (tab)
        tab.className = 'current';
    $('editor').innerHTML = tab ? datas[newtab] : '';

    tab = $(currtab.toString())
    if (tab)
        tab.className = '';

    currtab = newtab;
}

// 添加标签
function add_tab(name, value){
    if (name == "" || datas[name])
        return;

    //新建标签
    var tab = document.createElement("li");
    tab.id = name;
    tab.innerHTML = name.substr(name.lastIndexOf('/')+1);

    //新建关闭按钮
    var btn = document.createElement("a");
    btn.href = "#";
    btn.innerHTML = "x";

    //添加按钮到标签上
    tab.appendChild(btn);
    //添加按钮到标签栏上
    $('tabs').appendChild(tab);

    //设置标签和按钮的单击事件
    tab.onclick = function(){
        switch_tab(this.id);
    }
    btn.onclick = function(){
        var tab = this.parentNode;
        if (tab.className == 'current')
        {
            var _tab = tab.nextElementSibling;
            if (!_tab)
                _tab = tab.previousElementSibling;
            switch_tab(_tab ? _tab.id : '');
        }
        delete datas[tab.id];
        tab.remove();
    }

    //添加标签关联的数据
    datas[name] = value;
    //切换到新标签
    switch_tab(name);
}


////////////////////////////////////////////////////////////////////
// 页面初始化
////////////////////////////////////////////////////////////////////
window.onload = function(){
    add_tab("蒹葭", "<br/>" +
        "蒹葭苍苍　白露为霜<br/><br/>" +
        "所谓伊人　在水一方<br/><br/>" +
        "溯洄从之　道阻且长<br/><br/>" +
        "溯游从之　宛在水中央<br/><br/>" +
        "蒹葭萋萋　白露未晞<br/><br/>" +
        "所谓伊人　在水之湄<br/><br/>" +
        "溯洄从之　道阻且跻<br/><br/>" +
        "溯游从之　宛在水中坻<br/><br/>");

    add_tab("桃夭", "<br/>" +
        "桃之夭夭　灼灼其华<br/><br/>" +
        "之子于归　宜其室家<br/><br/>" +
        "桃之夭夭　有蕡其实<br/><br/>" +
        "之子于归　宜其家室<br/><br/>" +
        "桃之夭夭　其叶蓁蓁<br/><br/>" +
        "之子于归　宜其家人<br/><br/>");

    add_tab("关雎", "<br/>" +
        "关关雎鸠　在河之洲<br/><br/>" +
        "窈窕淑女　君子好逑<br/><br/>" +
        "参差荇菜　左右流之<br/><br/>" +
        "窈窕淑女　寤寐求之<br/><br/>" +
        "求之不得　寤寐思服<br/><br/>" +
        "悠哉悠哉　辗转反侧<br/><br/>" +
        "参差荇菜　左右采之<br/><br/>" +
        "窈窕淑女　琴瑟友之<br/><br/>" +
        "参差荇菜　左右芼之<br/><br/>" +
        "窈窕淑女　钟鼓乐之<br/><br/>");

    add_tab("采薇", "<br/>" +
        "采薇采薇　薇亦作止　曰归曰归　岁亦莫止　靡室靡家　玁狁之故　不遑启居　玁狁之故<br/><br/>" +
        "采薇采薇　薇亦柔止　曰归曰归　心亦忧止　忧心烈烈　载饥载渴　我戍未定　靡使归聘<br/><br/>" +
        "采薇采薇　薇亦刚止　曰归曰归　岁亦阳止　王事靡盬　不遑启处　忧心孔疚　我行不来<br/><br/>" +
        "彼尔维何　维常之华　彼路斯何　君子之车　戎车既驾　四牡业业　岂敢定居　一月三捷<br/><br/>" +
        "驾彼四牡　四牡骙骙　君子所依　小人所腓　四牡翼翼　象弭鱼服　岂不日戒　玁狁孔棘<br/><br/>" +
        "昔我往矣　杨柳依依　今我来思　雨雪霏霏　行道迟迟　载渴载饥　我心伤悲　莫知我哀<br/><br/>");
    
    add_tab("击鼓其镗　踊跃用兵", "<br/>" +
        "击鼓其镗　踊跃用兵　土国城漕　我独南行<br/><br/>" +
        "从孙子仲　平陈与宋　不我以归　忧心有忡<br/><br/>" +
        "爰居爰处　爰丧其马　于以求之　于林之下<br/><br/>" +
        "死生契阔　与子成说　执子之手　与子偕老<br/><br/>" +
        "于嗟阔兮　不我活兮　于嗟洵兮　不我信兮<br/><br/>");

    add_tab("斯干", "<br/>" +
        "秩秩斯干　幽幽南山　如竹苞矣　如松茂矣　兄及弟矣　式相好矣　无相犹矣<br/><br/>" +
        "似续妣祖　筑室百堵　西南其户　爰居爰处　爰笑爰语<br/><br/>" +
        "约之阁阁　椓之橐橐　风雨攸除　鸟鼠攸去　君子攸芋<br/><br/>" +
        "如跂斯翼　如矢斯棘　如鸟斯革　如翚斯飞　君子攸跻<br/><br/>" +
        "殖殖其庭　有觉其楹　哙哙其正　哕哕其冥　君子攸宁<br/><br/>" +
        "下莞上簟　乃安斯寝　乃寝乃兴　乃占我梦　吉梦维何　维熊维罴　维虺维蛇<br/><br/>" +
        "大人占之　维熊维罴　男子之祥　维虺维蛇　女子之祥<br/><br/>" +
        "乃生男子　载寝之床　载衣之裳　载弄之璋　其泣喤喤　朱芾斯皇　室家君王<br/><br/>" +
        "乃生女子　载寝之地　载衣之裼　载弄之瓦　无非无仪　唯酒食是议　无父母诒罹<br/><br/>");
    
    //初始化首个标签为选中标签
    switch_tab("关雎")
}