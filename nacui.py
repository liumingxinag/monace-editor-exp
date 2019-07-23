import talib, time, datetime
from dateutil import parser


#################################################################################
import winsound
def playsound(wavfile=''):
    if BarStatus() != 2: 
        return
    if len(wavfile) > 0:
        winsound.PlaySound(wavfile, winsound.SND_FILENAME or winsound.SND_ASYNC)
    else:
        winsound.MessageBeep(winsound.MB_ICONHAND)
        

#################################################################################
# 当前浮点时间
def current_tim():
    return float(time.strftime("0.%H%M%S", time.localtime()))

# 返回时间节点状态，0：当前节点， 1：下一个节点，-1：历史节点
def node_state(tim, begin, end):
    t = tim
    e = end
    if end < begin:
        if tim < end:
            tim += 0.24
        end += 0.24

    if begin <= tim <= end:
        return 0
    elif t > e:
        return 1
    else: # if t < e:
        return -1

# 获得当前或下一个交易时段的时间节点
# {'begin':起始时间, 'end':结束时间, 'type':节点类型, 'enter':当前时间是否位于该时间节点中, 'state':该时段交易状态}
# type： F当天第一个节点， M盘中的中间节点， L当天最后一个节点
def curr_time_node(code):
    tim = current_tim()
    
    i = 0
    nstate = -1
    tim1 = tim2 = 0.0
    count = GetSessionCount(code)
    for i in range(0, count):
        b = GetSessionStartTime(code, i)
        e = GetSessionEndTime(code, i)
        nstate = node_state(tim, b, e)
        if nstate < 0:
            break
        tim1 = b
        tim2 = e
        if nstate == 0:
            break

    # 非交易时间   
    if abs(tim1 - tim2) < 0.0000001:
        return {'begin':-1, 'end':-1, 'type':'', 'enter':False, 'state':None}
    # 交易时间
    else:
        tp = 'FL' if count == 1 else ('F' if i == 0 else ('L' if i == count - 1 else 'M'))
        return {'begin':tim1, 'end':tim2, 'type':tp, 'enter':True if nstate == 0 else False, 'state':3}

# 套利交叉时段，有可能产生两个时段，需要进一步判断当前时间属于哪个时段
# {'begin':起始时间, 'end':结束时间, 'type':节点类型, ''enter':当前时间是否位于该时间节点中, 'state':该时段交易状态}
def spd_time_node(code1, code2):
    tim = current_tim()
    node1 = curr_time_node(code1)
    node2 = curr_time_node(code2)
    
    # 两段交集
    if  node_state(node2['begin'], node1['begin'], node1['end']) == 0 or \
        node_state(node2['end'], node1['begin'], node1['end']) == 0 or \
        node_state(node1['begin'], node2['begin'], node2['end']) == 0 or \
        node_state(node1['end'], node2['begin'], node2['end']) == 0:

        if node_state(tim, node1['begin'], node2['end']) >= 0:
            return {'begin':node1['begin'], 'end':node2['end'], 'type':node1['type']+node2['type'], 'enter':node1['enter'] and node2['enter'], 'state':3}
        elif node_state(tim, node2['begin'], node1['end']) >= 0:
            return {'begin':node2['begin'], 'end':node1['end'], 'type':node1['type']+node2['type'], 'enter':node1['enter'] and node2['enter'], 'state':3}
        else:
            LogError('spd_time_node get faild!')  
            return {'begin':-1, 'end':-1, 'type':'', 'enter':False, 'state':None}
    # 无交集或一段交集          
    else:
        if node1['begin'] < node1['end']:
            node1['end'] += 0.24
        if node2['begin'] < node2['end']:
            node2['end'] += 0.24
            
        tim1 = node1['begin'] if node1['begin'] > node2['begin'] else node2['begin']
        tim2 = node1['end'] if node1['end'] < node2['end'] else node2['end']
        if tim2 < tim1:
            return {'begin':-1, 'end':-1, 'type':'', 'enter':False, 'state':None}
        else:
            if tim2 >= 0.24:
                tim2 -= 0.24
            return {'begin':tim1, 'end':tim2, 'type':node1['type']+node2['type'], 'enter':node1['enter'] and node2['enter'], 'state':3}

