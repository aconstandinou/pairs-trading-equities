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

### For all Python Scripts - `common_methods.py`
This python file holds many methods that are used across many of the python scripts. It was built with the desire to DRY my code and reuse as many methods as possible.

### Step 1) Identify Equity Pairs that are Cointegrated - `aug_dickey_fuller_test.py`

### Step 2) Backtest Equity Pairs - `pairs_backtester.py`

### Step 3) Analyze Trade Results - `trade_analysis.py`

### Development Environment
* Spyder IDE version 3.2.8
* Python 3.6.5
* PostgreSQL 9.5.9

### Author
Antonio Constandinou
