from datetime import datetime


def get_data_type(field):
    """
    Get the data type of the field. The data type is inferred by trying to convert the field to an int, a float, a
    datetime, and a string. If the field can be converted to an int, the data type is assumed to be int. If the
    field can be converted to a float, the data type is assumed to be float. If the field can be converted to a
    datetime, the data type is assumed to be datetime. If the field cannot be converted to any of the above, the
    data type is assumed to be string.

    :param field:
    :return:
    """
    formats = [
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S %z"
    ]
    try:
        int(field)
        return int
    except ValueError:
        pass
    try:
        float(field)
        return float
    except ValueError:
        pass
    for form in formats:
        try:
            datetime.strptime(field, form)
            return datetime
        except ValueError:
            pass
    return str