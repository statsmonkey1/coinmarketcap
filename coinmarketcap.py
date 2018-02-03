# -*- coding: utf-8 -*-
"""
Created on Sat Feb  3 14:18:22 2018


"""
import pandas as pd
import numpy as np
from steem import Steem
import requests
import matplotlib.pyplot as plt
import dropbox
import matplotlib.dates as mdates
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sys

"""
*******************************************************************************
PARAMETERS
*******************************************************************************
"""

# Output folder location where graphs are stored before uploading to dropbox
# *** MAKE SURE YOU USE / AND NOT \ ***
# also make sure you end with a  "/"
output_folder = "C:/steemit/Plots/"

# Which currency to create the report for
currency = "steem"

# Dropbox access token to upload/host graphs from dropbox
#dropbox_access_token = 'xxxxxxx'
dropbox_access_token = 'xxxxxxx'

# Parameters for RSI respectively

RSI_PERIOD = 14

# Parameters for RSI graph
OVERBOUGHT = 70
OVERSOLD = 30
MIDDLE = 50

# Indicate range of data for analysis. e.g. 40 = last 40 days of data
data_window = 40

# Email to send alerts to
from_email = "email@gmail.com"

# Password for from_email
from_pswd = "password"

# Where to send emails to
to_email = "email2@gmail.com"

"""
*******************************************************************************
*******************************************************************************
"""
#%% Function to send email alerts

def emailer(currency, body, from_email, from_pswd, to_email):
    fromaddr = from_email
    toaddr = to_email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Error posting Steemit post: " + currency
     
    msg.attach(MIMEText(body, 'plain'))
     
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, from_pswd)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

#%% Grab data from coinmarketcap

try: # Try pulling data from coinmarketcap
    link = 'https://graphs2.coinmarketcap.com/currencies/' + currency
    
    df = pd.DataFrame(requests.get(link).json())
    
    
    df2 = pd.concat([pd.DataFrame([x for x in df[df.columns[y]]], columns = ['Date', df.columns[y]]).set_index('Date', drop = True) for y in range(len(df.columns))],axis = 1)
    
    df2.index = pd.to_datetime(df2.index, unit = 'ms').date
    
    df2 = df2[~df2.index.duplicated(keep='first')]
except: # If the above fails, send a notification email
    body_ = "Error pulling market data from coinmarketcap.com. Try going to " + link + " to see if any data appears"
    emailer(currency, body_, from_email, from_pswd, to_email)
    sys.exit()

#%% do calculations to get Rsi, etc.

try: # Try doing calculations for plots
    RSI_ALPHA = 1/RSI_PERIOD
    RSI_1_ALPHA = 1-RSI_ALPHA
    
   
    df2['d_price'] = df2['price_usd'] - df2['price_usd'].shift()
    
    df2['U'] = df2[df2['d_price']>0]['d_price']
    df2['U'] = df2['U'].replace(np.nan, 0)
    
    df2['D'] = -df2[df2['d_price']<0]['d_price']
    df2['D'] = df2['D'].replace(np.nan, 0)
    
    df2.ix[df2.index[0], 'SMMA_U'] = 0
    df2.ix[df2.index[0], 'SMMA_D'] = 0
    
    for x in df2.index[1:]:
        df2.ix[x, 'SMMA_U'] = RSI_ALPHA*df2.ix[x,'U'] + RSI_1_ALPHA*df2.shift().ix[x,'SMMA_U']
        df2.ix[x, 'SMMA_D'] = RSI_ALPHA*df2.ix[x,'D'] + RSI_1_ALPHA*df2.shift().ix[x,'SMMA_D']
    
    df2['RS'] = df2['SMMA_U']/df2['SMMA_D']
    df2['RSI'] = 100 - (100/(1+df2['RS']))
    
    df2['OVERBOUGHT'] = OVERBOUGHT
    df2['OVERSOLD'] = OVERSOLD
    df2['MIDDLE'] = MIDDLE
    
        
except: # Send email if above fails
    body_ = "An error occured conducting calculations for charts. That data is reading in correctly."
    emailer(currency, body_, from_email, from_pswd, to_email)
    sys.exit()
    
#%% PLOTS

   RSI_PLOT, ax = plt.subplots(2, figsize = (12,8))
    ax[0].plot(df3['price_usd'], alpha = 0.7, lw = 2.0, label = currency + " price (USD)")
    ax[1].plot(df3['RSI'], alpha = 0.7, lw = 2.0, label = 'RSI', color = 'r')
    ax[1].plot(df3['OVERBOUGHT'], alpha = 0.7, lw = 2.0, label = 'Overbought(70)', ls = "--", color = 'k')
    ax[1].plot(df3['MIDDLE'], alpha = 0.7, lw = 2.0, label = 'Middle(50)', color = 'k')
    ax[1].plot(df3['OVERSOLD'], alpha = 0.7, lw = 2.0, label = 'Undersold(30)', ls = "--", color = 'k')
    for x in ax:
        x.spines['right'].set_color('none')
        x.spines['top'].set_color('none')
        
    ax[1].spines['bottom'].set_position('zero')   
    ax[1].axes.get_xaxis().set_visible(False)
    ax[0].set_xticklabels(ax[0].xaxis.get_majorticklabels(), rotation=30)
    myFmt = mdates.DateFormatter('%m/%d/%y')
    ax[0].xaxis.set_major_formatter(myFmt)
    ax[0].xaxis.set_ticks_position('bottom')
    ax[0].yaxis.set_ticks_position('left')
    ax[1].yaxis.set_ticks_position('left')
    ax[0].legend(loc=2)
    ax[1].legend(loc=3, ncol = 4)
    ax[1].set_ylim([0,100])


except:
    body_ = "An error occured when plotting the charts or saving them to your local drive. Check to make sure the file location you inputted is still valid."
    emailer(currency, body_, from_email, from_pswd, to_email)
    sys.exit()

#%% Function to save graphs to dropbox

def write_to_dropbox(file_from, access_token):
    dbx = dropbox.Dropbox(access_token)
    file_to = '/graphs/' + file_from.split("/")[-1]
    
    with open(file_from, 'rb') as f:
        dbx.files_upload(f.read(), file_to)
        
    url = dbx.sharing_create_shared_link(file_to).url
    url = url.replace(r"?dl=0", "?dl=1")
    return url
    
try:
    RSI_url = write_to_dropbox(RSI_file_from, dropbox_access_token)    
except:
    body_ = "An error occured when outputing the files to dropbox. Check to make sure internet is working."
    emailer(currency, body_, from_email, from_pswd, to_email)
    sys.exit()
    
#%%