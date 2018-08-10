# Mean Reversion concepts in equity market data

###### This project is meant to use python and the stattools library in evaluating mean reversion concepts. There is also code that utilizes a previously built PostgreSQL database of stock data to find pairs of stocks that exhibit cointegration. By using stock data and analyzing the data for mean reversion characteristics, we can begin to build a foundation for future analysis. Specifically, I plan on continuing this research within the framework of pairs trading equities.

###### The tests that follow are part of a blog series I've written over on Medium to tackle interesting quantitative research projects.

###### Link: https://medium.com/@constandinou.antonio

### Getting Started
If you plan on using this code along with the equity database, please reference the following link before moving forward: https://github.com/aconstandinou/data-warehouse-build

Otherwise, you will need to change all mean reversion tests to satisfy where you plan on pulling your data.

### Prerequisites
You need to have PostgreSQL and Python installed.

Here are the python libraries used in the mean reversion tests. Version numbers are included as well.

* psycopg2 version 2.7.5 (dt dec pq3)
* numpy 1.14.3
* pandas 0.23.0
* statsmodels 0.9.0
* statsmodels.api
* statsmodels.tsa.stattools
* matplotlib 2.2.2
* math
* os
* datetime

### Useful Information

### For all tests
1. All tests perform mean reversion analysis on data held in a pandas dataframe. Therefore if you plan on using the methods within each python script for your own use, ensure that the input variable to the method is a pandas dataframe.
2. Stock data used in these tests were from date range '2004-12-30' to '2010-12-30' which equates to around half of our data samples.

### Augmented Dickey Fuller Test (ADF) `aug_dickey_fuller_test.py`
1. Performs the ADF test with lags of 2 to 20.
2. Output two files: one file for t-test < 1% critical level, and one file for t-test < 5% critical level

### Hurst Exponent (HE) `he_test.py`
1. Calculates the Hurst Exponent with range 2 to 100.
2. Output a file of tickers that passed the HE test where HE < 0.5. This file is used in the `half_life.py` script for further analysis.

### Half-Life `half_life.py`
1. Output file from `he_test.py` is needed to run this python script.
2. Performs the Half-Life calculation on stocks that passed HE criteria of < 0.5.
3. Output two files: one file of tickers where Half-Life <= 50.0, second file of tickers where Half-Life > 50.0.

### Development Environment
* Spyder IDE version 3.2.8
* Python 3.6.5
* PostgreSQL 9.5.9

### Author
Antonio Constandinou
