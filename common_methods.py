# -*- coding: utf-8 -*-
"""
Created on Fri Jul 27 10:59:17 2018

@author: antonio constandinou
"""

# COMMON METHODS

import numpy as np
import pandas as pd
import statsmodels.tsa.stattools as ts
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import functools

from itertools import combinations
import statsmodels.api as sm


def plot_price_series(df, ts1, ts2, start_date, end_date):
    months = mdates.MonthLocator() # every month
    fig, ax = plt.subplots()
    ax.plot(df.index, df[ts1], label=ts1)
    ax.plot(df.index, df[ts2], label=ts2)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(True)
    fig.autofmt_xdate()
    plt.xlabel('Month/Year')
    plt.ylabel('Price ($)')
    plt.title('%s and %s Daily Prices' % (ts1, ts2))
    plt.legend()
    plt.show()

def plot_scatter_series(df, ts1, ts2):
    plt.xlabel('%s Price ($)' % ts1)
    plt.ylabel('%s Price ($)' % ts2)
    plt.title('%s and %s Price Scatterplot' % (ts1, ts2))
    plt.scatter(df[ts1], df[ts2])
    plt.show()

def plot_residuals(df):
    months = mdates.MonthLocator() # every month
    fig, ax = plt.subplots()
    ax.plot(df.index, df["res"], label="Residuals")
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.grid(True)
    fig.autofmt_xdate()
    plt.xlabel('Month/Year')
    plt.ylabel('Price ($)')
    plt.title('Residual Plot')
    plt.legend()
    plt.plot(df["res"])
    plt.show()

def write_dict_text(f_name, dict_):
    for sector, ticker_arr in dict_.items():
        """TO WORK ON"""
        print(sector)
        print(ticker_arr)

def fetch_last_day_mth(year_, mth_, conn):
    """
    return date of the last day of data we have for a given year in our Postgres DB. 
    args:
        year_: year, type int
        conn: a Postgres DB connection object
    return:
        integer, last trading day of year that we have data for
    """  
    cur = conn.cursor()
    SQL =   """
            SELECT MAX(date_part('day', date_price)) FROM daily_data
            WHERE date_price BETWEEN '%s-%s-01' AND '%s-%s-30'
            """
    cur.execute(SQL, [year_,mth_, year_, mth_])        
    data = cur.fetchall()
    cur.close()
    last_day = int(data[0][0])
    return last_day
    

def build_dict_of_arrays(list_of_tups):
    """
    create a dictionary from list of tuples. key = sector, values = array of tickers
           pertaining to a given sector
    args:
        list_of_tups: list of tickers matched with their sector
    returns:
        dictionary
    """
    sector_dict = {}
    
    for stock_sector in list_of_tups:
        sector = stock_sector[1]
        ticker = stock_sector[0]
        
        if sector not in sector_dict:
            sector_dict[sector] = [ticker]
        else:
            sector_dict[sector].append(ticker)
            
    return sector_dict


def write_results_text_file(f_name, sub_array):
    """
    write an array to text file
    args:
        f_name: name of our file to be written, type string
        sub_array: array of our data
    returns:
        None
    """
    # lets write elements of array to a file
    f_name = f_name + ".txt"
    file_to_write = open(f_name, 'w')

    for ele in sub_array:
        file_to_write.write("%s\n" % (ele,)) 


def load_db_credential_info(f_name_path):
    """
    load text file holding our database credential info and the database name
    args:
        f_name_path: name of file preceded with "\\", type string
    returns:
        array of 4 values that should match text file info
    """
    cur_path = os.getcwd()
    # lets load our database credentials and info
    f = open(cur_path + f_name_path, 'r')
    lines = f.readlines()[1:]
    lines = lines[0].split(',')
    return lines


def load_db_tickers_start_date(start_date, conn):
    """
    return a list of stock tickers that have data on the start_date arg provided
    args:
        start_date: datetime object to be used to query or PostgreSQL database
        conn: a Postgres DB connection object
    returns:
        list of tuples
    """
    # convert start_date to string for our SQL query
    date_string = start_date.strftime("%Y-%m-%d")
    
    cur = conn.cursor()
    SQL =   """
            SELECT ticker FROM symbol
            WHERE id IN
              (SELECT DISTINCT(stock_id) 
               FROM daily_data
               WHERE date_price = %s)
            """
    cur.execute(SQL, (date_string,))        
    data = cur.fetchall()
    return data


def load_db_tickers_sectors(start_date, conn):
    """
    return a list of tuples. each tuple is a ticker paired with it's sector
    args:
        start_date: datetime object to be used to query or PostgreSQL database
        conn: a Postgres DB connection object
    returns:
        list of tuples
    """
    # convert start_date to string for our SQL query
    date_string = start_date.strftime("%Y-%m-%d")
    cur = conn.cursor()
    SQL =   """
            SELECT ticker, sector FROM symbol
            WHERE id IN
              (SELECT DISTINCT(stock_id) 
               FROM daily_data
               WHERE date_price = %s)
            """
    cur.execute(SQL, (date_string,))        
    data = cur.fetchall()
    return data


