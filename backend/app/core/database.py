import asyncpg
from typing import List, Dict, Any
from .config import settings


class Database:
    def __init__(self):
        self.pool = None
    
    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=2,
            max_size=10
        )
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dictionaries"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            # Convert Record objects to dictionaries
            records = await conn.fetch(query)
            return [dict(record) for record in records]
    
    async def execute_query_single(self, query: str) -> Dict[str, Any]:
        """Execute SQL query and return single result as dictionary"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(query)
            return dict(record) if record else None


# Global database instance
db = Database()
