"""
Migration script: Copy data from local SQLite to Aiven MySQL.
"""
import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, ResearchSession, ChatMessage
from dotenv import load_dotenv

load_dotenv()

# Synchronous engines for easy scripting
SQLITE_URL = "sqlite:///./zylabs.db"

# The user has mysql+aiomysql in .env, so we strip out aiomysql and use pymysql for sync migration
raw_mysql_url = os.getenv("DATABASE_URL")
if not raw_mysql_url:
    print("DATABASE_URL not found in .env")
    exit(1)

MYSQL_URL = raw_mysql_url.replace("+aiomysql", "+pymysql").split("?")[0]

print(f"Source: {SQLITE_URL}")
print(f"Target: {MYSQL_URL}")

sqlite_engine = create_engine(SQLITE_URL)
mysql_engine = create_engine(MYSQL_URL)

SqliteSessionLocal = sessionmaker(sqlite_engine)
MysqlSessionLocal = sessionmaker(mysql_engine)

def migrate():
    print("Creating tables on target database...")
    Base.metadata.create_all(mysql_engine)

    with SqliteSessionLocal() as sqlite_db, MysqlSessionLocal() as mysql_db:
        # Fetch all research sessions
        sessions = sqlite_db.query(ResearchSession).all()
        print(f"Found {len(sessions)} ResearchSessions to migrate.")
        
        for s in sessions:
            # Check if it exists
            exists = mysql_db.query(ResearchSession).filter(ResearchSession.id == s.id).first()
            if not exists:
                mysql_db.merge(s)
        
        # Fetch all chat messages
        messages = sqlite_db.query(ChatMessage).all()
        print(f"Found {len(messages)} ChatMessages to migrate.")
        
        for m in messages:
            exists = mysql_db.query(ChatMessage).filter(ChatMessage.id == m.id).first()
            if not exists:
                mysql_db.merge(m)
                
        mysql_db.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
