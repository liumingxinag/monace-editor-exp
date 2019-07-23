# -*- coding: utf-8 -*-
from turtle import *
from datetime import *
 
def Skip(step):
    penup()
    forward(step)
    pendown()
 
#建立钟表的外框
def setupClock(radius):
    reset()
    hideturtle()
    pensize(7)
    for i in range(120):
        Skip(radius)
        if i%5==0:
            forward(-15)
            Skip(-radius+15)
        else:
            dot(5)
            Skip(-radius)
        right(6)
    # 圆心
    dot(12)
 
#注册turtle形状，建立名字为name的形状
def makeHand(name,length):
    reset()
    Skip(-0.1*length)
    # 开始记录多边形的顶点
    begin_poly()
    forward(1.1*length)
    # 停止记录多边形的顶点,并与第一个顶点相连
    end_poly()
    #返回最后记录的多边形
    handForm=get_poly()
    #注册形状，命名为name
    register_shape(name,handForm)
 
 
def init():
    global secHand,minHand,hurHand,printer
    #重置turtle指针向北
    mode("logo")
    secHand=Turtle()
    makeHand("secHand", 170)
    secHand.shape("secHand")
    minHand=Turtle()
    makeHand("minHand", 130)
    minHand.shape("minHand")
    hurHand=Turtle()
    makeHand("hurHand", 90)
    hurHand.shape("hurHand")
    #shapesize第一个参数没看到什么用，第二个参数表示几倍的长度，第3个参数表示3倍的宽度
    #speed(0)是最快
    i = 0
    for hand in secHand, minHand, hurHand:
        i += 1
        hand.shapesize(1, 1, i)
        hand.speed(0)
    #建立并输出文字的turtle对象，printer对象只是显示文字不显示路径，所以一直是penup和hideturtle
    printer=Turtle()
    printer.hideturtle()
    printer.penup()
 
def Week(t):
    week=["星期一","星期二","星期三","星期四","星期五","星期六","星期七"]
    return week[t.weekday()]
 
def Day(t):
    return "%s %d %d" %(t.year,t.month,t.day)
 
def Tick():
    t=datetime.today()
    second=t.second#+t.microsecond*0.000001
    minute=t.minute+t.second/60.0
    hour=t.hour+t.minute/60.0
    secHand.setheading(second*6)
    minHand.setheading(minute*6)
    hurHand.setheading(hour*30)
 
    tracer(False)
    printer.fd(70)
    printer.write(Week(t),align="center",font=("Courier", 14, "bold"))
    printer.back(130)
    printer.write(Day(t),align="center",font=("Courier", 14, "bold"))
    printer.home()
    tracer(True)

    ontimer(Tick,100)#1000ms后继续调用Tick
 
 
def main():
    #关闭动画
    tracer(False)
    init()
    setupClock(200)
    #开启动画
    tracer(True)
    Tick()
    done()

main()
