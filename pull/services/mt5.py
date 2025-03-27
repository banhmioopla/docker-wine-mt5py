import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.mt5 import (get_mt5_accounts, pull_data_accounts, 
                     get_test_mt5_accounts,
                     sync_latest_deals, check_login, 
                     get_latest_equity, 
                     get_latest_equity_sum as equity_sum,
                     get_latest_balance, 
                     get_latest_balance_by_fee as balance_by_fee,
                     get_latest_balance_sum as balance_sum,
                     day_counts
                     )
from mt5linux import MetaTrader5
import lib.constants as constants
import json
fee_management = 0.05

def pull_mt5():
    
    MT5_HOST = os.getenv('MT5_HOST')
    MT5_PORT = os.getenv('MT5_PORT')
    print("HOST PORT", MT5_HOST, MT5_PORT)
    mt5_accounts = get_mt5_accounts()
    mt5 = MetaTrader5('mt5app', '8001')
    mt5.initialize()
    pull_data = pull_data_accounts(mt5, mt5_accounts) # [accounts data]
    # print(pull_data)
    return {"data": mt5_accounts, "pull_data": pull_data}

    # return {"data": pull_data}

def pull_and_sync_mt5():
    MT5_HOST = os.getenv('MT5_HOST')
    MT5_PORT = os.getenv('MT5_PORT')
    mt5_accounts = get_mt5_accounts()
    mt5 = MetaTrader5(MT5_HOST,MT5_PORT)
    mt5.initialize()
    pull_data = pull_data_accounts(mt5, mt5_accounts) # [accounts data]

    for mt5_data in pull_data:
        sync_latest_deals(mt5, mt5_data)
    
    return {"status": "ok ?!"}

def get_accounts():
    return get_mt5_accounts()

def get_test_accounts():
    return get_test_mt5_accounts()

def get_latest_equity_details():
    return get_latest_equity()

def get_latest_equity_sum():
    return equity_sum()

def get_latest_balance_details():
    return get_latest_balance()

def get_latest_balance_by_fee(date):
    return {
        'balance_by_fee': balance_by_fee(date),
        'balance_original' : get_latest_balance(),
        'query': {
            'fee_management': constants.FEE_MANAGEMENT,
            'day_counts':  day_counts(constants.DATE_INIT, date),
            'fund_start_at': constants.DATE_INIT,
            'date': date
        }
    }

def get_latest_balance_sum():
    return balance_sum()

def run_check_login():
    MT5_HOST = os.getenv('MT5_HOST')
    MT5_PORT = os.getenv('MT5_PORT')
    mt5_accounts = get_mt5_accounts()
    mt5 = MetaTrader5(MT5_HOST,MT5_PORT)
    mt5.initialize()
    return check_login(mt5, mt5_accounts)