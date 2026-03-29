from app import create_app
from app.models import AdminInviteCode

app = create_app()

with app.app_context():
    codes = AdminInviteCode.query.all()

    print("📌 All Admin Codes:")
    for c in codes:
        print(c.code, "| Used:", c.is_used)