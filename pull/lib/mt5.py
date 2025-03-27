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
from sqlalchemy import and_, desc, func
from decimal import Decimal, ROUND_HALF_UP
import lib.constants as constants

RESOURCES_DIR = Path(__file__).resolve().parent.parent / 'resources'
MT5_HOST = os.getenv('MT5_HOST')
MT5_PORT = os.getenv('MT5_PORT')
DATE_INIT = '2025-03-24'
FEE_MANAGEMENT = 0.05

def pull_data_accounts(mt5, mt5_accounts):

    from_date = int(datetime(2015, 1, 1).timestamp())
    to_date = int((datetime.now() + timedelta(days=1)).timestamp())

    
    data = []
    for login in mt5_accounts:
        # ok = mt5.login(login["account_id"], login["password"], login["server"])
        if not mt5.initialize(login=int(login["account_id"]), server=login["server"],password=login["password"]): continue
        # if(ok == None): continue
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
    model = HistoryDeals
    
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

def get_test_mt5_accounts():

    CSV_PATH = RESOURCES_DIR / 'exness-mt5-accounts-trial dev.csv'
    
    df = pd.read_csv(CSV_PATH, header=None)
    data = df.to_dict(orient='split')['data']
    flattened_data = [item for sublist in data for item in sublist]
    convert_to_objects = [
        {"server": item.split(";")[0], "account_id": item.split(";")[1], "password": item.split(";")[2]}
        for item in flattened_data
    ]
    return convert_to_objects

def check_login(mt5, mt5_accounts):
    data = []
    for login in mt5_accounts:
        # ok = mt5.login(login["account_id"], login["password"], login["server"])
        
        if not mt5.initialize(login=int(login["account_id"]), server=login["server"],password=login["password"]):
            data.append(mt5.last_error())
        data.append(mt5.account_info()._asdict())

    mt5.shutdown()
    return data
def timestamp_to_date(unix_time):
        return datetime.fromtimestamp(unix_time, tz=timezone.utc).date()


def get_latest_equity():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Truy vấn con để lấy timestamp mới nhất cho mỗi account_id
        latest_timestamp_subquery = (
            session.query(
                HistoryDeals.account_id,
                func.max(HistoryDeals.timestamp).label("max_timestamp")
            )
            .group_by(HistoryDeals.account_id)
            .subquery()
        )
        
        # Lấy ID lớn nhất (bản ghi mới nhất) cho mỗi account_id với timestamp mới nhất
        latest_id_subquery = (
            session.query(
                HistoryDeals.account_id,
                func.max(HistoryDeals.id).label("max_id")
            )
            .join(
                latest_timestamp_subquery,
                (HistoryDeals.account_id == latest_timestamp_subquery.c.account_id) &
                (HistoryDeals.timestamp == latest_timestamp_subquery.c.max_timestamp)
            )
            .group_by(HistoryDeals.account_id)
            .subquery()
        )
        
        # Join với bảng chính dựa trên ID để đảm bảo chỉ lấy bản ghi mới nhất
        latest_records = (
            session.query(
                HistoryDeals.account_id,
                HistoryDeals.account_equity,
                HistoryDeals.timestamp,
                HistoryDeals.timestamp_iso
            )
            .join(
                latest_id_subquery,
                (HistoryDeals.account_id == latest_id_subquery.c.account_id) &
                (HistoryDeals.id == latest_id_subquery.c.max_id)
            )
            .all()
        )
        
        # Tính tổng
        total_equity = sum(record.account_equity for record in latest_records)
        
        return {
            "accounts": [
                {
                    "account_id": record.account_id,
                    "account_equity": float(record.account_equity),
                    "timestamp": float(record.timestamp),
                    "timestamp_iso": record.timestamp_iso
                } for record in latest_records
            ],
            "total_equity": float(total_equity)
        }
    finally:
        session.close()

def get_latest_equity_sum():
    Session = sessionmaker(bind=engine)
    session = Session()
    # Truy vấn con để lấy timestamp mới nhất cho mỗi account_id
    latest_timestamp_subquery = (
        session.query(
            HistoryDeals.account_id,
            func.max(HistoryDeals.timestamp).label("max_timestamp")
        )
        .group_by(HistoryDeals.account_id)
        .subquery()
    )
    
    # Join với bảng chính để lấy các bản ghi với timestamp mới nhất
    latest_equity_records = (
        session.query(HistoryDeals)
        .join(
            latest_timestamp_subquery,
            (HistoryDeals.account_id == latest_timestamp_subquery.c.account_id) &
            (HistoryDeals.timestamp == latest_timestamp_subquery.c.max_timestamp)
        )
    )
    
    # Tính tổng account_equity từ các bản ghi mới nhất
    total_equity = session.query(func.sum(HistoryDeals.account_equity)).filter(
        HistoryDeals.id.in_([record.id for record in latest_equity_records])
    ).scalar() or 0
    
    return total_equity

