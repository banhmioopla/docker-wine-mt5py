import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import (get_current_equity, get_current_balance, 
                      get_current_mean_win_rate, build_OHLC, build_timestamp, 
                      pull_mt5, pull_and_sync_mt5, 
                      get_accounts, run_check_login, 
                      get_latest_equity_details, get_latest_equity_sum,
                      get_latest_balance_details, get_latest_balance_sum
                      )
from datetime import datetime
import subprocess
import json


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Wealth Farming Hello"}


@app.get("/airflow/pull-mt5")
async def airflow_pull_mt5():
    return {"message": "Welcome to Wealth Farming Hello"}


@app.get("/cron/pull-mt5")
async def cron_pull_mt5():
    return pull_mt5()

@app.get("/cron/pull-and-sync-mt5")
async def cron_pull_and_sync_mt5():
    return pull_and_sync_mt5()


@app.get("/cron/check-login")
async def cron_check_login():
    return run_check_login()

@app.get("/dapp/equity")
async def dapp_equity(timestamp = datetime.now().timestamp()):
    return {
        "data": {
            "balance": get_current_balance(timestamp),
            "equity": get_current_equity(timestamp),
            "mean_win_rate": get_current_mean_win_rate(timestamp),
        }
    }

@app.get("/dapp/timeseries/equity")
async def dapp_equity(start_timestamp, end_timestamp, timeframe, is_test = None):
    return {
        "data": build_OHLC((start_timestamp), (end_timestamp), timeframe, str(is_test))
    }

@app.get("/dapp/timeseries/timestamp-equity")
async def dapp_timestamp_equity(start_timestamp, end_timestamp, is_test = None):
    
    return {
        "data": build_timestamp((start_timestamp), (end_timestamp), str(is_test))
    }

@app.get("/dapp/equity-latest/details")
async def dapp_equity_latest_details():
    return get_latest_equity_details()

@app.get("/dapp/equity-latest/sum")
async def dapp_equity_latest_sum():
    return get_latest_equity_sum()


@app.get("/dapp/balance-latest/details")
async def dapp_balance_latest_details():
    return get_latest_balance_details()

@app.get("/dapp/balance-latest/sum")
async def dapp_balance_latest_sum():
    return get_latest_balance_sum()

@app.get("/mt5/accounts")
async def mt5_accounts():
    return [acc["account_id"] for acc in get_accounts()] 
