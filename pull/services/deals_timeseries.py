import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import engine, HistoryDeals, HistoryDealsTest, BrokerAccounts
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from datetime import datetime, timedelta, time
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
from pytz import timezone

def build_OHLC(start_timestamp, end_timestamp, timeframe, isTest = None):
    Session = sessionmaker(bind=engine)
    session = Session()
    accounts_tz = session.query(
        BrokerAccounts.platform_timezone,
        BrokerAccounts.account_id,
    ).all()

    _HistoryDeals = HistoryDeals
    if isTest == "true": 
        print("Test MODE")
        _HistoryDeals = HistoryDealsTest

    deals = session.query(
        _HistoryDeals.account_id,
        _HistoryDeals.timestamp,
        _HistoryDeals.account_equity
    ).filter(
        _HistoryDeals.timestamp >= start_timestamp,
        _HistoryDeals.timestamp <= end_timestamp,
    ).all()

    def _convert_to_UTC(_account_id, _timestamp):
        print("accounts_tz", accounts_tz)
        tz_acc = [
            tz.platform_timezone 
                for tz in accounts_tz 
                if tz.account_id == _account_id
        ]

        broker_tz = timezone(
            tz_acc[0]
        )
        print('broker_tz', broker_tz)
        utc_timezone = timezone('UTC')
        datetime_broker = datetime.fromtimestamp(_timestamp, broker_tz)
        datetime_utc = datetime_broker.astimezone(utc_timezone)
        return int(datetime_utc.timestamp())

    data = [
        {
            "timestamp": datetime
            .fromtimestamp(float(_convert_to_UTC(deal.account_id, float(deal.timestamp)))),
            "account_id": deal.account_id,
            "equity": deal.account_equity
        }
        for deal in deals
    ]
    
    if not data:
        return {"OpenTime": [], "O": [], "H": [], "L": [], "C": []}
    
    df = pd.DataFrame(data)

    if timeframe == "D1":
        df["timestamp"] = df["timestamp"].dt.date
    elif timeframe == "H1":
        df["timestamp"] = df["timestamp"].dt.floor("H")
    elif timeframe == "W1":
        df["timestamp"] = df["timestamp"].dt.to_period("W").apply(lambda r: r.start_time.date())

    ohlc_per_account = df.groupby(["account_id", "timestamp"]).agg(
        O=("equity", "first"),
        H=("equity", "max"),
        L=("equity", "min"),
        C=("equity", "last")
    ).reset_index()

    final_ohlc = ohlc_per_account.groupby("timestamp").agg(
        O=("O", "mean"),  
        H=("H", "mean"),  
        L=("L", "mean"),  
        C=("C", "mean") 
    ).reset_index()

    return {
        "OpenTime": final_ohlc["timestamp"].tolist(),
        "O": final_ohlc["O"].tolist(),
        "H": final_ohlc["H"].tolist(),
        "L": final_ohlc["L"].tolist(),
        "C": final_ohlc["C"].tolist()
    }

# Function to build timestamps with aggregated equity

def build_timestamp(start_timestamp, end_timestamp, isTest=None):
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Query broker accounts with their platform timezones
    accounts_tz = session.query(
        BrokerAccounts.platform_timezone,
        BrokerAccounts.account_id,
    ).all()
    print('accounts_tz ... ', accounts_tz)
    
    # Determine which table to use based on test mode

    _HistoryDeals = HistoryDealsTest if isTest == "true" else HistoryDeals
    print(">>> Table :: ", _HistoryDeals.__tablename__)
    print(">>> isTest :: ", isTest)
    
    # Query deal data within the specified timestamp range
    deals = session.query(
        _HistoryDeals.account_id,
        _HistoryDeals.timestamp,
        _HistoryDeals.account_equity
    ).filter(
        _HistoryDeals.timestamp >= start_timestamp,
        _HistoryDeals.timestamp <= end_timestamp,
    ).all()
    
    # Function to convert timestamp from broker's timezone to UTC
    def _convert_to_UTC(_account_id, _timestamp):
        try:
            broker_tz_str = next(
                tz.platform_timezone for tz in accounts_tz if tz.account_id == str(_account_id)
            )
            broker_tz = timezone(broker_tz_str)
            utc_timezone = timezone('UTC')
            datetime_broker = datetime.fromtimestamp(_timestamp, broker_tz)
            datetime_utc = datetime_broker.astimezone(utc_timezone)
            return int(datetime_utc.timestamp())
        except StopIteration:
            print(f"Warning: No timezone found for account_id {_account_id}")
            return int(_timestamp)  # Fallback to original timestamp if timezone is missing
    
    # Convert deals to UTC timestamps and prepare structured data
    data = []
    for deal in deals:
        converted_timestamp = _convert_to_UTC(deal.account_id, float(deal.timestamp))
        data.append({
            "timestamp": converted_timestamp,
            "account_id": deal.account_id,
            "equity": float(deal.account_equity)  # Ensure equity is numeric
        })
    
    if not data:
        return {"timestamp": [], "equity_sum": []}
    
    # Create a DataFrame from the extracted data
    df = pd.DataFrame(data)
    
    # Sort data by timestamp and account_id
    df = df.sort_values(by=["timestamp", "account_id"])
    
    # Ensure 'equity' column is of numeric type
    df["equity"] = pd.to_numeric(df["equity"], errors='coerce')
    
    # Compute mean equity for timestamps that have multiple records
    df["equity"] = df.groupby("timestamp")["equity"].transform("mean")
    df = df.drop_duplicates(subset=["timestamp"], keep='first')

    print('df', df.head(10))
    
    # Compute sum of equity only when account_id is different for the same timestamp
    equity_sum_per_timestamp = df.groupby("timestamp").agg(
        equity_sum=("equity", "sum")
    ).reset_index()
    
    # Return the equity sums grouped by timestamp
    return {
        "timestamp": equity_sum_per_timestamp["timestamp"].tolist(),
        "equity_sum": equity_sum_per_timestamp["equity_sum"].tolist()
    }
