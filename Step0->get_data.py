from realtrade.all_common.gateway.private_enum import *
import pandas as pd
import csv
import os
import time
import datetime
from realtrade.all_common.util.utility import load_json_info

limit_dic = {'okex': 100, 'binance': 200, 'mexc': 300, 'ascendex': 200, 'kucoin': 200, 'ftx': 500, 'gate': 100,
             'coinbase': 100}
# 逆向新增--适用于binance/okex/mexc(future_u)/ascendex/kucoin/ftx
reverse_list = ['binance_spot', 'binance_future_u', 'binance_future_coin', 'okex_spot', 'okex_future_u',
                'okex_future_coin',
                'mexc_future_u', 'ascendex_spot', 'ascendex_future_u', 'kucoin_spot', 'kucoin_future_u',
                'kucoin_future_coin',
                'ftx_spot', 'ftx_future_u']
# 正向新增--适用于gate/coinbase/mexc(spot)
obverse_list = ['gate_spot', 'gate_future_u', 'coinbase_spot', 'mexc_spot']
time_dic = {'1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min', '1h': '1hour', '4h': '4hour', '1d': '1day'}


class reverse_order_increment(object):
    # 分离symbol要素
    def split_name(self, name):
        base_asset = name.split('-')[0]
        asset_type = None
        if '_' in name:
            quote_asset = name.split('-')[1].split('_')[0]
            asset_type = name.split('_')[1]
        else:
            quote_asset = name.split('-')[1]
        if asset_type:
            return base_asset, quote_asset, asset_type
        else:
            return base_asset, quote_asset

    def get_exchange_format(self, exchange_name, market_type):
        path = f"exchange_info_{exchange_name}"
        format_text = load_json_info(path)[f"{exchange_name}_{market_type}"]["format"]
        return format_text

    def make_trade_name(self, format_rule, elements):

        if len(elements) == 2:
            trade_name = format_rule.format(elements[0], elements[1])
        else:
            trade_name = format_rule.format(elements[0], elements[1], elements[2])
            if 'SWAP' in trade_name:
                if not elements[2] == 'PERP':
                    trade_name.replace('SWAP', elements[2])
        return trade_name

    def get_data_write_csv(self, http_client, symbol, period, start_time, end_time, data_history_root, get_limit,
                           exchange_name, market_type):
        if 'm' in period.value.lower():
            sec_time_interval = int(period.value.split('m')[0]) * 60
        elif 'h' in period.value.lower():
            sec_time_interval = int(period.value.split('h')[0]) * 60 * 60
        elif 'd' in period.value.lower():
            sec_time_interval = int(period.value.split('d')[0]) * 60 * 60 * 24
        else:
            print('周期输入错误，无法获取K线')
            return
        local_symbol_name = symbol
        elements = self.split_name(name=symbol)
        format_rule = self.get_exchange_format(exchange_name=exchange_name, market_type=market_type)
        trade_name = self.make_trade_name(format_rule=format_rule, elements=elements)

        # 检查文件夹是否存在，不存在则创建品种文件夹
        file_dir_path = data_history_root + local_symbol_name
        if not os.path.exists(file_dir_path):
            os.makedirs(file_dir_path)
        file_name = f"{file_dir_path}/{local_symbol_name}({time_dic[period.value]}).csv"

        # 获取方式：倒叙获取-----------
        # 处理开始时间
        data_start_time = int(time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S")))
        if end_time:
            data_end_time = int(time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S")))
        else:
            data_end_time = int(time.mktime(time.strptime(str(datetime.datetime.now()), "%Y-%m-%d %H:%M:%S.%f")))
        # 以现在为基准往前倒推最大间隔

        first_k = 0
        count = 0
        blank_dic = {'datetime': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
        re_df = pd.DataFrame(blank_dic)
        # 循环获取K线，倒叙获取
        while True:
            if first_k == 0:
                end_time = data_end_time
                first_k = 1
            if end_time < data_start_time:
                break
            re = http_client.get_kline(symbol=trade_name, interval=period, end_time=end_time)
            print(re)
            # 开始处理数据
            if re['success']:
                if len(re['data']) > 0:
                    count = 1
                    re_df = re_df.append(re['data'])
                    # 以最小的时间作为结束时间，往前继续推一个最小间隔
                    end_time = int(time.mktime(time.strptime(str(re['data']['datetime'].iloc[0]), "%Y-%m-%d %H:%M:%S")))
                    if len(re['data']) < get_limit * (1 - 0.1):
                        break
                else:
                    if count == 0:
                        print('当前时间段没有K线数据，自动向后推一根K线')
                        end_time += sec_time_interval
                    else:
                        break

            else:
                if re['message'] == '尝试超过错误':
                    try:
                        os.rmdir(file_dir_path)
                        return
                    except:
                        return
                elif re['message'] == 'no data':
                    break

        # 按时间排序及去重
        re_df = re_df.sort_values(by='datetime')
        re_df = re_df.drop_duplicates(subset=['datetime'], keep='first')
        re_df.to_csv(file_name, index=0, header=0)


class obverse_order_increment(object):

    # 分离symbol要素
    def split_name(self, name):
        base_asset = name.split('-')[0]
        asset_type = None
        if '_' in name:
            quote_asset = name.split('-')[1].split('_')[0]
            asset_type = name.split('_')[1]
        else:
            quote_asset = name.split('-')[1]
        if asset_type:
            return base_asset, quote_asset, asset_type
        else:
            return base_asset, quote_asset

    def get_exchange_format(self, exchange_name, market_type):
        path = f"./quant/realtrade/all_config_info/exchange_info/exchange_info_{exchange_name}"
        format_text = load_json_info(path)[f"{exchange_name}_{market_type}"]["format"]
        return format_text

    def make_trade_name(self, format_rule, elements):
        if len(elements) == 2:
            trade_name = format_rule.format(elements[0], elements[1])
        else:
            trade_name = format_rule.format(elements[0], elements[1], elements[2])
            if 'SWAP' in trade_name:
                if not elements[2] == 'PERP':
                    trade_name.replace('SWAP', elements[2])
        return trade_name

    def get_data_write_csv(self, http_client, symbol, period, start_time, end_time, data_history_root, get_limit,
                           exchange_name, market_type):
        if 'm' in period.value.lower():
            sec_time_interval = int(period.value.split('m')[0]) * 60
        elif 'h' in period.value.lower():
            sec_time_interval = int(period.value.split('h')[0]) * 60 * 60
        elif 'd' in period.value.lower():
            sec_time_interval = int(period.value.split('d')[0]) * 60 * 60 * 24
        else:
            print('周期输入错误，无法获取K线')
            return
        local_symbol_name = symbol
        elements = self.split_name(name=symbol)
        format_rule = self.get_exchange_format(exchange_name=exchange_name, market_type=market_type)
        trade_name = self.make_trade_name(format_rule=format_rule, elements=elements)

        # 检查文件夹是否存在，不存在则创建品种文件夹
        file_dir_path = data_history_root + local_symbol_name
        if not os.path.exists(file_dir_path):
            os.makedirs(file_dir_path)
        file_name = f"{file_dir_path}\\{local_symbol_name}({time_dic[period.value]}).csv"

        # 获取方式：倒叙获取-----------
        # 处理开始时间
        data_start_time = int(time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S")))
        if end_time:
            data_end_time = int(time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S")))
        else:
            data_end_time = int(time.mktime(time.strptime(str(datetime.datetime.now()), "%Y-%m-%d %H:%M:%S.%f")))
        # 以现在为基准往前倒推最大间隔

        s_time = int(time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S")))
        e_time = s_time + get_limit * sec_time_interval
        # 循环获取K线，倒叙获取
        count = 0
        blank_dic = {'datetime': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': [], 'trade_money': []}
        re_df = pd.DataFrame(blank_dic)
        while True:
            re = http_client.get_kline(symbol=trade_name, interval=period, start_time=s_time + 1, end_time=e_time)
            print(re)
            if re['success']:
                if len(re['data']) > 0:
                    count += 1
                    re_df = re_df.append(re['data'])
                    # 以最小的时间作为结束时间，往前继续推一个最小间隔
                    s_time = int(time.mktime(time.strptime(str(re['data']['datetime'].iloc[-1]), "%Y-%m-%d %H:%M:%S")))
                    e_time = s_time + get_limit * sec_time_interval
                    if s_time > data_end_time:
                        break
                    if len(re['data']) < get_limit * (1 - 0.1):
                        if count > 2:
                            break
                else:
                    if count == 0:
                        print('当前时间段没有K线数据，自动向后推一根K线')
                        s_time += sec_time_interval
                        e_time = s_time + get_limit * sec_time_interval
                    else:
                        if len(re['data']) < get_limit * (1 - 0.1):
                            if count == 1:
                                s_time += sec_time_interval * get_limit
                                e_time = s_time - get_limit * sec_time_interval
                            else:
                                break
            else:
                if re['message'] == 'no data':
                    try:
                        os.rmdir(file_dir_path)
                        return
                    except:
                        return

        # 按时间排序及去重
        re_df = re_df.sort_values(by='datetime')
        re_df = re_df.drop_duplicates(subset=['datetime'], keep='first')
        re_df.to_csv(file_name, index=0, header=0)


if __name__ == '__main__':
    # 设定交易所名称
    exchange_name = 'binance'
    # 设置市场类型
    market_type = 'spot'
    # 交易所币种名称分隔符号
    # symbol_list = ['BTC-USDT']
    symbol_list = ['BTC-USDT', 'ETH-USDT', 'XRP-USDT', 'AVAX-USDT', 'FTM-USDT', 'SOL-USDT', 'BNB-USDT',
                   'GALA-USDT', 'DOGE-USDT', 'SHIB-USDT', 'NEAR-USDT', 'ADA-USDT', 'DOT-USDT', 'MATIC-USDT',
                   'LINK-USDT', 'SAND-USDT', 'LTC-USDT', 'MANA-USDT', 'GRT-USDT','ONE-USDT', 'FIL-USDT',
                   'ETC-USDT', 'BCH-USDT', 'CRV-USDT']
    # period_list = [Interval.MINUTE_1, Interval.MINUTE_5, Interval.MINUTE_15, Interval.MINUTE_30, Interval.HOUR_1, Interval.HOUR_4, Interval.DAY_1]
    period_list = [Interval.MINUTE_5]
    # 开始日期，在这里修改
    start_time = '2017-01-01 08:00:00'
    # start_time = '2022-03-31 08:00:00'
    # 结束日期，在这里修改，默认None
    end_time = '2022-12-06 08:00:00'
    # 历史数据存放根目录
    # data_history_root = f"D:\\quant\\data_history\\DIGICCY_data\\{exchange_name}_data\\{market_type}_data\\"
    data_history_root = f"./data/{exchange_name}_data/{market_type}_data/"
    # 交易所单次获取数据上限
    get_limit = limit_dic[exchange_name]
    # 代理设置
    # proxy_host = "192.168.1.31"
    # proxy_port = 7078
    proxy_host = '192.168.1.161'
    proxy_port = ''
    # 调用通讯文件
    # logic_http = getattr(__import__(f"realtrade.all_common.gateway.{exchange_name}_http", fromlist=(f"gateway.{exchange_name}_http",)), f"{exchange_name}_{market_type}_http")
    logic_http = getattr(
        __import__(f"ml_project_temp.{exchange_name}_http", fromlist=(f"gateway.{exchange_name}_http",)),
        f"{exchange_name}_{market_type}_http")
    http_client = logic_http(key='6w1+NKL1nt72p0XOlA1J5g==', secret='QRGDKKBPXFFQOMN2H5FIR5MXLVVK', special_key='test',
                             proxy_host=proxy_host, proxy_port=proxy_port)
    # 调用class代码
    reverse = reverse_order_increment()
    obverse = obverse_order_increment()
    # 匹配K线获取模式
    if f"{exchange_name}_{market_type}" in obverse_list:
        running = obverse
    elif f"{exchange_name}_{market_type}" in reverse_list:
        running = reverse
    else:
        running = None
        print('输入的交易所和市场类型不正确，请参考支持列表')
        exit()

    for symbol in symbol_list:
        for period in period_list:
            print(f"开始抓取 {symbol}-{period.value}")
            running.get_data_write_csv(http_client=http_client,
                                       symbol=symbol,
                                       period=period,
                                       start_time=start_time,
                                       end_time=end_time,
                                       data_history_root=data_history_root,
                                       get_limit=get_limit,
                                       exchange_name=exchange_name,
                                       market_type=market_type)
