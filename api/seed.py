from api.models.database import SessionLocal, User
from api.routes.auth import get_password_hash

def seed_admin_user():
    db = SessionLocal()
    admin_exists = db.query(User).filter(User.username == "admin").first()
    
    if not admin_exists:
        print("🌱 Seeding default admin user...")
        hashed_password = get_password_hash("admin")
        admin_user = User(username="admin", password_hash=hashed_password)
        db.add(admin_user)
        db.commit()
        print("✅ Admin user seeded successfully.")
    else:
        print("⚡ Admin user already exists. Skipping seeding.")
    
    db.close()

if __name__ == "__main__":
    seed_admin_user()
