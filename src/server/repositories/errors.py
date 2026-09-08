class DBError(Exception):
    pass


class DBNotFoundError(DBError):
    pass


class DBDuplicateValueError(DBError):
    pass
