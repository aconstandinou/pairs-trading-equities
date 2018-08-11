# Building an Equity Pairs Trading Model

###### This project is meant to use python and the stattools library in building a pairs trading model. There is also code that utilizes a previously built PostgreSQL database of stock data to find pairs of stocks that exhibit cointegration. By using my equity data warehouse (built with PostgreSQL and Python) the project that follows builds a rolling cointegrated pairs trading model.

###### The tests that follow are part of a blog series I've written over on Medium to tackle interesting quantitative research projects.

###### Link: https://medium.com/@constandinou.antonio
###### Title of blog post - *Quant Post 3.2: Building a Pairs Trading Model*

### Getting Started
If you plan on using this code along with the equity database, please reference the following link before moving forward: https://github.com/aconstandinou/data-warehouse-build

##### Otherwise, you will need to change how the following python scripts access market data.

### Quick overview of computed iterations
I have not documented actual time taken in running the below scripts, but the original database used for this test includes ~ 505 equities and their respective historical data which totals around 1.5 million lines of historical data.

The pairs trading model will only identify pairs to trade within the same sector, and there are 11 sectors total. The total number of potential pairs tested across all sectors is roughly 14,500 pairs.

The current setup also uses 2-year's worth of market data in a rolling fashion starting in 2006 and up until 2016. That creates 11 time periods to verify all potential 14,500 pairs to trade.

### Prerequisites
You need to have PostgreSQL and Python installed.

Here are the python libraries used in the mean reversion tests. Version numbers are included as well.

* psycopg2 version 2.7.5 (dt dec pq3)
* numpy 1.14.3
* pandas 0.23.0
* seaborn 0.8.1
* statsmodels 0.9.0
* statsmodels.api
* statsmodels.tsa.stattools
* matplotlib 2.2.2
* math
* os
* datetime

### Useful Information & How to use the code

### For all Python Scripts
`common_methods.py`
This python file contains many methods that are used across the python scripts that follow. It was built with the desire to "DRY" (Don't Repeat Yourself) my code and reuse as many methods as possible.

File is imported as `cm` in all the following scripts.

`database_info.txt`
This text file holds database credentials needed to connect to a PostgreSQL database built in a previous project (link above). Specifically, the file holds four necessary identifiers: database_host, database_user, database_password, database_name

The only specific identifier that was previously set was the database_name as *securities_master*. All other details will be specific to your local setup.

### Part I - Identifying Equity Pairs that are Cointegrated - `identifying_pairs.py`
1. Code connects to database and sets variable `year_array` to a list with given range of years.

2. For each year in our range, we need to connect to our DB and find the last trading day for a given year.

3. Build a dictionary where each key is a sector and each value is a list of tickers for given sector.

Variable: `sector_dict = cm.build_dict_of_arrays(list_of_stocks)`

4. Within each sector, for each ticker load two years of data into a pandas dataframe, and create a list of all these dataframes.

```python
data_array_of_dfs = cm.load_df_stock_data_array(ticker_arr, start_dt, end_dt, conn)
merged_data = cm.data_array_merge(data_array_of_dfs)
```

5. Using the `merged_data` variable, find cointegrated pairs within each sector that pass at the 99% critical level. This can be changed within `common_methods.py` with method name `find_cointegrated_pairs`.

Variable to change is a method argument p_value currently defaulted to 0.01.
```python
def find_cointegrated_pairs(data, p_value=0.01):
```

6. OPTIONAL: Currently commented out, but starting at `confidence_level = 1 - 0.01` and up until `plt.show()` you could view the seaborn heatmap built for each sector for a given time period.

7. Remove any pairs that include our SPY ETF.

8. Output a text file ex: `coint_method_pairs_20061229.txt` that contains cointegrated pairs for all sectors. The date included in the text file name is the last day of data in our training year. Pairs are used in the following year for backtesting in Part II below. Each row in text file contains `Sector,Pair1,Pair2`.

### Part II - Backtest Equity Pairs - `pairs_backtester.py`
1. Code connects to database.

2. For all text files generated in Part I, load their file names to a list.

3. For each file to load in step 2, load our text file data by pair into a dictionary where each key is our sector and value is a list of tuples. Each tuple is a pair of two tickers.

4. Create our backtesting date range.

5. For each pair, load their data, merge their data and set parameters for our backtest. These can be changed.

```Python
short_window = 5 # short rolling average
long_window = 30 # long rolling average

# BUILDING OUR CLASS
z_threshold = [1.0, 0.0] # entry and exit thresholds
lookback_periods = [short_window, long_window] # create a list of our rolling averages
initial_capital = 50000.0 # total capital allocated to one position in each pair, for total $100,000
```

6. Backtest each pair using `PairBackTester` class

7. `PairBackTester` class handles the entire backtesting, data storing, and output of our trade results. Results outputted are:

- Main directory `PairsResults_5_30` to hold:
- Directory for each pair. Directory contains every trade saved as `entrydate_longpair.txt` ex: `20160430_ShortZTSVRTX.txt`. This is also a specific trade's `tradeID`
- Text file `MasterResults.txt` where each row contains each trade in our backtest that is used in Part III.

#### Directory Tree Preview
```bash
- PairsResults_5_30
  |-  MasterResults.txt
  |-  Stock1_Stock2
      |--20160430_ShortStock1Stock2.txt
      |--20161002_LongStock1Stock2.txt
  |-  Stock1_Stock3
  |-  Stock1_Stock4
```

8. A `tradeID` is created to link trades within the `MasterResults.txt` file and their subdirectory trade file generated

### Part III - Analyze Trade Results - `trade_analysis.py`

Variable `params` needs to match the directory ending created in Part II. For example, in the previous python script `pairs_backtester.py` the directory created is `PairsResults_5_30`. Therefore `params` needs to equal `_5_30`.

```python
## these parameters impact file name and sub-folder to gather data from
params = "_5_30"
```
##### Trade Statistics
`MasterResults.txt` file includes all trade related data to compute our trade statistics. Method `trade_stats` takes care of evaluating these trade results and returns a list with trade statistics.

##### Daily Statistics
To compute daily statistics, we need to loop through a range of dates, and for each date, verify if we have any open trades. Using `tradeID` from our `MasterResults.txt` file, I created a path to the individual trade data which includes daily PnL for a given trade (amongst other daily trade data).

A class `NewTrade()` is used to load each trade, with specific methods to return required data. Examples include returning a `tradeID`, current day's PnL when provided with a date, exit date check.

`daily_stats` method provides the looping mechanism to walk through each date. We use a dictionary `trd_holder` to store each initialized `NewTrade()` object to a key which is their `tradeID`.

When a trade needs to be removed from our dictionary, we load a trade's `tradeID` to a list called `trds_to_delete` and then loop through each `trd_holder` item and if there is a matching key to `tradeID` then we rename the key to `deleted`.

Finally, we output all data to text files:

```python
f_name = "daily_results" + params
f_name2 = "model_daily_stats" + params
f_name3 = "model_trade_stats" + params

cm.write_results_text_file(f_name, daily_pnl)
cm.write_results_text_file(f_name2, daily_statistics)
cm.write_results_text_file(f_name3, trade_statistics)
```

### Development Environment
* Spyder IDE version 3.2.8
* Python 3.6.5
* PostgreSQL 9.5.9

### Author
Antonio Constandinou
