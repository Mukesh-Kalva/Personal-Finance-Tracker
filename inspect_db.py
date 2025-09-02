from app import app, db, User, Transaction

with app.app_context():
    print("Users in DB:")
    for user in User.query.all():
        print(f"- {user.id} | {user.username}")

    print("\nTransactions in DB:")
    for tx in Transaction.query.all():
        print(f"- {tx.id} | {tx.category} | {tx.amount} | User {tx.user_id}")
