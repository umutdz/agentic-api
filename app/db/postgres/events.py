from sqlalchemy import event

from app.models.user import User


@event.listens_for(User, "after_insert")
def track_user_insert(mapper, connection, target):
    if target.email:  # Ensure email is set
        ...  # TODO: we should send email to user


@event.listens_for(User, "after_update")
def track_user_update(mapper, connection, target):
    if target.email:  # Ensure email is set
        ...  # TODO: we should send email to user
