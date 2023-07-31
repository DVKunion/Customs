import time
from datetime import datetime, timedelta

def calculate_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {execution_time:.6f} seconds.")
        return result

    return wrapper


def get_previous_day():
    current_datetime = datetime.now()
    # 提取日期部分
    current_date = current_datetime.date()
    # 使用timedelta减去一天
    previous_day = current_date - timedelta(days=1)
    return previous_day
