from pathlib import Path
import os
import pandas as pd
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mt5linux import MetaTrader5
import json

from datetime import datetime, timedelta, timezone

from database import engine, HistoryDeals, BrokerAccounts, HistoryDealsTest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, desc
from decimal import Decimal, ROUND_HALF_UP

RESOURCES_DIR = Path(__file__).resolve().parent.parent / 'resources'
MT5_HOST = os.getenv('MT5_HOST')
MT5_PORT = os.getenv('MT5_PORT')

def pull_data_accounts(mt5, mt5_accounts):

    from_date = int(datetime(2015, 1, 1).timestamp())
    to_date = int((datetime.now() + timedelta(days=1)).timestamp())

    
    data = []
    for login in mt5_accounts:
        ok = mt5.login(login["account_id"], login["password"], login["server"])
        if(ok == None): continue
        history_orders_dict = []
        history_deals_dict  = []

        history_orders = mt5.history_orders_get(from_date, to_date)

        if history_orders:
            history_orders_dict = [order._asdict() for order in history_orders]
        
        history_deals = mt5.history_deals_get(from_date, to_date)
    
        if history_deals:
            history_deals_dict = [deal._asdict() for deal in history_deals]
        
        positions = mt5.positions_get()
        positions_list = []
        if positions:
            for pos in positions:
                positions_list.append(pos._asdict())

        orders = mt5.orders_get()
        orders_list = []
        if orders:
            for order in orders:
                orders_list.append(order._asdict())

        login_data = {
            "account": mt5.account_info()._asdict(),
            "terminal_info": mt5.terminal_info()._asdict(),
            "terminal_version": mt5.version(),
            "history_deals": history_deals_dict,
            "history_orders": history_orders_dict,
            "positions": positions_list
        }
        data.append(login_data)
        # sync_latest_deals
    mt5.shutdown()
    return data

def sync_latest_deals(mt5, mt5_data):
    Session = sessionmaker(bind=engine)
    session = Session()

    history_deals = mt5_data['history_deals']
    model = HistoryDealsTest
    
    _balance_to_deal = 0
    _latest_timestamp = 0
    _win_rate_to_deal = 0
    _win_count_to_deal = 0
    _count_to_deal = 0
    

    latest_deal = session.query(model).filter(
            model.account_id == str(mt5_data['account']['login']),
        ).order_by(desc(model.timestamp)).first()
    
    
    
    if(latest_deal != None):
        _latest_timestamp = latest_deal.timestamp
        _balance_to_deal  = latest_deal.account_balance
        _win_rate_to_deal = latest_deal.win_rate
        _win_count_to_deal = latest_deal.deal_win_count
        _count_to_deal = latest_deal.deal_count

    mt5_latest_deals = [deal for deal in history_deals 
        if deal["time"] >= _latest_timestamp
    ]
    
    # sync new deals Entry Out!
    for _item in mt5_latest_deals:
        
        _is_exist = session.query(model).filter(
            model.account_id == str(mt5_data['account']['login']),
            model.deal_id == _item["ticket"]
        ).order_by(desc(model.timestamp)).first()
        
        
        
        if _is_exist == None:
            _balance_to_deal += Decimal(_item["profit"])
            if _item["type"] in [mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL] and _item["entry"] in [mt5.DEAL_ENTRY_OUT]: 
                _count_to_deal += 1

                if _item["profit"] > 0 : 
                    _win_count_to_deal += 1
                _win_rate_to_deal = _win_count_to_deal / _count_to_deal

            if  _item["entry"] in [mt5.DEAL_ENTRY_OUT] or _item["type"] in [mt5.DEAL_TYPE_BALANCE]:
                # Add new to table
                record = model(
                    timestamp = _item["time"],
                    timestamp_iso = timestamp_to_date(_item["time"]).isoformat(),
                    account_id = mt5_data['account']['login'],
                    account_balance = round(_balance_to_deal, 2),
                    account_equity =  round(_balance_to_deal, 2),
                    win_rate = _win_rate_to_deal,
                    deal_log = json.dumps(_item, default=str),
                    deal_win_count = _win_count_to_deal,
                    deal_count = _count_to_deal,
                    deal_id = _item['ticket']
                )
                session.add(record)
                session.commit()
    # end For loop
    

    # update realtime mt5 data to latest deal
    latest_deal = session.query(model).filter(
            model.account_id == str(mt5_data['account']['login']),
        ).order_by(desc(model.timestamp)).first()
    
    latest_deal.account_balance = mt5_data['account']['balance']
    latest_deal.account_equity  = mt5_data['account']['equity']
    session.commit()
    pass


def save_history_deal():
    pass

def get_mt5_accounts():

    CSV_PATH = RESOURCES_DIR / 'exness-mt5-accounts-trial.csv'
    
    df = pd.read_csv(CSV_PATH, header=None)
    data = df.to_dict(orient='split')['data']
    flattened_data = [item for sublist in data for item in sublist]
    convert_to_objects = [
        {"server": item.split(";")[0], "account_id": item.split(";")[1], "password": item.split(";")[2]}
        for item in flattened_data
    ]
    return convert_to_objects


def timestamp_to_date(unix_time):
        return datetime.fromtimestamp(unix_time, tz=timezone.utc).date()
    

def main():
    mt5_accounts = get_mt5_accounts()
    mt5 = MetaTrader5(MT5_HOST,MT5_PORT)
    mt5.initialize()
    pull_data = pull_data_accounts(mt5, mt5_accounts) # [accounts data]

    for mt5_data in pull_data:
        sync_latest_deals(mt5, mt5_data)

if __name__ == "__main__":
    main()