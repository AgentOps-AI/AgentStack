import os
import psycopg2
from typing import Optional, Any
from agentstack import tools


connection = None

def _get_connection() -> psycopg2.extensions.connection:
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


def _get_query_action(connection: psycopg2.extensions.connection, query: str) -> Optional[tools.Action]:
    """EXPLAIN the query and classify it as READ, WRITE, DELETE, or unknown"""
    try:
        connection = _get_connection()
        with connection.cursor() as cursor:
            cursor.execute(f"EXPLAIN {query}")
            plan = cursor.fetchone()[0]
            operation = plan.split()[0].upper()
            
            if operation in ('SELECT', 'WITH'):
                return tools.Action.READ
            elif operation in ('INSERT', 'UPDATE', 'MERGE'):
                return tools.Action.WRITE
            elif operation == 'DELETE':
                return tools.Action.DELETE

        return None
    except Exception as e:
        return None


def get_schema() -> dict[str, Any]:
    """
    Initialize connection and get database schema.
    Returns a dictionary containing the database schema.
    """
    permissions = tools.get_permissions(get_schema)
    if not permissions.READ:
        return {'error': 'User has not granted read permission.'}
    
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
        return {'error': str(e)}


def execute_query(query: str) -> list:
    """
    Execute a SQL query on the database.
    Args:
        query: SQL query to execute
    Returns:
        List of query results
    """
    permissions = tools.get_permissions(execute_query)
    
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        
        # ensure the user has granted permission for this action
        action = _get_query_action(conn, query)
        if not action in permissions.actions:
            return [
                {'error': f'User has not granted {action} permission.'}
            ]
        
        # Execute the query
        cursor.execute(query)
        results = cursor.fetchall()
        
        cursor.close()
        # conn.close()
        return results
        
    except Exception as e:
        return [
            {'error': str(e)}
        ]
