from app import create_app, db
from app.models import AdminInviteCode
import random
import string

app = create_app()

def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

with app.app_context():
    codes = []

    for _ in range(20):
        code = generate_code()
        new_code = AdminInviteCode(code=code)
        db.session.add(new_code)
        codes.append(code)

    db.session.commit()

    print("✅ Admin Codes:")
    for c in codes:
        print(c)