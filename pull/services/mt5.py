import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.mt5 import get_mt5_accounts, pull_data_accounts, sync_latest_deals
from mt5linux import MetaTrader5
import json

def pull_mt5():
    
    MT5_HOST = os.getenv('MT5_HOST')
    MT5_PORT = os.getenv('MT5_PORT')
    print("HOST PORT", MT5_HOST, MT5_PORT)
    mt5_accounts = get_mt5_accounts()
    mt5 = MetaTrader5('mt5app', '8001')
    mt5.initialize()
    # pull_data = pull_data_accounts(mt5, mt5_accounts) # [accounts data]
    # print(pull_data)
    return {"data": "test pull mt5"}

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
    
    return {"accounts": [acc["account_id"] for acc in mt5_accounts]}