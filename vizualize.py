
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

main_path = Path(__file__).parent.parent
if str(main_path) not in sys.path:
    sys.path.append(str(main_path))

#TODO: import two different strategy objects
from .strategy_class import get_all_data
from .strategy_class import futures_Strategy as fs1
from .strategy_class import futures_Strategy as fs2

from combine_strategy import main as combine

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

#NOTE: the best combination for xi2 as xi1 fixed.
#xi1 = [4000, -4000, 0.06,0.09,0.8,1000]
#xi2 = [1700,-2600,-2700,1800,8,23]

#TODO: set paras for first strategy
xi1 = []
para1 = {
    }

#TODO: set paras for second strategy
xi2 = []
para2 = {
        }

strategy1.calculate_indicator(para1)
strategy1.strategy_signal()

strategy2.calculate_indicator(para2)
strategy2.strategy_signal()
    
complete_strategy = combine(strategy1, strategy2)


fig = px.line(price1, x=price1.index, y='trade_price')

trade_date = complete_strategy.record

trade_date['in_date'] = pd.to_datetime(trade_date['in_date'])
trade_date['out_date'] = pd.to_datetime(trade_date['out_date'])

for index, i in complete_strategy.record.iterrows():
    fig.add_vline(x=i.in_date, line_width=1, line_color=('red' if i.signal == 1 else 'green'))
    fig.add_vline(x=i.out_date, line_width=0.5, line_color=('red' if i.signal == -1 else 'green'))
fig.show()
