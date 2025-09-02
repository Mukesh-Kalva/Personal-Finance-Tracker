from app import app, db, User

username = input("Enter username to delete: ")

with app.app_context():
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()
        print(f"✅ User '{username}' deleted.")
    else:
        print(f"❌ User '{username}' not found.")
