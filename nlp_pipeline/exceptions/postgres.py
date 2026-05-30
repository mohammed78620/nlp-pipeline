from sqlalchemy.exc import DatabaseError


class DeadlockError(DatabaseError):
    pass
