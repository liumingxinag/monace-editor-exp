from turtle import *

# 原点

origin = (0, 100)

def skip(step):

    penup()

    forward(step)

    pendown()



 # 绘制表盘

def draw_clock(radius):

    # 绘制表盘刻度

    penup()

    color('black')

    setheading(90)

    goto(origin[0], origin[1])

    pensize(7)

    for i in range(120):

        skip(radius)

        if i % 10==0:

            forward(30)

            skip(-radius-30)

        elif i % 5==0:

            forward(10)

            skip(-radius-10)

        else:

            dot(5)

            skip(-radius)

        right(3)



    # 绘制表盘文字

    penup()

    fsize = 18

    pensize(5)

    radius -= fsize

    goto(origin[0] - 6, origin[1] - 15)

    for i in range(120):

        skip(radius)

        if i % 10==0:            

            n = int(i * 2 / 10)

            write(str(n), align="left", font=("Courier", fsize, "bold"))

        skip(-radius)

        right(3)



    return radius + fsize + 30





# 绘制时段

def draw_tim_range(radius):  

    clear()

    hideturtle()

 

    speed(0)

    tracer(False)

    radius = draw_clock(radius) + 20

    tracer(True)

    speed(10)



    nodes = [[15, 9, 'red'], [7, 21, 'blue']]



    print('请输入两个时间段(24以内的正整数)')

    nodes[0][0] = abs(int(input("开始时间1: ")) % 24)

    nodes[0][1] = abs(int(input("结束时间2: ")) % 24)

    print('')

    nodes[1][0] = abs(int(input("开始时间1: ")) % 24)

    nodes[1][1] = abs(int(input("结束时间2: ")) % 24)    

    print('')

    print('时段1:', nodes[0][0:2])

    print('时段2:', nodes[1][0:2])



    pensize(10)

    d = -360 / 24

    for node in nodes:

        penup() 

        goto(origin[0], origin[1] + radius)

        setheading(180)



        circle(radius, d * node[0])



        pendown()

        color(node[2])

        circle(radius, d * ((24 + node[1] - node[0]) % 24))

        penup() 

        radius += 30



    input()

    print('')

    print('------------------------------------------')

    print('')

    





def main():

    while True:       

        draw_tim_range(120)





main()

