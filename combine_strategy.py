
import os
import sys
from pathlib import Path

g_path = Path(__file__).parent
if str(g_path) not in sys.path:
    sys.path.append(str(g_path))
    
main_path = Path(__file__).parent.parent
if str(main_path) not in sys.path:
    sys.path.append(str(main_path))
    

from combined_record_to_signal import futures_Strategy
import pandas as pd
from datetime import datetime

def combine_record(main, second):
    main['in_date'] = pd.to_datetime(main['in_date'])
    main['out_date'] = pd.to_datetime(main['out_date'])
    second['in_date'] = pd.to_datetime(second['in_date'])
    second['out_date'] = pd.to_datetime(second['out_date'])
    
    main['strategy'] = 1
    
    for index, row in second.iterrows():
        if (((main['in_date'] <= row['in_date']) & (row['in_date'] <= main['out_date'])).any() or 
            ((main['in_date'] <= row['out_date']) & (row['out_date'] <= main['out_date'])).any()):
            continue
        else:
            row['strategy'] = 2
            new_df = pd.DataFrame([row])
            main = pd.concat([main, new_df])
    main = main.sort_values(by=['in_date'])
    main = main.reset_index(drop=True)
    main = main.drop(['lot'], axis=1)
    return main

#only accepts strategy classes with finished strategy_signal call
def main(fs1, fs2):
    combined = combine_record(fs1.record.copy(), fs2.record.copy())

    combined_strategy = futures_Strategy(fs1.price_data, combined)
    combined_strategy.strategy_signal()
    
    return combined_strategy


if __name__ == "__main__":
    
    #TODO: import two different strategy objects
    from '.strategy_class import get_all_data
    from '.strategy_class import futures_Strategy as fs1
    from '.strategy_class import futures_Strategy as fs2
    #TODO: change the other data file name
    price1, feature1 = get_all_data('2018-06-05',
                                    '2023-06-30',
                                    'price_data.csv',
                                    '.csv')

    price2, feature2 = get_all_data('2018-06-05',
                                    '2023-06-30',
                                    'price_data.csv',
                                    '.csv')

    strategy1 = fs1(price1, feature1)
    strategy2 = fs2(price2, feature2)

    #TODO: set paras for first strategy
    xi1 = []
    para1 = {}

    #TODO: set paras for second strategy
    xi2 = []
    para2 = {}

    strategy1.calculate_indicator(para1)
    strategy1.strategy_signal()

    strategy2.calculate_indicator(para2)
    strategy2.strategy_signal()
    
    combined_strategy = main(strategy1, strategy2)