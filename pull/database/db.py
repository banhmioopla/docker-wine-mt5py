from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper, relationship
from sqlalchemy import Column, Integer, Text, JSON, TIMESTAMP, Numeric, func, create_engine
from dotenv import load_dotenv
import os
load_dotenv(override=True)
db_engine = os.getenv("DB_LOCAL_URL")
engine = create_engine(db_engine)
Base = declarative_base()
class Brokers(Base):
    __tablename__ = "brokers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    broker_name = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)
    platform_name = Column(Text, nullable=False)
    def to_dict(self):
        return {column.key: getattr(self, column.key) for column in class_mapper(self.__class__).columns}
    
class BrokerAccounts(Base):
    __tablename__ = "broker_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_logs = Column(JSON, nullable=True)  # JSONB column
    account_id = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)
    broker_name = Column(Text, nullable=False)
    platform_name = Column(Text, nullable=False)
    platform_timezone = Column(Text, nullable=True)
    def to_dict(self):
        return {column.key: getattr(self, column.key) for column in class_mapper(self.__class__).columns}
    
class HistoryDeals(Base):
    __tablename__ = "history_deals_prod_20250324"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Numeric(precision=20), nullable=True) 
    timestamp_iso = Column(Text, nullable=True)
    account_id = Column(Text, nullable=True)
    deal_log = Column(JSON, nullable=True)
    account_balance = Column(Numeric(precision=18, scale=2), nullable=True, default=0)
    account_equity = Column(Numeric(precision=18, scale=2), nullable=True, default=0)
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)
    deal_id = Column(Numeric(precision=20), nullable=True) 
    deal_win_count = Column(Numeric(precision=20), nullable=True, default=0)
    deal_count = Column(Numeric(precision=20,), nullable=True, default=0)
    win_rate = Column(Numeric(precision=10, scale=5), nullable=True, default=0)
    sharpe_ratio = Column(Numeric(precision=10, scale=5), nullable=True, default=0)
    
    def to_dict(self):
        return {column.key: getattr(self, column.key) for column in class_mapper(self.__class__).columns}

class HistoryDealsTest(Base):
    __tablename__ = "history_deals_test_518"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Numeric(precision=20), nullable=True) 
    timestamp_iso = Column(Text, nullable=True)
    account_id = Column(Text, nullable=True)
    deal_log = Column(JSON, nullable=True)
    account_balance = Column(Numeric(precision=18, scale=2), nullable=True, default=0)
    account_equity = Column(Numeric(precision=18, scale=2), nullable=True, default=0)
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)
    deal_id = Column(Numeric(precision=20), nullable=True) 
    deal_win_count = Column(Numeric(precision=20), nullable=True, default=0)
    deal_count = Column(Numeric(precision=20,), nullable=True, default=0)
    win_rate = Column(Numeric(precision=10, scale=5), nullable=True, default=0)
    sharpe_ratio = Column(Numeric(precision=10, scale=5), nullable=True, default=0)
    
    def to_dict(self):
        return {column.key: getattr(self, column.key) for column in class_mapper(self.__class__).columns}
# db_engine = "<dialect>+<driver>://<username>:<password>@<host>:<port>/<db_name>"
Base.metadata.create_all(engine)