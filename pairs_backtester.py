# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 13:13:18 2018

@author: antonio constandinou
"""

# WORKING WITH SINGLE PAIRS - LOADING DB DATA

import datetime
import psycopg2
import common_methods as cm
import statsmodels.tsa.stattools as ts
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd    
import glob


class PairBackTester():
    
    def __init__(self, pair, merged_df, z_threshold, lookback_periods, initial_capital):
        self.pair = pair
        self.stock_1 = self.pair[0]
        self.stock_2 = self.pair[1]
        self.merged_df = merged_df
        self.z_upper_thresh = z_threshold[0]
        self.z_lower_thresh = z_threshold[1]
        self.short_lookback = lookback_periods[0]
        self.long_lookback = lookback_periods[1]
        self.params = "_{0}_{1}".format(self.short_lookback, self.long_lookback)
        self.initial_capital = initial_capital        
        self.ratios = self.merged_df[self.stock_1] / self.merged_df[self.stock_2]
        self.ma_short = self.ratios.rolling(window = self.short_lookback, center = False).mean()
        self.ma_long = self.ratios.rolling(window = self.long_lookback, center = False).mean()
        self.std = self.ratios.rolling(window = self.long_lookback, center = False).std()
        self.zscore = (self.ma_short - self.ma_long)/self.std
        self.total_dollars_per_trade = self.initial_capital * 2.0
        self.long_pos = False
        self.short_pos = False
        self.daily_data = []
        # CREATE OUR COLUMNS
        self.daily_data.append("Date,Position,Ticker1,Ticker2,ZScore,Ticker1_Shares,Ticker2_Shares,Ratio,Ticker1_P,Ticker2_P,Days,PnL")
        self.directory_pair = "PairsResults"+self.params+"/{0}_{1}".format(self.stock_1, self.stock_2)
        self.create_directories()
        
        self.TrdID = ""
        self.position = ""
        self.pos1 = 0.0
        self.pos2 = 0.0
        self.EntryP_S1 = 0.0
        self.EntryP_S2 = 0.0
        self.YestP_S1 = 0.0
        self.YestP_S2 = 0.0
        self.CurrentP_S1 = 0.0
        self.CurrentP_S2 = 0.0
        self.ExitP_S1 = 0.0
        self.ExitP_S2 = 0.0
        self.PnL = 0.0
        self.Pnl_history = []
        self.TradePnL = 0.0
        self.OrigTrRatio = 0.0
        self.TrRatio = 0.0
        self.EntryDateStr = ""
        self.EntryDate = None
        self.ExitDateStr = ""
        self.days_in_trade = 0
        
    def create_directories(self):
        main_directory = "PairsResults"+self.params
        
        if not os.path.exists(main_directory):
            os.makedirs(main_directory)
        if not os.path.exists(self.directory_pair):
            os.makedirs(self.directory_pair)
    
    def collect_data(self, ii, position, pos1, pos2, tr_ratio, stock1_p, stock2_p):
        # a class method to collect data every day
        self.daily_data.append(
                               self.merged_df.index[ii].strftime('%Y%m%d') + "," +
                               position + "," + self.stock_1 + "," +
                               self.stock_2 + "," + repr(self.zscore[ii-1]) + "," +
                               repr(pos1) + "," + repr(pos2) + "," + repr(tr_ratio) + "," +
                               repr(stock1_p) + "," + repr(stock2_p) + "," +
                               repr(self.days_in_trade) + "," + repr(self.PnL)
                              )
    
    def write_all_data(self):
        # instance method to write data to individual pairs folder and master results file
        self.write_file()
        self.write_trade_master()
        
    def write_file(self):
        with open((self.directory_pair + "/{0}.txt".format(self.TrdID)),"w") as ff:
            for item in self.daily_data:
                item = "".join(item) + "\n"
                ff.write(item)
        ff.close()
        
    def write_trade_master(self):
        main_file = "PairsResults"+self.params+"/MasterResults.txt"
        # trade statistics
        if len(self.Pnl_history) > 0:
            trd_mean = sum(self.Pnl_history)/len(self.Pnl_history)
            max_day = max(self.Pnl_history)
            min_day = min(self.Pnl_history)
        else:
            trd_mean, max_day, min_day = [0.0, 0.0, 0.0]
        # create an array for our string
        trade_details = [self.TrdID, self.EntryDateStr, self.position, self.stock_1, self.stock_2, 
                         repr(self.pos1), repr(self.pos2), repr(self.OrigTrRatio), self.ExitDateStr,
                         repr(trd_mean),repr(max_day), repr(min_day), 
                         repr(self.days_in_trade), repr(self.TradePnL)]
        # join our array    
        item = ",".join(trade_details) + "\n"
        # write the data to our file
        with open(main_file,"a") as ff:
            ff.write(item)
        ff.close()
    
    def calc_day_PnL(self):
        self.PnL = ((self.CurrentP_S1 - self.YestP_S1) * self.pos1) + ((self.CurrentP_S2 - self.YestP_S2) * self.pos2)
        self.TradePnL += self.PnL 
        self.Pnl_history.append(self.PnL)

    
    def reset_trade(self):
        self.daily_data = []
        self.daily_data.append("Date,Position,Ticker1,Ticker2,ZScore,Ticker1_Shares,Ticker2_Shares,Ratio,Ticker1_P,Ticker2_P,Days,PnL")
        self.Pnl_history = []
        self.TradePnL = 0.0
        self.PnL = 0.0
        self.pos1 = 0.0
        self.pos2 = 0.0
        self.short_pos = False
        self.long_pos = False
        self.position = ""
        self.OrigTrRatio = 0.0
        self.TrdID = ""
        self.days_in_trade = 0
        
    def set_new_trade(self, ii, EntryD):
        if self.position == "Long":
            self.pos1 = self.initial_capital/self.merged_df[self.stock_1][ii]
        else:
            self.pos1 = self.initial_capital/self.merged_df[self.stock_1][ii] * -1.0  
        # if pos1 is long, pos2 is short, vice versa if pos1 is short, pos2 is long
        self.OrigTrRatio = self.TrRatio
        self.pos2 = self.pos1 * self.ratios[ii-1] * -1.0
        self.EntryP_S1 = self.CurrentP_S1
        self.EntryP_S2 = self.CurrentP_S2
        self.PnL = 0.0
        self.EntryDateStr = EntryD.strftime('%Y%m%d')
        self.EntryDate = EntryD
        self.TrdID = self.EntryDateStr + "_" + self.position + "{0}{1}".format(self.stock_1, self.stock_2)
        
    def backtest(self):
        # method to run after we've instantiated a new PairBackTester object
        # we only enter trades using previous day z-score and ratio
        for ii in range(1, len(self.ratios)):
            self.YestP_S1 = self.merged_df[self.stock_1][ii-1]
            self.YestP_S2 = self.merged_df[self.stock_2][ii-1]
            self.CurrentP_S1 = self.merged_df[self.stock_1][ii]
            self.CurrentP_S2 = self.merged_df[self.stock_2][ii]
            self.TrRatio = self.ratios[ii-1]
            
            CurrentDate = self.merged_df.index[ii]
            Zscore = self.zscore[ii-1]
            
            if Zscore < -self.z_upper_thresh and not self.long_pos:
                # WE HAVE A NEW LONG SIGNAL - COLLECT ALL OUR DATA
                self.position = "Long"
                self.long_pos = True
                self.set_new_trade(ii, CurrentDate)
                self.collect_data(ii, self.position, self.pos1, self.pos2, self.TrRatio, self.EntryP_S1, self.EntryP_S2)
                
            if Zscore > -self.z_lower_thresh and self.long_pos:
                # WE NEED TO EXIT LONG SIGNAL - COLLECT ALL OUR DATA
                self.days_in_trade += 1
                self.ExitP_S1 = self.CurrentP_S1
                self.ExitP_S2 = self.CurrentP_S2
                self.calc_day_PnL()
                self.collect_data(ii, self.position, self.pos1, self.pos2, self.TrRatio, self.ExitP_S1, self.ExitP_S2)
                self.ExitDateStr = CurrentDate.strftime('%Y%m%d')
                # exit trade, write our trade details, reset
                self.write_all_data()
                self.reset_trade()
                
            if Zscore > self.z_upper_thresh and not self.short_pos:
                # WE HAVE A NEW SHORT SIGNAL - COLLECT ALL OUR DATA
                self.position = "Short"
                self.short_pos = True
                self.set_new_trade(ii, CurrentDate)
                self.collect_data(ii, self.position, self.pos1, self.pos2, self.TrRatio, self.EntryP_S1, self.EntryP_S2)
                
            if Zscore < self.z_lower_thresh and self.short_pos:
                self.days_in_trade += 1
                self.ExitP_S1 = self.CurrentP_S1
                self.ExitP_S2 = self.CurrentP_S2
                self.calc_day_PnL()
                self.collect_data(ii, self.position, self.pos1, self.pos2, self.TrRatio, self.ExitP_S1, self.ExitP_S2)
                self.ExitDateStr = CurrentDate.strftime('%Y%m%d')
                # exit trade, write our trade details, reset
                self.write_all_data()
                self.reset_trade()
                           
            if ii == (len(self.ratios)-1):
                if (self.long_pos or self.short_pos):
                    self.days_in_trade += 1
                    self.calc_day_PnL()
                    self.ExitP_S1 = self.merged_df[self.stock_1][ii]
                    self.ExitP_S2 = self.merged_df[self.stock_2][ii]
                    self.ExitDateStr = CurrentDate.strftime('%Y%m%d')
                    self.collect_data(ii, self.position , self.pos1, self.pos2, self.TrRatio, self.ExitP_S1, self.ExitP_S2)
                    self.write_all_data()
                else:
                    continue
                print("Finished trading for {0}".format(self.pair))
            
            if (self.long_pos or self.short_pos) and (CurrentDate != self.EntryDate):
                self.days_in_trade += 1
                self.calc_day_PnL()
                self.collect_data(ii, self.position, self.pos1, self.pos2, self.TrRatio, self.CurrentP_S1, self.CurrentP_S2)


def main():
    # DB INFO FILE - host, user, password, db_name
    db_credential_info_p = "\\" + "database_info.txt"
    
    # create our instance variables for host, username, password and database name
    db_host, db_user, db_password, db_name = cm.load_db_credential_info(db_credential_info_p)
    conn = psycopg2.connect(host=db_host,database=db_name, user=db_user, password=db_password)
    
    # LOAD ALL COINTEGRATED FILE NAMES INTO A LIST
    all_pairs_files = []
    
    for file_name in glob.glob("coint_method_pairs_*.txt"):
        all_pairs_files.append(file_name)

    
    for pairs_file in all_pairs_files:
        
        # LOAD COINTEGRATED PAIRS
        cur_path = os.getcwd()
        full_path = cur_path + "\\" + pairs_file
        
        # extract start date from file name
        # creating dates for the start of backtest and end of backtest
        year_int = int(pairs_file.split(".")[0].split('_')[-1][0:4])
        end_yr_int = year_int + 1
        month_int = int(pairs_file.split(".")[0].split('_')[-1][4:6])
        
        # start in month 11 not 12 to allow zscores to be calculated
        mth = 11
        last_tr_day_start = cm.fetch_last_day_any_mth(end_yr_int, mth, conn)
        trd_start_dt = datetime.date(year_int,month_int - 1,last_tr_day_start)
        
        # we need the final day of our year
        mth = 12
        last_tr_day_end = cm.fetch_last_day_any_mth(end_yr_int, mth, conn)
        trd_end_dt = datetime.date(end_yr_int,month_int,last_tr_day_end)
        
        # load each pair to its appropriate sector key
        pairs_dict = {}
        
        with open(full_path) as f:
            for line in f:
               (key, val1, val2) = line.split(",")
               if key in pairs_dict:
                   pairs_dict[key].append((val1, val2.strip("\n")))
               else:
                   pairs_dict[key] = [(val1, val2.strip("\n"))]
      
        print("Starting BT from {0} to {1}".format(trd_start_dt.strftime('%Y%m%d'), trd_end_dt.strftime('%Y%m%d')))
        
        # BEGIN OUR BACKTEST PER EQUITY PAIR PER DATE RANGE
        for sector, ticker_arr in pairs_dict.items():
            for pair in ticker_arr:
                if pair != ('GOOG','GOOGL'):
                    # OUT OF SAMPLE DATA
    
                    array_df_data_tr = cm.load_df_stock_data_array(pair, trd_start_dt, trd_end_dt, conn)
                    merged_data_tr = cm.data_array_merge(array_df_data_tr)
                    
                    short_window = 5
                    long_window = 30
                    #trade_PNL = trade(merged_data_tr, pair, short_window, long_window)
                    
                    # BUILDING OUR CLASS
                    z_threshold = [1.0, 0.0]
                    lookback_periods = [short_window, long_window]
                    initial_capital = 50000.0
                    
                    new_pair = PairBackTester(pair, merged_data_tr, z_threshold, lookback_periods, initial_capital)
                    new_pair.backtest()


        print("Completed BT from {0} to {1}".format(trd_start_dt.strftime('%Y%m%d'), trd_end_dt.strftime('%Y%m%d')))

    
if __name__ == "__main__":
    main()