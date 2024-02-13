import datetime

def get_current_year_month():
    now = datetime.datetime.now()

    # Check if it's the last week of the month
    last_week = (now + datetime.timedelta(days=7)).month != now.month

    if last_week:
        # If it's the last week, return the next month
        next_month = now.replace(month=(now.month % 12) + 1, day=1)
        return next_month.strftime("%y%b").upper() + 'FUT'
    else:
        # If it's not the last week, return the current month
        return now.strftime("%y%b").upper() + 'FUT'

# Example usage
result = get_current_year_month()
print(result)
