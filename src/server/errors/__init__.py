"""Define custom exceptions for database operations."""


class CustomDatabaseError(Exception):
    """Represent an error raised during a database operation."""


__all__ = ["CustomDatabaseError"]
