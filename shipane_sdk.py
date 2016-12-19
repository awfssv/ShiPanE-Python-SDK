# -*- coding: utf-8 -*-

import copy
import json
import requests
from six.moves.urllib.parse import urlencode
import time
import threading


class Portfolio_spe(object):
    def __init__(self):
        self._available_cash =0 #可用资金
        self._positions = {}  # 多单的仓位, 一个 dict, key 只证券代码, value 是 Position对象
        self._total_value =0 # 总的权益, 包括现金, 保证金, 仓位的总价值, 可用来计算收益
        self._returns = 0 # 总权益的累计收益
        self._positions_value = 0 # 持仓价值, 股票基金才有持仓价值, 期货为0
        self._updatetime=0  # 标记最后一次更新成功时间戳
        
    @property  
    def available_cash(self):  
        return self._available_cash  

    @available_cash.setter  
    def available_cash(self, value):
        self._available_cash = value  
       
    @property  
    def positions(self):  
        return self._positions  
 
    @positions.setter  
    def positions(self, value):  
        self._positions = value  
       
    @property  
    def total_value(self):
        return self._total_value
    
    @total_value.setter
    def total_value(self, value):
        self._total_value = value  
       
    @property  
    def returns(self):  
        return self._returns  
 
    @returns.setter  
    def returns(self, value):  
        self._returns = value  
       
    @property  
    def positions_value(self):  
        return self._positions_value  
 
    @positions_value.setter  
    def positions_value(self, value):  
        self._positions_value = value  
       
    @property  
    def updatetime(self):  
        return self._updatetime  
 
    @updatetime.setter  
    def updatetime(self, value):  
        self._updatetime = value
        
