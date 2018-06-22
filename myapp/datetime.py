import datetime


class Datetime:
    MAXYEAR = datetime.MAXYEAR
    max = datetime.datetime.max.replace(tzinfo=None)
    min = datetime.datetime.min.replace(tzinfo=None)

    @staticmethod
    def strptime(var, fmt=None):
        fmts = [fmt] if fmt else [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f"
        ]
        for fmt in fmts:
            try:
                return datetime.datetime.strptime(var, fmt).replace(tzinfo=None) if var else None
            except ValueError:
                pass
        raise ValueError("time data '{}' does not match formats {}".format(var, fmts))

    @staticmethod
    def format(var, fmt="%Y-%m-%dT%H:%M:%SZ"):
        return var.strftime(fmt) if var else None

    @staticmethod
    def utcnow():
        return datetime.datetime.utcnow().replace(tzinfo=None)

    @staticmethod
    def utcfromtimestamp(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).replace(tzinfo=None)

    @staticmethod
    def timedelta(years=0, days=0, hours=0, minutes=0, seconds=0):
        days += years * 365
        return datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def to_datetime(date):
        return datetime.datetime.combine(date, datetime.time.min).replace(tzinfo=None)
