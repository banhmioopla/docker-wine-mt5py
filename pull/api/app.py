import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import (get_current_equity, get_current_balance, 
                      get_current_mean_win_rate, build_OHLC, build_timestamp, 
                      pull_mt5, pull_and_sync_mt5, 
                      get_accounts, run_check_login, get_test_accounts,
                      get_latest_equity_details, get_latest_equity_sum,
                      get_latest_balance_details, get_latest_balance_sum,
                      get_latest_balance_by_fee
                      )
from datetime import datetime
import subprocess
import json
import lib.backend as be
import lib.constants as constants

root_path = os.getenv("ROOT_PATH", "")
app = FastAPI(
    title="MT5 Pull API",
    description="API for MT5 data pulling",
    version="1.0.0",
    root_path=root_path,  # Quan trọng: Sử dụng root_path
    # Quan trọng: Đặt URL rõ ràng cho OpenAPI schema
    openapi_url="/openapi.json", 
    docs_url="/docs",
    redoc_url="/redoc"
)

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


@app.get("/airflow/pull-mt5", include_in_schema=False)
async def airflow_pull_mt5():
    return {"message": "Welcome to Wealth Farming Hello"}


@app.get("/cron/pull-mt5", include_in_schema=False)
async def cron_pull_mt5():
    return pull_mt5()

@app.get("/cron/pull-and-sync-mt5", include_in_schema=False)
async def cron_pull_and_sync_mt5():
    return pull_and_sync_mt5()


@app.get("/cron/check-login", include_in_schema=False)
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

@app.get("/test/mt5/accounts")
async def test_mt5_accounts():
    return [acc["account_id"] for acc in get_test_accounts()]



@app.get("/backend/day-counts")
async def backend_day_counts(start = "2025-03-24", end = "2025-03-26"):
    # result : 3
    return {"result": be.day_counts(start, end)}

@app.get("/backend/to-unix-timestamp")
async def backend_day_counts(date='2025-03-25'):
    return {"result": be.to_unix_timestamp(date)}

@app.get("/backend/balance-latest/details")
async def backend_balance_latest_details(timestamp):

    by_date = be.from_unix_timestamp(int(timestamp))

    return get_latest_balance_by_fee(by_date)

@app.get("/constants/fund-start-at")
async def constants_fund_start_at():
    return {"result": constants.DATE_INIT}


@app.get("/constants/fee-management")
async def constants_fee_management():
    return {"result": constants.FEE_MANAGEMENT}