class Client(object):
    def __init__(self, **kwargs):
        self._host = kwargs.pop('host', 'localhost')
        self._port = kwargs.pop('port', 8888)
        self._key = kwargs.pop('key', '')
        self._title = kwargs.pop('title', 'monijiaoyi')
        self._account = kwargs.pop('account', '')
        self._timeout = kwargs.pop('timeout', (5.0, 10.0))
        self.portfolio_spe = Portfolio_spe()
        
        self.get_positions(True)
        #Timer（定时器）是Thread的派生类，
        #用于在指定时间后调用一个方法。
        #timer = threading.Timer(10, self.get_positions(True))
        #timer.start()
        
    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        self._port = value

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def account(self):
        return self._account

    @account.setter
    def account(self, value):
        self._account = value

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value
        
    def get_account(self):
        return requests.get(self.__create_url('accounts'), timeout=self._timeout)

    def get_positions(self, forceupdate=False):
        if(forceupdate==False): return self.portfolio_spe
        tmpPortfolio_spe = Portfolio_spe()
        try:
            response = requests.get(self.__create_url('positions'), timeout=self._timeout)
            #return response
            if response.status_code==200:
                resjson = json.loads(response.text)
                tmpPortfolio_spe.available_cash = float(resjson['subAccounts'][u'人民币'][u'可用']) #可用资金
                tmpPortfolio_spe.total_value = float(resjson['subAccounts'][u'人民币'][u'总资产']) # 总的权益, 包括现金, 保证金, 仓位的总价值, 可用来计算收益
                tmpPortfolio_spe.returns = float(resjson['subAccounts'][u'人民币'][u'盈亏']) # 总权益的累计收益
                tmpPortfolio_spe.positions_value = float(resjson['subAccounts'][u'人民币'][u'参考市值']) # 持仓价值, 股票基金才有持仓价值, 期货为0
                tmpPortfolio_spe.positions = {}  # 多单的仓位, 一个 dict, key 只证券代码, value 是 Position对象
                lstCol=resjson['dataTable']['columns']
                dicCol={}
                for i in range(len(lstCol)): dicCol[lstCol[i]]=i
                if(resjson['dataTable']['rows'][0][dicCol[u'持仓量']] != ''):
                    for stock in resjson['dataTable']['rows']:
                        security=stock[dicCol[u'证券代码']]
                        tmpPortfolio_spe.positions[security]={}
                        tmpPortfolio_spe.positions[security]['price']=float(stock[dicCol[u'当前价']])  #当前价
                        tmpPortfolio_spe.positions[security]['avg_cost']=float(stock[dicCol[u'成本价']])  #持仓成本（均价）
                        tmpPortfolio_spe.positions[security]['total_amount']=int(float(stock[dicCol[u'持仓量']]))  #总持仓
                        tmpPortfolio_spe.positions[security]['closeable_amount']=int(float(stock[dicCol[u'可卖数量']]))  #可卖数量
                        tmpPortfolio_spe.positions[security]['value'] = float(stock[dicCol[u'最新市值']])   #最新市值
                else:
                    print('WARNNING:实盘未持仓!')
                tmpPortfolio_spe.updatetime=time.time()  #记录刷新成功时间
                self.portfolio_spe = tmpPortfolio_spe
            else:
                print ('[实盘易]ERROR:无法获取持仓信息,' + response.text)
        except Exception as e:
            print ('[实盘易]ERROR: 获取持仓信息异常：' + str(e))
        return self.portfolio_spe
            
    def buy(self, symbol, price, amount):
        return self.__execute('BUY', symbol, price, amount)

    def sell(self, symbol, price, amount):
        return self.__execute('SELL', symbol, price, amount)

    def execute(self, order_type, symbol, price, amount):
        return self.__execute(order_type, symbol, price, amount)

    def cancel(self, order_id):
        return requests.delete(self.__create_order_url(order_id), timeout=self._timeout)

    def cancel_all(self):
        return requests.delete(self.__create_order_url(), timeout=self._timeout)

    def query(self, navigation):
        return requests.get(self.__create_url('', navigation=navigation), timeout=self._timeout)

    def __execute(self, order_type, symbol, price, amount):
        print('[SHIPANE] Send Order:'.encode('gbk'), {'orderType': order_type, 'symbol': symbol, 'price': price, 'amount': amount})
        return requests.post(self.__create_order_url(),
                             json={'orderType': order_type, 'symbol': symbol, 'price': price, 'amount': amount},
                             timeout=self._timeout)

    def __create_order_url(self, order_id=None, **params):
        return self.__create_url('orders', order_id, **params)

    def __create_url(self, resource, resource_id=None, **params):
        client_param = self.__create_client_param()
        all_params = copy.deepcopy(params)
        all_params.update(client=client_param, key=self._key)
        if resource_id is None:
            path = '/{}'.format(resource)
        else:
            path = '/{}/{}'.format(resource, resource_id)

        return '{}{}?{}'.format(self.__create_base_url(), path, urlencode(all_params))

    def __create_base_url(self):
        return 'http://' + self._host + ':' + str(self._port)

    def __create_client_param(self):
        client_param = ''
        if self._title:
            client_param += 'title:' + self._title
        if self._account:
            if client_param:
                client_param += ','
            client_param += 'account:' + self._account
        return client_param

# From joinquant/executor.py
try:
    from shipane_sdk.client import Client
except:
    pass

try:
    from kuanke.user_space_api import *
except:
    pass

