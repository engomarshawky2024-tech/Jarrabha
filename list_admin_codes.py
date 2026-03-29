import os
from app import create_app, db

app = create_app()
with app.app_context():
    from app.models import AdminInviteCode
    codes = AdminInviteCode.query.all()
    for c in codes:
        print(f"ID: {c.id}, Code: {c.code}, Used: {c.is_used}")
