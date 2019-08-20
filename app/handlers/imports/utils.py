from datetime import datetime


def check_valid_date(value, date_format):
    try:
        datetime.strptime(value, date_format)
        return True
    except ValueError:
        return False


def check_relatives(relatives: dict):
    for citizen in relatives:
        relatives_list = relatives[citizen]
        for item in relatives_list:
            if item not in relatives or citizen not in relatives[item]:
                return False
    return True
