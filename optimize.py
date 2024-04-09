
import os
import sys
from pathlib import Path

g_path = Path(__file__).parent
if str(g_path) not in sys.path:
    sys.path.append(str(g_path))
    
main_path = Path(__file__).parent.parent
if str(main_path) not in sys.path:
    sys.path.append(str(g_path))

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.pntx import SinglePointCrossover
from pymoo.operators.mutation.pm import PM

from pymoo.core.problem import Problem
from pymoo.optimize import minimize

#TODO:
from '.strategy_class import get_all_data
from '.strategy_class import futures_Strategy as fs1
from '.strategy_class import futures_Strategy as fs2

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import csv

class trade_problem(Problem):
    def __init__(self):
        # TODO:
        super().__init__(n_var=0,
                          n_obj=2,
                          n_ieq_constr=1,
                          n_eq_constr=0,
                          #重新設定基因上下界
                          xl=[],
                          xu=[])
        
    def _evaluate(self, x, out, *args, **kwargs):
        # TODO:
        # f for the target value(max, min)
        # g for the limitations
        f1_list = []
        f2_list = []
        g1_list = []
        
        for xi in x:
            xi = xi.round(0).astype(int)
            # TODO: change xi to a para dict
            para1 = {}

            para2 = {}

            strategy1.calculate_indicator(para1)
            strategy1.strategy_signal()

            strategy2.calculate_indicator(para2)
            strategy2.strategy_signal()
            
            combined_strategy = main(strategy1, strategy2)

            KPI_dict = combined_strategy.KPI()
            
            #TODO: if want to pursue for other target values
            f1 = KPI_dict['cum_return']
            f2 = KPI_dict['MDD']
            g1 = -f1
            
            f1_list.append(-f1)
            f2_list.append(f2)
            g1_list.append(g1)
            print('.', end='')
            
        out["F"] = np.column_stack([f1_list, f2_list])
        out["G"] = np.column_stack([g1_list])
        print('one generation finished.')
        
def main(MU, NGEN, CXPB, MUTPB):
    crossover = SinglePointCrossover(prob=CXPB)
    mut = PM(prob=MUTPB)
    
    algorithm = NSGA2(pop_size=MU, 
                    crossover=crossover, 
                    mutation=mut)
    
    problem = trade_problem()
    
    res = minimize(problem, 
                   algorithm, 
                   ('n_gen', NGEN),
                   save_history=True)
        
    #把最佳化每一代的點都畫出來，看是否有收斂
    for i in range(NGEN):
        f1_list = res.history[i].pop.get("F")[:,0]
        f2_list = res.history[i].pop.get("F")[:,1]
        
        plt.scatter(f2_list, -f1_list, color='green')
        plt.title(f"GEN {i}")
        plt.xlabel("MDD")
        plt.ylabel("return")
        if i == (NGEN-1):
            break
        plt.show()
        
    #取出最佳化參數及對應目標值
    x = res.pop.get("X").round(0).astype(int)
    
    f1_list = res.pop.get("F")[:,0]
    f2_list = res.pop.get("F")[:,1]
    
    #合併參數與目標值，並輸出成csv
    best_sols = pd.DataFrame(x)
    # TODO:
    best_sols.columns = []
    
    #TODO: decode the parameters for better visualization in csv
    
    best_sols['return'] = f1_list * -1
    best_sols['MDD'] = f2_list
    
    
    c = 0
    file = 'best_results_v0.csv'
    plot_file = '分布圖_v0.png'
    while os.path.exists(file):
        c += 1
        file = f'best_results_v{c}.csv'
        plot_file = f'分布圖_v{c}.png'
        
    best_sols.to_csv(file, index=False)
    plt.savefig(plot_file)
    plt.show()
            
    #取不重複值平均當作該策略整體表現
    return_mean = round(best_sols['return'].unique().mean(), 2)
    mdd_mean = round(best_sols['MDD'].unique().mean(), 4)
    
    summary_file = g_path.parent / 'summary.csv'
    strategy_name = g_path.name
    
    with open(summary_file, 'a', newline='') as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow([strategy_name, return_mean, mdd_mean])

if __name__ == '__main__':
    MU, NGEN, CXPB, MUTPB = 100, 25, 0.8, 0.05
    
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
    
    main(MU, NGEN, CXPB, MUTPB)
