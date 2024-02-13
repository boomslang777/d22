from datetime import datetime, timedelta

def get_exp(contract_name):

    if contract_name != "BANKNIFTY":
        return None  # Only handle BANKNIFTY contracts


    current_date = datetime.now()  # Use current date if not provided

    day_of_week = current_date.weekday()

    # If today is Tuesday or Wednesday, adjust date to point to next Wednesday
    if day_of_week in [1, 2]:
        nearest_wednesday_date = current_date + timedelta(days=7)
    else:
        # Calculate days until next Wednesday
        days_until_nearest_wednesday = (2 - day_of_week + 7) % 7
        nearest_wednesday_date = current_date + timedelta(days=days_until_nearest_wednesday)
    week_number = (nearest_wednesday_date.day - 1) // 7 + 1
    print(week_number)
    if week_number == 4:
        # Format as YYMON (e.g., 24FEB)
        return nearest_wednesday_date.strftime("%y%b").upper()
    else:
        # Format as YYDDMM (e.g., 240207)
        month = nearest_wednesday_date.strftime("%m").lstrip("0")
        return nearest_wednesday_date.strftime("%y{0}%d").format(month) + nearest_wednesday_date.strftime("%y%m%d")[6:]

# Example usage:
print(get_exp("BANKNIFTY"))  # Output: 240207 (today is Wednesday, 2024-02-07)

# # Simulate different dates (optional):
# desired_date = datetime(2024, 2, 22)  # Friday
# print(get_exp("BANKNIFTY", current_date=desired_date))  # Output: 240214 (next Wednesday is 2024-02-14)
# # desired_date = datetime(2024, 2, 19)  # Tuesday
# print(get_exp("BANKNIFTY", current_date=desired_date))  # Output: 24222 (next Wednesday is 2024-03-20)
