"""Migration script to add whitelist columns to existing database."""
import sqlite3
import sys
from pathlib import Path

def migrate_database():
    """Add is_whitelisted and whitelist_reason columns to users table."""
    
    # Database path
    db_path = Path(__file__).parent / "instagram_tool.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        print("No migration needed - database will be created with new schema on first run.")
        return
    
    print(f"📦 Found database at: {db_path}")
    print("🔄 Starting migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'is_whitelisted' in columns:
            print("✅ Column 'is_whitelisted' already exists - migration not needed")
        else:
            print("➕ Adding column 'is_whitelisted'...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_whitelisted BOOLEAN DEFAULT 0")
            print("✅ Added 'is_whitelisted' column")
        
        if 'whitelist_reason' in columns:
            print("✅ Column 'whitelist_reason' already exists - migration not needed")
        else:
            print("➕ Adding column 'whitelist_reason'...")
            cursor.execute("ALTER TABLE users ADD COLUMN whitelist_reason TEXT")
            print("✅ Added 'whitelist_reason' column")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        print("\nYou can now:")
        print("  - Add users to whitelist: POST /api/whitelist/add")
        print("  - Remove from whitelist: POST /api/whitelist/remove")
        print("  - View whitelist: GET /api/whitelist")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()
