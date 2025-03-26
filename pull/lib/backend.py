from datetime import datetime
def day_counts(start, end):
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')
    delta = (end_date - start_date).days + 1
    return delta

def to_unix_timestamp(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    timestamp = int(date_obj.timestamp())
    return timestamp

def from_unix_timestamp(timestamp):
    date_obj = datetime.fromtimestamp(timestamp)
    date_str = date_obj.strftime('%Y-%m-%d')
    return date_str