class JoinQuantExecutor(object):
    def __init__(self, Context, **kwargs):
        if 'log' in globals():
            self._log = log
        else:
            import logging
            self._log = logging.getLogger()
        self._client = Client(**kwargs)
        self._order_id_map = dict()
        
        #data= get_current_data()
        #self._log.info(data['000001.XSHE'].close)
        self._send2weixin = True  #是否推送微信通知
        self._context = Context
        self._order2spe = False   #是否同步订单到实盘易
        
    @property
    def client(self):
        return self._client
        
    @property
    def send2weixin(self):
        return self._send2weixin

    @send2weixin.setter
    def send2weixin(self, value):
        self._send2weixin = value
        
    @property
    def client(self):
        return self._client
    
    @property
    def order2spe(self):
        return self._order2spe
    
    @order2spe.setter
    def order2spe(self, value):
        self._order2spe=value

    def get_total_value_rate(self):
        capital_shipan = self._client.portfolio_spe.total_value
        capital_simulation = self._context.portfolio.total_value
        rate = capital_shipan/capital_simulation #实虚盘资金比率: 实盘/模拟盘
        return rate
    
    #order_spe: 按股数交易
    #security: 股票代码
    #numb: 交易数量(股数）
    def order_spe(self, security, amount):
        # 保存 order 对象
        order_ = order(security, amount)
        if(self.order2spe and order_ is not None):
            self.execute(order_)
        
    # order by value
    def order_value_spe(self, security, value):
        order_ = order_value(security, value)
        if(self.order2spe and order_ is not None):
            self.execute(order_)

    #order_target_spe: 目标股数(实际下单：目标数量-持仓数量)
    #security: 股票代码
    #numb: 目标持有数量（股数）
    def order_target_spe(self, security, amount):
        # 保存 order 对象
        order_ = order_target(security, amount)
        if(self.order2spe and order_ is not None):
            self.order_to_spe_by_amount(order_)
        
    def order_target_value_spe(self, security, value):
        order_ = order_target_value(security, value)
        if(self.order2spe and order_ is not None):
            self.order_to_spe_by_amount(order_)
        
    def order_to_spe_by_amount(self, order_):
        if(order_ is not None):
            if(order_.security[:6] in self._client.portfolio_spe.positions.keys()):
                total_amount_in_spe = self._client.portfolio_spe.positions[order_.security[:6]]['total_amount']
            else:
                total_amount_in_spe =0
                
            changeamount = order_.amount - total_amount_in_spe/self.get_total_value_rate()  #目标量-已持仓量，将实盘持仓放大到与模拟盘相同倍数

            if(changeamount>0):
                order_.is_buy = True
                order_.amount = changeamount
            else:
                order_.is_buy = False
                order_.amount = -changeamount
            # 实盘易依据聚宽的 order 对象下单
            self.execute(order_)

    def execute(self, order):
        if order is None:
            self._log.info('[实盘易] 委托为空，忽略下单请求')
            return
        
        # 5分钟未刷新账户数据，下单前先刷新
        #if(time.time()-self._client.portfolio_spe.updatetime>300):
        self._client.get_positions(True)
        try:
            if order.is_buy:
                capital_shipan = self._client.portfolio_spe.total_value
                capital_simulation = self._context.portfolio.total_value
                rate = capital_shipan/capital_simulation #实虚盘的可用资金比率
                response = self._client.buy(order.security, order.price, int(order.amount*rate/100)*100)
            else:
                capital_shipan = self._client.portfolio_spe.total_value
                capital_simulation = self._context.portfolio.total_value
                #capital_shipan = self._client.portfolio_spe.positions[order.security[:6]]['closeable_amount']
                #capital_simulation = self._context.portfolio.positions[order.security].closeable_amount
                rate = capital_shipan/capital_simulation #实虚盘的可卖持仓比率
                order.amount=int(round(order.amount*rate))   #四舍五入取整
                if(abs(capital_shipan-order.amount)<100): order.amount=capital_shipan  #实际持仓量<100则清仓
                self._log.info(capital_shipan, capital_simulation, order.amount)
                response = self._client.sell(order.security, order.price, order.amount)

            if response is not None:
                self._log.info(u'[实盘易] 回复如下：\nstatus_code: %d\ntext: %s', response.status_code, response.text)
                #self.send2message('I', '[实盘易]下单成功：' + response.text)
            else:
                self._log.error('[实盘易] 未回复')
                self.send2message('E', "[实盘易]下单异常：" + response.text)

            if response is None:
                return None

            if response.status_code == 200:
                self._order_id_map[order.order_id] = response.json()['id'];
            else:
                self.send2message('E', "[实盘易]下单异常：" + response.text)

            return response
        except Exception as e:
            self._log.error("[实盘易] 下单异常：" + str(e))
            self.send2message('E', "[实盘易]下单异常：" + str(e))

    def cancel(self, order):
        if order is None:
            self._log.info('[实盘易] 委托为空，忽略撤单请求')
            return

        try:
            order_id = order if isinstance(order, int) else order.order_id
            if order_id in self._order_id_map:
                return self._client.cancel(self._order_id_map[order_id])
            else:
                self._log.warn('[实盘易] 未找到对应的委托编号')
        except Exception as e:
            self._log.error("[实盘易] 撤单异常：" + str(e))
            self.send2message('E', "[实盘易]下单异常：" + str(e))
            
    #推送消息到微信
    def send2message(self,errType, message):
        if(self._send2weixin):
            send_message(str(message), channel='weixin')   #在模拟交易才可发送
