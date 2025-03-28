import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import func, desc, cast, Date, extract, distinct
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pandas as pd
from database import engine, HistoryDeals, BrokerAccounts, HistoryDealsTest
from lib.mt5 import cal_balance_after_fee
from lib.backend import from_unix_timestamp

def get_hourly_balance_chart(timeframe='H1', hours=24):
    """
    Tính tổng balance của tất cả account MT5 theo từng giờ.
    
    Parameters:
    - timeframe: Khung thời gian, mặc định là 'H1' (1 giờ)
    - hours: Số giờ cần lấy dữ liệu, mặc định là 24
    
    Returns:
    - Dictionary chứa timeseries dữ liệu
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Tính thời gian bắt đầu (24 giờ trước)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Chuyển đổi thành timestamp
        start_timestamp = int(start_time.timestamp())
        
        # Lấy tất cả bản ghi trong khoảng thời gian
        all_records = (
            session.query(
                HistoryDeals.id,
                HistoryDeals.account_id,
                HistoryDeals.timestamp,
                HistoryDeals.account_balance
            )
            .filter(HistoryDeals.timestamp >= start_timestamp)
            .order_by(HistoryDeals.account_id, HistoryDeals.timestamp, HistoryDeals.id)
            .all()
        )
        
        # Xử lý dữ liệu bằng Python để tối ưu
        hour_buckets = {}
        latest_records = {}
        
        # Tạo các bucket trống cho 24 giờ
        hour_keys = []
        for i in range(hours):
            hour_time = end_time - timedelta(hours=hours-i-1)
            hour_str = hour_time.strftime("%Y-%m-%d %H:00")
            hour_buckets[hour_str] = []
            hour_keys.append(hour_str)
        
        # Gom các bản ghi vào bucket theo giờ
        for record in all_records:
            # Chuyển đổi timestamp thành số nguyên
            timestamp_value = int(float(record.timestamp))
            record_time = datetime.fromtimestamp(timestamp_value)
            hour = record_time.strftime("%Y-%m-%d %H:00")
            
            if hour in hour_buckets:
                # Lưu bản ghi mới nhất cho mỗi account trong mỗi giờ
                key = (hour, record.account_id)
                if key not in latest_records or record.id > latest_records[key].id:
                    latest_records[key] = record
        
        # Tìm giờ đầu tiên có dữ liệu
        first_valid_balance = None
        first_valid_hour_index = None
        
        for i, hour in enumerate(hour_keys):
            hour_records = [record for (h, _), record in latest_records.items() if h == hour]
            if hour_records:
                first_valid_balance = sum(float(record.account_balance) for record in hour_records)
                first_valid_hour_index = i
                break
        
        # Nếu không tìm thấy dữ liệu nào, trả về giá trị 0 cho tất cả giờ
        if first_valid_balance is None:
            hourly_data = [{
                "time": hour,
                "balance": 0.0
            } for hour in hour_keys]
            
            return {
                "timeframe": timeframe,
                "period": f"{hours} hours",
                "data": hourly_data
            }
        
        # Tính tổng balance cho mỗi giờ
        hourly_data = []
        current_balance = first_valid_balance
        
        for i, hour in enumerate(hour_keys):
            # Nếu đây là giờ trước giờ đầu tiên có dữ liệu, sử dụng giá trị của giờ đầu tiên
            if i < first_valid_hour_index:
                total_balance = first_valid_balance
            else:
                # Lấy tất cả bản ghi mới nhất cho giờ này
                hour_records = [record for (h, _), record in latest_records.items() if h == hour]
                
                if hour_records:
                    total_balance = sum(float(record.account_balance) for record in hour_records)
                    current_balance = total_balance
                else:
                    # Sử dụng balance của giờ trước nếu không có dữ liệu
                    total_balance = current_balance
            
            hourly_data.append({
                "time": hour,
                "balance": float(total_balance)
            })
        
        return {
            "timeframe": timeframe,
            "period": f"{hours} hours",
            "data": hourly_data
        }
    finally:
        session.close() 

def get_hourly_balance_by_fee_chart(timeframe='H1', hours=24):
    """
    Tính tổng balance của tất cả account MT5 theo từng giờ.
    
    Parameters:
    - timeframe: Khung thời gian, mặc định là 'H1' (1 giờ)
    - hours: Số giờ cần lấy dữ liệu, mặc định là 24
    
    Returns:
    - Dictionary chứa timeseries dữ liệu
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Tính thời gian bắt đầu (24 giờ trước)
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Chuyển đổi thành timestamp
        start_timestamp = int(start_time.timestamp())
        
        # Lấy tất cả bản ghi trong khoảng thời gian
        all_records = (
            session.query(
                HistoryDeals.id,
                HistoryDeals.account_id,
                HistoryDeals.timestamp,
                HistoryDeals.account_balance
            )
            .filter(HistoryDeals.timestamp >= start_timestamp)
            .order_by(HistoryDeals.account_id, HistoryDeals.timestamp, HistoryDeals.id)
            .all()
        )
        
        # Xử lý dữ liệu bằng Python để tối ưu
        hour_buckets = {}
        latest_records = {}
        
        # Tạo các bucket trống cho 24 giờ
        hour_keys = []
        for i in range(hours):
            hour_time = end_time - timedelta(hours=hours-i-1)
            hour_str = hour_time.strftime("%Y-%m-%d %H:00")
            hour_buckets[hour_str] = []
            hour_keys.append(hour_str)
        
        # Gom các bản ghi vào bucket theo giờ
        for record in all_records:
            # Chuyển đổi timestamp thành số nguyên
            timestamp_value = int(float(record.timestamp))
            record_time = datetime.fromtimestamp(timestamp_value)
            hour = record_time.strftime("%Y-%m-%d %H:00")
            
            if hour in hour_buckets:
                # Lưu bản ghi mới nhất cho mỗi account trong mỗi giờ
                key = (hour, record.account_id)
                if key not in latest_records or record.id > latest_records[key].id:
                    latest_records[key] = record
        
        # Tìm giờ đầu tiên có dữ liệu
        first_valid_balance = None
        first_valid_hour_index = None
        
        for i, hour in enumerate(hour_keys):
            hour_records = [record for (h, _), record in latest_records.items() if h == hour]
            if hour_records:
                first_valid_balance = sum(float(record.account_balance) for record in hour_records)
                first_valid_hour_index = i
                break
        
        # Nếu không tìm thấy dữ liệu nào, trả về giá trị 0 cho tất cả giờ
        if first_valid_balance is None:
            hourly_data = [{
                "time": hour,
                "balance": 0.0
            } for hour in hour_keys]
            
            return {
                "timeframe": timeframe,
                "period": f"{hours} hours",
                "data": hourly_data
            }
        
        # Tính tổng balance cho mỗi giờ
        hourly_data = []
        current_balance = first_valid_balance
        
        for i, hour in enumerate(hour_keys):
            # Nếu đây là giờ trước giờ đầu tiên có dữ liệu, sử dụng giá trị của giờ đầu tiên
            if i < first_valid_hour_index:
                total_balance = first_valid_balance
            else:
                # Lấy tất cả bản ghi mới nhất cho giờ này
                hour_records = [record for (h, _), record in latest_records.items() if h == hour]
                
                if hour_records:
                    total_balance = sum(float(record.account_balance) for record in hour_records)
                    current_balance = total_balance
                else:
                    # Sử dụng balance của giờ trước nếu không có dữ liệu
                    total_balance = current_balance
            
            only_date = hour.split()[0]
            balance_by_fee = cal_balance_after_fee(total_balance, only_date)
            
            hourly_data.append({
                "time": hour,
                "balance": float(balance_by_fee)
            })
        
        return {
            "timeframe": timeframe,
            "period": f"{hours} hours",
            "data": hourly_data
        }
    finally:
        session.close() 
