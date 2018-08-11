# -*- coding: utf-8 -*-
"""
Created on Wed Aug  1 19:45:12 2018

@author: antonio constandinou
"""

# ANALYZE TRADE RESULTS - PAIRS TRADING

import os
import pandas as pd
# http://dateutil.readthedocs.io/en/stable/rrule.html
from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR
import datetime
import psycopg2
import common_methods as cm
import numpy as np


class NewTrade():
    
    def __init__(self, trd_id, ticker_1, ticker_2, params):
        self.trd_id = trd_id
        self.cur_dir = os.getcwd()
        self.ticker1 = ticker_1
        self.ticker2 = ticker_2
        self.params = params
        # load our trd data into a df
        self.daily_trd_df = self.load_trd_history()
        self.exit_date = self.daily_trd_df.iloc[-1]['Date']

    def load_trd_history(self):
        # need to load our trd history into a pd dataframe
        ticker_dir = self.ticker1 + "_" + self.ticker2 + "\\"
        path_load = self.cur_dir + "\\PairsResults" + self.params + "\\" + ticker_dir + self.trd_id + ".txt"
        daily_trd_df = pd.read_csv(path_load, sep=',' , header=0)
        return daily_trd_df
    
    def fetch_day_pnl(self, date_int):
        # given a date, we need to fetch day's PnL
        try:
            day_pnl = self.daily_trd_df.loc[self.daily_trd_df['Date'] == date_int, 'PnL'].iloc[0]
        except:
            # most likely holiday
            day_pnl = 0
        return day_pnl
        
    def fetch_trade_id(self):
        return self.trd_id

    def exit_date_check(self, date_int):
        if self.exit_date == date_int:
            return True
        else:
            return False

def daterange(start_date, end_date):
    """
    automate a range of business days between two dates
    args:
        start_date:
        end_date:
    returns:
        
    """
    return rrule(DAILY, dtstart=start_date, until=end_date, byweekday=(MO,TU,WE,TH,FR))


def daily_stats(df_trds, st_dt, end_dt, params):
    """
    on every business day in a given range, load trades from backtest to calculate
    cumulative daily PnL for all trades
    args:
        df_trds: two column dataframe containing a trade_id and entry_date
                 trade_id is used to load a text file containing daily trade outcome
        st_dt: start of our analysis, datetime obj
        end_dt: start of our analysis, datetime obj
    returns:
        
    """
    trd_dict = {}
    for row in df_trds.itertuples():
        if row[2] in trd_dict:
            trd_dict[row[2]].append([row[1], row[3], row[4]])
        else:
            trd_dict[row[2]] = [[row[1], row[3], row[4]]]

    params = params
    start_date = st_dt
    end_date = end_dt
    
    trd_holder = {}
    daily_pnl = []
    # lets track each trd_id for a given date
    #daily_trd_ids = {}
    curr_year = 0
    
    for tr_date in daterange(start_date, end_date):
        
        date_int = int(tr_date.strftime("%Y%m%d"))
        year = int(str(date_int)[0:4])
        # reset current year and dict
        if year != curr_year:
            curr_year = year
            trd_holder = {}
            
        days_pnl = 0.0
        no_trades = 0
        
        trds_to_delete = []
        
        if date_int == 20070119:
            print("debug")
            
        #this avoids an error by using .copy().items() rather than .items()
        for k, trd in trd_holder.copy().items():
            # renamed key to deleted - avoid these trds
            if k != "deleted":
                days_pnl += trd.fetch_day_pnl(date_int)
                no_trades += 1
                
                # if the trade is also exiting today - remove from our trd_list
                if trd.exit_date_check(date_int):
                    # locate trd.id
                    trd_id_to_remove = trd.fetch_trade_id()
                    trds_to_delete.append(trd_id_to_remove)
        
        for trd_del in trds_to_delete:
            trd_holder["deleted"] = trd_holder.pop(trd_del)
            
        daily_pnl.append([date_int, days_pnl, no_trades])
        
        print("Currently at {0} with PnL: {1}, number tr: {2}".format(date_int, days_pnl, no_trades))
        
        if date_int in trd_dict:
            # we need to load all trade_ids for given date
            trd_ids = trd_dict[date_int]
            
            for trade in trd_ids:
                trd_id = trade[0]
                ticker_1 = trade[1]
                ticker_2 = trade[2]
                # we need to load new trade objects and append to our list
                new_trd = NewTrade(trd_id, ticker_1, ticker_2, params)
                trd_holder[trd_id] = new_trd

    # COMPUTE DAILY STATS
    daily_df = pd.DataFrame(daily_pnl, columns = ['Date', 'PnL', 'TradeCount'])
    daily_stats = trade_stats('daily', daily_df, 'PnL')    
    
    return daily_pnl, daily_stats


