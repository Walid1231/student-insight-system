"""Reusable model mixins."""

from datetime import datetime
from core.extensions import db


class TimestampMixin:
    """Adds created_at / updated_at to any model."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
