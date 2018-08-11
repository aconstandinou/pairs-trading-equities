# Building an Equity Pairs Trading Model

###### This project is meant to use python and the stattools library in building a pairs trading model. There is also code that utilizes a previously built PostgreSQL database of stock data to find pairs of stocks that exhibit cointegration. By using my equity data warehouse (built with PostgreSQL and Python) the project that follows builds a rolling cointegrated pairs trading model.

###### The tests that follow are part of a blog series I've written over on Medium to tackle interesting quantitative research projects.

###### Link: https://medium.com/@constandinou.antonio
###### Title of blog post - *Quant Post 3.2: Building a Pairs Trading Model*

### Getting Started
If you plan on using this code along with the equity database, please reference the following link before moving forward: https://github.com/aconstandinou/data-warehouse-build

Otherwise, you will need to change how the following python scripts access market data.

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

### Useful Information

### For all Python Scripts
`common_methods.py`
This python file holds many methods that are used across many of the python scripts. It was built with the desire to DRY my code and reuse as many methods as possible.

File is imported as `cm` in all the following scripts.

`database_info.txt`
This text file holds database credentials needed to connect to a PostgreSQL database built in a previous project (link above). Specifically, the file holds four necessary identifiers: database_host, database_user, database_password, database_name

The only specific identifier that was previously set was the database_name as 'securities_master'. All other details will be specific to your machine.

### Step 1) Identify Equity Pairs that are Cointegrated - `identifying_pairs.py`
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

8. Output a text file ex: `coint_method_pairs_20061229.txt` that contains cointegrated pairs for all sectors. The date included in the text file name is the last day of data in our training year. Pairs are used in the following year for backtesting in step 2 below. Each row in text file contains `Sector,Pair1,Pair2`.

### Step 2) Backtest Equity Pairs - `pairs_backtester.py`

### Step 3) Analyze Trade Results - `trade_analysis.py`

### Development Environment
* Spyder IDE version 3.2.8
* Python 3.6.5
* PostgreSQL 9.5.9

### Author
Antonio Constandinou