def load_pairs_stock_data(pair, start_date, end_date, conn):
    """
    return a list of tuples. each tuple is a ticker paired with it's sector
    args:
        pair: tuple of two strings, each string is ticker
        start_date: datetime object to filter our pandas dataframe
        end_date: datetime object to filter our pandas dataframe
        conn: a Postgres DB connection object
    returns:
        array of pandas dataframe, each dataframe is stock data
    """    
    array_pd_dfs = []    

    cur = conn.cursor()
    SQL = """
          SELECT date_price, adj_close_price 
          FROM daily_data 
          INNER JOIN symbol ON symbol.id = daily_data.stock_id 
          WHERE symbol.ticker LIKE %s
          """
    # for each ticker in our pair
    for ticker in pair:
        # fetch our stock data from our Postgres DB
        cur.execute(SQL, (ticker,))
        results = cur.fetchall()
        # create a pandas dataframe of our results
        stock_data = pd.DataFrame(results, columns=['Date', 'Adj_Close'])
        # ensure our data is in order of date
        stock_data = stock_data.sort_values(by=['Date'], ascending = True)
        # convert our column to float
        stock_data['Adj_Close'] = stock_data['Adj_Close'].astype(float)
        # filter our column based on a date range
        mask = (stock_data['Date'] > start_date) & (stock_data['Date'] <= end_date)
        # rebuild our dataframe
        stock_data = stock_data.loc[mask]
        # re-index the data
        stock_data = stock_data.reset_index(drop=True)
        # append our df to our array
        array_pd_dfs.append(stock_data)
        
    return array_pd_dfs


def pair_data_verifier(array_df_data, pair_tickers, threshold=10):
    """
    merge two dataframes, verify if we still have the same number of data we originally had.
    use an inputted threshold that tells us whether we've lost too much data in our merge or not.
    args:
        array_df_data: array of two pandas dataframes
        pair_tickers: tuple of both tickers
        threshold: integer, max number of days of data we can be missing after merging two
                            dataframes of data.
                   default = 10 to represent 10 days.
    returns:
        boolean False or new merged pandas dataframe
        
        False: if our new merged dataframe is missing too much data (> threshold)
        merged pandas dataframe: if our pd.dataframe index length is < threshold
    """
    stock_1 = pair_tickers[0]
    stock_2 = pair_tickers[1]
    df_merged = pd.merge(array_df_data[0], array_df_data[1], left_on=['Date'], right_on=['Date'], how='inner')
    
    new_col_names = ['Date', stock_1, stock_2] 
    df_merged.columns = new_col_names
    # round columns
    df_merged[stock_1] = df_merged[stock_1].round(decimals = 2)
    df_merged[stock_2] = df_merged[stock_2].round(decimals = 2)
    
    new_size = len(df_merged.index)
    old_size_1 = len(array_df_data[0].index)
    old_size_2 = len(array_df_data[1].index)

#        print("Pairs: {0} and {1}".format(stock_1, stock_2))
#        print("New merged df size: {0}".format(new_size))
#        print("{0} old size: {1}".format(stock_1, old_size_1))
#        print("{0} old size: {1}".format(stock_2, old_size_2))
#        time.sleep(2)
    
    if (old_size_1 - new_size) > threshold or (old_size_2 - new_size) > threshold:
        print("This pair {0} and {1} were missing data.".format(stock_1, stock_2))
        return False
    else:
        return df_merged

def data_array_merge(data_array):
    """
    merge all dfs into one dfs
    args:
        data_array: array of pandas df
    returns:
        merged_df, single pandas dataframe
    """
    merged_df = functools.reduce(lambda left,right: pd.merge(left,right,on='Date'), data_array)
    merged_df.set_index('Date', inplace=True)
    return merged_df


def load_df_stock_data_array(stocks, start_date, end_date, conn):
    """
    return an array where each element is a dataframe of loaded data
    args:
        stocks: tuple of strings, each string is ticker
        start_date: datetime object to filter our pandas dataframe
        end_date: datetime object to filter our pandas dataframe
        conn: a Postgres DB connection object
    returns:
        array of pandas dataframe, each dataframe is stock data
    """    
    array_pd_dfs = []    

    cur = conn.cursor()
    SQL = """
          SELECT date_price, adj_close_price 
          FROM daily_data 
          INNER JOIN symbol ON symbol.id = daily_data.stock_id 
          WHERE symbol.ticker LIKE %s
          """
    # for each ticker in our pair
    for ticker in stocks:
        # fetch our stock data from our Postgres DB
        cur.execute(SQL, (ticker,))
        results = cur.fetchall()
        # create a pandas dataframe of our results
        stock_data = pd.DataFrame(results, columns=['Date', ticker])
        # ensure our data is in order of date
        stock_data = stock_data.sort_values(by=['Date'], ascending = True)
        # convert our column to float
        stock_data[ticker] = stock_data[ticker].astype(float)
        # filter our column based on a date range
        mask = (stock_data['Date'] > start_date) & (stock_data['Date'] <= end_date)
        # rebuild our dataframe
        stock_data = stock_data.loc[mask]
        # re-index the data
        stock_data = stock_data.reset_index(drop=True)
        # append our df to our array
        array_pd_dfs.append(stock_data)
        
    return array_pd_dfs


def find_cointegrated_pairs(data, p_value=0.01):
    """
    statsmodels.tsa.stattools coint method for identifying pairs
    args:
        data: needs to be pd_df where each column = individual ticker Adj_Close
        p_value: threshold for accepting a pairs model (float), default 0.01
    returns:
        score_matrix (np.array), pvalue_matrix (np.array), pairs (array)
    """
    n = data.shape[1]
    score_matrix = np.zeros((n, n))
    pvalue_matrix = np.ones((n, n))
    keys = data.keys()
    pairs = []
    for i in range(n):
        for j in range(i+1, n):
            S1 = data[keys[i]]
            S2 = data[keys[j]]
            result = ts.coint(S1, S2)
            score = result[0]
            pvalue = result[1]
            score_matrix[i, j] = score
            pvalue_matrix[i, j] = pvalue
            if pvalue < p_value:
                pairs.append((keys[i], keys[j]))
    return score_matrix, pvalue_matrix, pairs