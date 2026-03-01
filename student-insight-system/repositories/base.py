"""
Generic CRUD repository.

Subclass and set ``model`` to get free get/create/update/delete:

    class StudentRepo(BaseRepository):
        model = StudentProfile
"""

from core.extensions import db


class BaseRepository:
    """Generic repository providing common CRUD operations."""

    model = None  # Set in subclass

    @classmethod
    def get_by_id(cls, id_):
        """Return one instance or None."""
        return cls.model.query.get(id_)

    @classmethod
    def get_all(cls, limit=100, offset=0):
        """Return paginated list."""
        return cls.model.query.offset(offset).limit(limit).all()

    @classmethod
    def create(cls, **kwargs):
        """Insert and flush (so we get the id) but leave commit to caller."""
        instance = cls.model(**kwargs)
        db.session.add(instance)
        db.session.flush()
        return instance

    @classmethod
    def update(cls, instance, **kwargs):
        """Update attributes on an existing instance."""
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        db.session.flush()
        return instance

    @classmethod
    def delete(cls, instance):
        """Mark for deletion (commit left to caller)."""
        db.session.delete(instance)

    @classmethod
    def commit(cls):
        """Commit the current transaction."""
        db.session.commit()

    @classmethod
    def rollback(cls):
        """Roll back the current transaction."""
        db.session.rollback()
