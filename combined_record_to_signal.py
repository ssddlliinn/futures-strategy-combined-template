
from FinMind.data import DataLoader
import pandas as pd
import os
from pathlib import Path

class futures_Strategy:
    def __init__(self, price, combined_record) -> None: 
        self.price_data = price
        self.indicator = combined_record
        
        self.original_cash = 1200000
        self.current_asset = 1200000
        self.fee = 1
        self.point_value = 200
        self.margin = 500000
        self.hold_data = {
                'date':'',
                'signal':0,
                'strategy':0,
                'price':0,
                'adjust_cost':0,
                'lot':0,
                'start':False,
                'max':0}
        
    #要套用到indicator df的函數
    def add_signal(self, date, signal, strategy, PL, lot, total_cash):
        new_data = pd.DataFrame([[date, signal, strategy, PL, lot, total_cash]], columns=['date','signal','strategy','PL','lot','total_cash'])
        self.signal = pd.concat([self.signal, new_data], axis=0)
            
    def strategy_signal(self):
        self.price_data = self.price_data[['trade_price', 'diff']].copy()
        self.price_data = self.price_data.rename({'diff':'div'}, axis=1)
        #平倉時再紀錄 #再決定訊號函數內，平倉時新增資料
        #成本用調整後、平倉用扣除費用後
        #必備欄位in_date、out_date、signal、lot、cost、cover(點數紀錄)
        self.record = pd.DataFrame(columns=['in_date', 'out_date', 'signal', 'strategy', 'lot', 'cost', 'cover'])
        
        
        #每天都要記錄 #for迴圈跑過indicator決定訊號放入signal
        # 必備欄位date、signal、strategy、PL(點數)、lot、total_cash(現金)
        self.signal = pd.DataFrame()
        
        for index, row in self.price_data.iterrows():
            #根據hold_data內的資訊，建立策略機制
            if self.hold_data['signal'] == 0:
                #取資料
                date = row.name
                price = row['trade_price']
                # 設定進場條件
                # TODO:
                if (date in self.indicator['in_date'].values):
                    signal = self.indicator[self.indicator['in_date'] == date].signal.values[0]
                    strategy = self.indicator[self.indicator['in_date'] == date].strategy.values[0]
                    self.new_Recording(date, price, signal, strategy)
                else:
                    self.add_signal(date, 0, 0, 0, 0, self.current_asset)
                    
            else:
                #取資料
                date = row.name
                price = row['trade_price']
                adjust = row['div']
                lot = self.hold_data['lot']
                #遠近合約價差調整成本
                self.hold_data['adjust_cost'] -= adjust
                #計算當前獲利
                PL = (price - self.hold_data['adjust_cost']) * self.hold_data['signal']
                unrealized = self.current_asset + (PL*self.point_value*lot)
                #針對停利所算的歷史最高獲利點數
                self.hold_data['max'] = max(self.hold_data['max'], PL)
                # TODO: set about stop profit values(not necessary)
                
                #設定出場條件
                # TODO:
                if (date in self.indicator['out_date'].values):
                    signal = self.hold_data['signal']
                    strategy = self.hold_data['strategy']
                    self.cover_Recording(self.hold_data['date'],
                                         date, 
                                         signal,
                                         strategy,
                                         lot,
                                        self.hold_data['adjust_cost'],
                                        price,
                                        unrealized)
                    
                
                
                else:
                    self.add_signal(date, self.hold_data['signal'], self.hold_data['strategy'], PL, lot, unrealized)
                
        #所有日期跑完尚未平倉的話，直接平倉以計算交易KPI
        if self.hold_data['signal'] != 0:
            self.cover_Recording(self.hold_data['date'],
                                date,
                                self.hold_data['signal'],
                                self.hold_data['strategy'],
                                lot,
                                self.hold_data['adjust_cost'],
                                price,
                                unrealized)
        
    def KPI(self):
        if self.record.shape[0] == 0:
            output_KPI = {
                        'cum_return':-999,
                        'avg_return':-999,
                        'MDD':999,
                        'std_return':999,
                        'profit_factor':-999,
                        'win_lose_ratio':-999,
                        'expectation':-999,
                        'sharpe':-999,
                        'trade_times':0,
                        'win_rate':-999,
                        'max_continuous_wins':-999,
                        'max_continuous_loses':999,
                        }
        
            return output_KPI

        #(尚未確定)調整價格(額外費用)
        
        #計算return(報酬率)、return_cash(每筆獲利金額)欄位，加到record上面
        cost_per_lot = int(self.margin / self.point_value)
        self.record['return'] = ((self.record['cover'] - self.record['cost'])*self.record['signal']) / cost_per_lot
        self.record['return_cash'] = self.record['return'] * self.record['lot'] * cost_per_lot * self.point_value
        
        
        #計算平均獲利百分比、獲利標準差與夏普比率
        avg_return = round(self.record['return'].mean(), 4)
        std_return = round(self.record['return'].std(), 4)
        sharpe = round((avg_return - 0.01565) / std_return, 4)
        
        #計算交易次數與勝率
        trade_times = len(self.record)
        win_rate = round((self.record['return'] > 0).sum() / trade_times, 2)
        
        #計算累積獲利、MDD
        cum_return = round(self.signal.iloc[-1]['total_cash'] / self.original_cash, 4)
        mdd_df = pd.DataFrame()
        mdd_df['total_cash'] = self.signal['total_cash']
        mdd_df['historic_max'] = mdd_df['total_cash'].cummax()
        mdd_df['dropdown'] = round((mdd_df['total_cash'] / mdd_df['historic_max'])-1, 4)
        MDD = round(mdd_df['dropdown'].min(), 4)
        
        #計算獲利因子、賺賠比、期望值
        win_data = self.record[self.record['return'] > 0]
        lose_data = self.record[self.record['return'] <= 0]
        
        if len(lose_data) > 0:
            profit_factor = win_data['return_cash'].sum() / lose_data['return_cash'].sum()
            profit_factor = round(abs(profit_factor), 2)
            
            win_lose_ratio = win_data['return_cash'].mean() / lose_data['return_cash'].mean()
            win_lose_ratio = round(abs(win_lose_ratio), 2)
        else:
            profit_factor = '勝率100%'
            win_lose_ratio = '勝率100%'
        
        expectation = round(win_data['return_cash'].mean() * win_rate + lose_data['return_cash'].mean() * (1-win_rate), 0)
        
        #計算最大連續獲利/虧損次數
        max_continuous_wins = 0
        max_continuous_loses = 0
        times = 0
        
        for p in self.record['return_cash']:
            if p > 0 and times >= 0:
                times += 1
            elif p <= 0 and times <= 0:
                times -= 1
            elif p > 0 and times < 0:
                times = 1
            elif p < 0 and times > 0:
                times = -1
                
            if times > max_continuous_wins:
                max_continuous_wins = times
            elif times < max_continuous_loses:
                max_continuous_loses = times
                
        max_continuous_loses = abs(max_continuous_loses)
        
        output_KPI = {
        'cum_return':cum_return,
        'avg_return':avg_return,
        'MDD':MDD,
        'std_return':std_return,
        'profit_factor':profit_factor,
        'win_lose_ratio':win_lose_ratio,
        'expectation':expectation,
        'sharpe':sharpe,
        'trade_times':trade_times,
        'win_rate':win_rate,
        'max_continuous_wins':max_continuous_wins,
        'max_continuous_loses':max_continuous_loses,
        }
    
        return output_KPI
    
    def new_Recording(self, date, price, signal, strategy):
        lot = self.current_asset // self.margin
        
        self.hold_data['date'] = date
        self.hold_data['signal'] = signal
        self.hold_data['strategy'] = strategy
        self.hold_data['price'] = price
        self.hold_data['adjust_cost'] = price
        self.hold_data['lot'] = lot
        
        self.add_signal(date, signal, strategy, 0, lot, self.current_asset)
    
    def cover_Recording(self, in_date, out_date, signal, strategy, lot, cost, cover, unrealized):
        if self.record.empty:
            index_count = 0
        else:
            index_count = self.record.index[-1] + 1
        
        #平倉時扣除所有手續費
        cost += (self.fee * signal)
        cover -= (self.fee * signal)
        unrealized -= (self.fee*2*lot*self.point_value)
        
        #記錄到record上(只有交易日)
        self.record.at[index_count, 'in_date'] = in_date
        self.record.at[index_count, 'out_date'] = out_date
        self.record.at[index_count, 'signal'] = signal
        self.record.at[index_count, 'strategy'] = strategy
        self.record.at[index_count, 'lot'] = lot
        self.record.at[index_count, 'cost'] = cost
        self.record.at[index_count, 'cover'] = cover
        
        #平倉時調整其他相關變數
        self.current_asset = unrealized
        self.add_signal(out_date, 0, 0, 0, 0, unrealized)
        self.hold_data = {
                'date':'',
                'signal':0,
                'strategy':0,
                'price':0,
                'adjust_cost':0,
                'lot':0,
                'start':False,
                'max':0}