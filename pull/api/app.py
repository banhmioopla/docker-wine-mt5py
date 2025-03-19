import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import get_current_equity, get_current_balance, get_current_mean_win_rate, build_OHLC, build_timestamp, pull_mt5
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


@app.get("/cron/pull-mt5")
async def cron_pull_mt5():
    return pull_mt5()

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
