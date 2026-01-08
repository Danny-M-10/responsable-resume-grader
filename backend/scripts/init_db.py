#!/usr/bin/env python3
"""
Standalone script to initialize database tables
Can be run as a one-off task or manually
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.init_db_async import init_db_async

async def main():
    """Initialize database tables"""
    try:
        print("Initializing database tables...")
        await init_db_async()
        print("✓ Database tables initialized successfully!")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