# 浮点时间转字符串时间
def ftime_to_stime(tim):
    num = int(tim * 1000000)
    return '%02d:%02d:%02d' % (num // 10000, int(num // 100) % 100, num % 100)


#################################################################################
# 是否达到停板价附近，回测实盘自适应
def is_limit(code, diff_dot):
    if  BarStatus(code) == 2:
        return False
    else:
        return Q_UpLimit(code) - Q_BidPrice(code) <= diff_dot * PriceTick() or \
            Q_AskPrice(code) - Q_DownLimit(code) <= diff_dot * PriceTick()

# 获得买价 bid + tick，回测实盘自适应
def bid_price(code, outdot = 0):
    if BarStatus(code) == 2:
        if Q_BidPrice(code) == 0:
            return Q_Close(code)
        elif Q_BidPrice(code) + PriceTick() * outdot > Q_UpperLimit(code):
            return Q_UpperLimit(code)
        else:
            return Q_BidPrice(code) + PriceTick(code) * outdot
    else:
        return Open(code)[-1]

# 获得卖价 ask - tick，回测实盘自适应
def ask_price(code, outdot = 0):    
    if BarStatus(code) == 2:
        if Q_AskPrice(code) == 0:
            return Q_Close(code)
        elif Q_AskPrice(code) - PriceTick(code) * outdot < Q_LowLimit(code):
            return Q_LowLimit(code)
        else:
            return Q_AskPrice(code) - PriceTick(code) * outdot
    else:
        return Open(code)[-1]

# 净持仓量，回测实盘自适应
def net_position(code):
    return A_TotalPosition(code) if BarStatus(code) == 2 else MarketPosition(code)

# 下单操作，回测实盘自适应
def send_order(qty, price, direct, offset, ordertype = '2', validtype = '0', hedge = 'T', code = '', user = ''):
    if BarStatus() == 2:
        if code == '':
            code = Symbol()
        if user == '':
            user = A_AccountID()
        ret, msg = A_SendOrder(user, code, ordertype, validtype, direct, offset, hedge, price, qty)
        if ret == 0:
            return msg
        else:
            LogError(ret, msg)
            return ''
    else:
        if direct == Enum_Buy():
            if offset != Enum_Exit() and offset != Enum_ExitToday():
                Buy(qty, price)
            else:
                BuyToCover(qty, price)
        else:
            if offset != Enum_Exit() and offset != Enum_ExitToday():
                SellShort(qty, price)
            else:
                Sell(qty, price) 
        return '0' 

# 清仓，回测实盘自适应
def clear_position(code):
    all_qty = A_BuyPosition(code)
    if all_qty == 0:
        if 'SHFE' in code:
            day_qty = A_TodayBuyPosition(code)
            his_qty = all_qty - day_qty
            if day_qty > 0:
                send_order(day_qty, bid_price(code), Enum_Sell(), Enum_ExitToday())
            if his_qty > 0:
                send_order(his_qty, bid_price(code), Enum_Sell(), Enum_Exit())
        else:
            send_order(all_qty, bid_price(code), Enum_Sell(), Enum_Exit())

    all_qty = A_SellPosition(code)
    if all_qty == 0:
        if 'SHFE' in code:
            day_qty = A_TodaySellPosition(code)
            his_qty = all_qty - day_qty
            if day_qty > 0:
                send_order(day_qty, ask_price(code), Enum_Buy(), Enum_ExitToday())
            if his_qty > 0:
                send_order(his_qty, ask_price(code), Enum_Buy(), Enum_Exit())
        else:
            send_order(all_qty, ask_price(code), Enum_Buy(), Enum_Exit())

# 净盈亏，回测实盘自适应
def profit(code):
    if BarStatus(code) == 2:
        return A_CoverProfit(code) + A_ProfitLoss(code) - A_Cost(code)
    else:
        return NetProfit(code) + FloatProfit(code) - TradeCost(code)

