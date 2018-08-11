# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 09:50:49 2018

@author: antonio constandinou
"""

# UTILIZING COINT METHOD TO ISOLATE PAIRS TRADING
# WITH INTRODUCTION OF SPY AS A MEMBER OF EACH SECTOR

import psycopg2
import datetime
import seaborn
import pandas as pd
import os
import functools
import matplotlib.pyplot as plt

import common_methods as cm


def main():
    skip_etfs = True
    # create a path version of our text file
    db_credential_info_p = "\\" + "database_info.txt"
    
    # create our instance variables for host, username, password and database name
    db_host, db_user, db_password, db_name = cm.load_db_credential_info(db_credential_info_p)
    conn = psycopg2.connect(host=db_host,database=db_name, user=db_user, password=db_password)
    
    year_array = list(range(2004, 2015))
    
    for yr in year_array:
        # create a pairs file for each two year chunk in our range
        year = yr
        end_year = year + 2
        # find the last trading day for our years range
        last_tr_day_start = cm.fetch_last_day_mth(year, conn)
        last_tr_day_end = cm.fetch_last_day_mth(end_year, conn)
        # date range to pull data from
        start_dt = datetime.date(year,12,last_tr_day_start)
        end_dt = datetime.date(end_year,12,last_tr_day_end)
        start_dt_str = start_dt.strftime("%Y%m%d")
        end_dt_str = end_dt.strftime("%Y%m%d")
        
        # list of stocks and their sector
        list_of_stocks = cm.load_db_tickers_sectors(start_dt, conn)
        # dict: key = sector with values = array of all tickers pertaining to a sector
        sector_dict = cm.build_dict_of_arrays(list_of_stocks)
        # write these arrays to text files later
        passed_pairs = {}
        #all_failed_pairs = []
        
        for sector, ticker_arr in sector_dict.items():
            if skip_etfs and sector != "ETF":
                # we need to append SPY to each sub_array to ensure that cointegrated pairs
                # don't include a 3rd variable in why they are cointegrated

                ticker_arr.append('SPY')

                data_array_of_dfs = cm.load_df_stock_data_array(ticker_arr, start_dt, end_dt, conn)
                merged_data = cm.data_array_merge(data_array_of_dfs)
                

                scores, pvalues, pairs = cm.find_cointegrated_pairs(merged_data)
                # seaborn heatmap for each sector within each range of time
                # uncomment this section to print out seaborn heatmaps in iPython console
#                confidence_level = 1 - 0.01
#                m = [0,0.2,0.4,0.6,0.8,1]
#                plt.figure(figsize=(min(10,len(pvalues)), min(10,len(pvalues))))
#                seaborn.heatmap(pvalues, xticklabels=ticker_arr, 
#                                yticklabels=ticker_arr, cmap='RdYlGn_r', 
#                                mask = (pvalues >= confidence_level))
#                plt.show()

                new_pairs = cm.remove_ticker('SPY', pairs)
                passed_pairs[sector] = new_pairs
                print("Complete sector {0} for date range: {1}-{2}".format(sector, start_dt_str, end_dt_str))
                
        f_name = "coint_method_pairs_{0}".format(end_dt_str)    
        cm.write_dict_text(f_name, passed_pairs)
    
    
if __name__ == "__main__":
    main()