def trade_stats(formatting, df_results, pnl_col_name):
    """
    calculate trade statistics with given pandas dataframe
    args:
        formatting: daily or trade, type string, used to represent the format of our results
        df_results: pandas dataframe of results, type pd dataframe
        pnl_col_name: name of column to computer statistics, type string
                      the column itself in the df must be an integer or float
    return:
        array of results indexed as follows:
            total_trades, total_w, win_perc, total_pnl, avg_trade, 
            max_winner, max_loser, avg_winner, avg_loser
    """
    if formatting == 'daily':
        # remove all 0s from date and equity
        df_results = df_results[df_results['PnL'] != 0]
        print(len(df_results))
        
    # ANALYZE DATA AT TRADE LEVEL
    total_trades = len(df_results[pnl_col_name])
    print("Total {0}: {1}".format(formatting, total_trades))
    
    mask = df_results[pnl_col_name] > 0
    all_winning_trades = df_results[pnl_col_name].loc[mask]
    
    total_win_tr = len(all_winning_trades)
    print("Total winning {0}: {1}".format(formatting, total_win_tr))
    
    win_percent = float(total_win_tr)/float(total_trades)
    print("Win percentage: {}".format(win_percent))
    
    # total PnL
    total_pnl = df_results[pnl_col_name].sum()
    print("Total {0} PnL: {1}".format(formatting, total_pnl))
    
    # avg. trade PnL
    avg_trade = df_results[pnl_col_name].mean()
    print("Avg {0} PnL: {1}".format(formatting, avg_trade))
    
    # avg. trade %
    notional = 100000.0
    rounded_val = round((avg_trade/notional)*100.0,4)
    print("Avg {0} with 100k notional: {1} %".format(formatting, rounded_val))
    
    # max trade gain
    max_winner = df_results[pnl_col_name].max()
    print("Max winning {0} PnL: {1}".format(formatting, max_winner))
    
    # max trade loss
    max_loser = df_results[pnl_col_name].min()
    print("Max losing {0} PnL: {1}".format(formatting, max_loser))

    # avg winner
    avg_winner = all_winning_trades.mean()
    print("Avg winning {0} PnL: {1}".format(formatting, avg_winner))

    # avg loser
    mask = df_results[pnl_col_name] <= 0
    all_losing_trades = df_results[pnl_col_name].loc[mask]
    avg_loser = all_losing_trades.mean()
    print("Avg losing {0} PnL: {1}".format(formatting, avg_loser))

    return [total_trades, total_win_tr, total_pnl, win_percent, avg_trade, 
            max_winner, max_loser, avg_winner, avg_loser]


def main():
    
    # DB INFO FILE - host, user, password, db_name
    db_credential_info_p = "\\" + "database_info.txt"
    
    # create our instance variables for host, username, password and database name
    db_host, db_user, db_password, db_name = cm.load_db_credential_info(db_credential_info_p)
    conn = psycopg2.connect(host=db_host,database=db_name, user=db_user, password=db_password)
    
    cur_path = os.getcwd()
    
    ## these parameters impact file name and sub-folder to gather data from
    params = "_TimeLimit_30"
    
    results_file = cur_path + "\\PairsResults" + params + "\\MasterResults.txt"
    
    # load results_file to pandas df
    df_res = pd.read_table(results_file, 
                           delimiter =",", 
                           names = ('Trade_Id', 'Entry_Date', 'Position', 
                                    'Ticker1', 'Ticker2', 
                                    'Pos1', 'Pos2', 'Ratio', 
                                    'Exit_Date', 'Avg_Day', 
                                    'Max_Day', 'Min_Day', 'Tr_Length', 
                                    'Total_PnL'), 
                           index_col = False)
    
    # TRADE SATISTICS - compute and output trade stats
    trade_statistics = trade_stats('trade', df_res, 'Total_PnL')
    
    # DAILY STATISTICS
    dly_stats_df = df_res[['Trade_Id','Entry_Date', 'Ticker1', 'Ticker2']]
    
    # back test start_date and end_date as datetime objects

    start_yr = 2006
    end_yr = 2017
    mth_ = 12
    start_dt_day = cm.fetch_last_day_mth(start_yr, mth_, conn)
    end_dt_day = cm.fetch_last_day_mth(end_yr, mth_, conn)

    start_dt = datetime.date(start_yr,mth_,start_dt_day)
    end_dt = datetime.date(end_yr,mth_,end_dt_day)
    
    daily_pnl, daily_statistics = daily_stats(dly_stats_df, start_dt, end_dt, params)
    
    # write our data to text file
    f_name = "daily_results" + params
    f_name2 = "model_daily_stats" + params
    f_name3 = "model_trade_stats" + params
    
    cm.write_results_text_file(f_name, daily_pnl)
    cm.write_results_text_file(f_name2, daily_statistics)
    cm.write_results_text_file(f_name3, trade_statistics)
    
    #df_res.hist(column='Total_PnL', figsize = (20,20), bins=100)
    
if __name__ == "__main__":
    main()