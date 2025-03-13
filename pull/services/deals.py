import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import engine, HistoryDeals
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, desc, func
from datetime import datetime

def get_current_balance(timestamp = datetime.now().timestamp(), ):
    Session = sessionmaker(bind=engine)
    session = Session()
    _HistoryDeals = HistoryDeals()
    
    subquery = (
        session.query(
            _HistoryDeals.account_id,
            func.max(_HistoryDeals.timestamp).label("max_timestamp")
        )
        .filter(_HistoryDeals.timestamp <= timestamp)
        .group_by(_HistoryDeals.account_id)
        .subquery()
    )

    query = (
        session.query(func.sum(_HistoryDeals.account_balance))
        .join(subquery, and_(
            _HistoryDeals.account_id == subquery.c.account_id,
            _HistoryDeals.timestamp == subquery.c.max_timestamp
        ))
    )

    return query.scalar()


def get_current_equity(timestamp = datetime.now().timestamp()):
    Session = sessionmaker(bind=engine)
    session = Session()
    _HistoryDeals = HistoryDeals()
    
    subquery = (
        session.query(
            _HistoryDeals.account_id,
            func.max(_HistoryDeals.timestamp).label("max_timestamp")
        )
        .filter(_HistoryDeals.timestamp <= timestamp)
        .group_by(_HistoryDeals.account_id)
        .subquery()
    )

    query = (
        session.query(func.sum(HistoryDeals.account_equity))
        .join(subquery, and_(
            _HistoryDeals.account_id == subquery.c.account_id,
            _HistoryDeals.timestamp == subquery.c.max_timestamp
        ))
    )

    return query.scalar()

def get_current_mean_win_rate(timestamp = datetime.now().timestamp()):
    Session = sessionmaker(bind=engine)
    session = Session()
    _HistoryDeals = _HistoryDeals()
    
    subquery = (
        session.query(
            _HistoryDeals.account_id,
            func.max(_HistoryDeals.timestamp).label("max_timestamp")
        )
        .filter(_HistoryDeals.timestamp <= timestamp)
        .group_by(_HistoryDeals.account_id)
        .subquery()
    )

    query = (
        session.query(func.avg(_HistoryDeals.win_rate))
        .join(subquery, and_(
            _HistoryDeals.account_id == subquery.c.account_id,
            _HistoryDeals.timestamp == subquery.c.max_timestamp
        ))
    )

    return query.scalar()
