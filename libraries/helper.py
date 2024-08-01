from datetime import datetime
from dateutil.relativedelta import relativedelta


def get_date_range(term):
    today = datetime.today()
    start_date = today.replace(day=1)
    end_date = (start_date - relativedelta(months=term - 1)).replace(day=1) if term > 1 else start_date
    end_date = end_date + relativedelta(months=1) - relativedelta(days=1)

    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

