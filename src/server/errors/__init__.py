from django.db import DatabaseError


class CustomDatabaseError(DatabaseError):
    pass


__all__ = ["CustomDatabaseError"]