def get_latest_balance_sum():
    Session = sessionmaker(bind=engine)
    session = Session()
    # Truy vấn con để lấy timestamp mới nhất cho mỗi account_id
    latest_timestamp_subquery = (
        session.query(
            HistoryDeals.account_id,
            func.max(HistoryDeals.timestamp).label("max_timestamp")
        )
        .group_by(HistoryDeals.account_id)
        .subquery()
    )
    
    # Join với bảng chính để lấy các bản ghi với timestamp mới nhất
    latest_balance_records = (
        session.query(HistoryDeals)
        .join(
            latest_timestamp_subquery,
            (HistoryDeals.account_id == latest_timestamp_subquery.c.account_id) &
            (HistoryDeals.timestamp == latest_timestamp_subquery.c.max_timestamp)
        )
    )
    
    # Tính tổng account_balance từ các bản ghi mới nhất
    total_balance = session.query(func.sum(HistoryDeals.account_balance)).filter(
        HistoryDeals.id.in_([record.id for record in latest_balance_records])
    ).scalar() or 0
    
    return total_balance

def get_latest_balance():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Truy vấn con để lấy timestamp mới nhất cho mỗi account_id
        latest_timestamp_subquery = (
            session.query(
                HistoryDeals.account_id,
                func.max(HistoryDeals.timestamp).label("max_timestamp")
            )
            .group_by(HistoryDeals.account_id)
            .subquery()
        )
        
        # Lấy ID lớn nhất (bản ghi mới nhất) cho mỗi account_id với timestamp mới nhất
        latest_id_subquery = (
            session.query(
                HistoryDeals.account_id,
                func.max(HistoryDeals.id).label("max_id")
            )
            .join(
                latest_timestamp_subquery,
                (HistoryDeals.account_id == latest_timestamp_subquery.c.account_id) &
                (HistoryDeals.timestamp == latest_timestamp_subquery.c.max_timestamp)
            )
            .group_by(HistoryDeals.account_id)
            .subquery()
        )
        
        # Join với bảng chính dựa trên ID để đảm bảo chỉ lấy bản ghi mới nhất
        latest_records = (
            session.query(
                HistoryDeals.account_id,
                HistoryDeals.account_balance,
                HistoryDeals.timestamp,
                HistoryDeals.timestamp_iso
            )
            .join(
                latest_id_subquery,
                (HistoryDeals.account_id == latest_id_subquery.c.account_id) &
                (HistoryDeals.id == latest_id_subquery.c.max_id)
            )
            .all()
        )
        
        # Tính tổng
        total_balance = sum(record.account_balance for record in latest_records)
        
        return {
            "accounts": [
                {
                    "account_id": record.account_id,
                    "account_balance": float(record.account_balance),
                    "timestamp": float(record.timestamp),
                    "timestamp_iso": record.timestamp_iso
                } for record in latest_records
            ],
            "total_balance": float(total_balance)
        }
    finally:
        session.close()


def get_latest_balance_by_fee(by_date):
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Truy vấn con để lấy timestamp mới nhất cho mỗi account_id
        latest_timestamp_subquery = (
            session.query(
                HistoryDeals.account_id,
                func.max(HistoryDeals.timestamp).label("max_timestamp")
            )
            .group_by(HistoryDeals.account_id)
            .subquery()
        )
        
        # Lấy ID lớn nhất (bản ghi mới nhất) cho mỗi account_id với timestamp mới nhất
        latest_id_subquery = (
            session.query(
                HistoryDeals.account_id,
                func.max(HistoryDeals.id).label("max_id")
            )
            .join(
                latest_timestamp_subquery,
                (HistoryDeals.account_id == latest_timestamp_subquery.c.account_id) &
                (HistoryDeals.timestamp == latest_timestamp_subquery.c.max_timestamp)
            )
            .group_by(HistoryDeals.account_id)
            .subquery()
        )
        
        # Join với bảng chính dựa trên ID để đảm bảo chỉ lấy bản ghi mới nhất
        latest_records = (
            session.query(
                HistoryDeals.account_id,
                HistoryDeals.account_balance,
                HistoryDeals.timestamp,
                HistoryDeals.timestamp_iso
            )
            .join(
                latest_id_subquery,
                (HistoryDeals.account_id == latest_id_subquery.c.account_id) &
                (HistoryDeals.id == latest_id_subquery.c.max_id)
            )
            .all()
        )
        
        # Tính tổng
        total_balance = sum(record.account_balance for record in latest_records)
        total_balance_after_fee = cal_balance_after_fee(total_balance, by_date)

        return {
            "accounts": [
                {
                    "account_id": record.account_id,
                    "account_balance": cal_balance_after_fee(float(record.account_balance), by_date) ,
                    "timestamp": float(record.timestamp),
                    "timestamp_iso": record.timestamp_iso
                } for record in latest_records
            ],
            "total_balance": float(total_balance_after_fee)
        }
    finally:
        session.close()


def cal_balance_after_fee(balance, date):
    counts = day_counts(constants.DATE_INIT, date)
    return float(balance) * ((1 - constants.FEE_MANAGEMENT) ** counts)

def day_counts(start, end):

    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')
    delta = (end_date - start_date).days + 1
    return delta