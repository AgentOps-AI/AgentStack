import os
import psycopg2
from typing import Dict, Any

connection = None

def _get_connection():
    """Get PostgreSQL database connection"""

    global connection
    if connection is None:
        connection = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )

    return connection

def get_schema() -> Dict[str, Any]:
    """
    Initialize connection and get database schema.
    Returns a dictionary containing the database schema.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        # Query to get all tables in the current schema
        schema_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE';
        """
        
        cursor.execute(schema_query)
        tables = cursor.fetchall()
        
        # Create schema dictionary
        schema = {}
        for (table_name,) in tables:
            # Get column information for each table
            column_query = """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s;
            """
            cursor.execute(column_query, (table_name,))
            columns = [col[0] for col in cursor.fetchall()]
            schema[table_name] = columns
            
        cursor.close()
        # conn.close()
        return schema
        
    except Exception as e:
        print(f"Error getting database schema: {str(e)}")
        return {}

def execute_query(query: str) -> list:
    """
    Execute a SQL query on the database.
    Args:
        query: SQL query to execute
    Returns:
        List of query results
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        # conn.close()
        return results
        
    except Exception as e:
        print(f"Error executing query: {str(e)}")
        return []
