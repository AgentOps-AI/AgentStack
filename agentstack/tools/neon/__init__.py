import os
from neon_api import NeonAPI
import psycopg2
from psycopg2.extras import RealDictCursor


NEON_API_KEY = os.getenv("NEON_API_KEY")
neon_client = NeonAPI(api_key=NEON_API_KEY)


def create_database(project_name: str) -> str:
    """
    Creates a new Neon project. (this takes less than 500ms)
    Args:
        project_name: Name of the project to create
    Returns:
        the connection URI for the new project
    """
    try:
        project = neon_client.project_create(project={"name": project_name}).project
        connection_uri = neon_client.connection_uri(
            project_id=project.id, database_name="neondb", role_name="neondb_owner"
        ).uri
        return f"Project/database created, connection URI: {connection_uri}"
    except Exception as e:
        return f"Failed to create project: {str(e)}"


def execute_sql_ddl(connection_uri: str, command: str) -> str:
    """
    Inserts data into a specified Neon database.
    Args:
        connection_uri: The connection URI for the Neon database
        command: The DDL SQL command to execute
    Returns:
        the result of the DDL command
    """
    conn = psycopg2.connect(connection_uri)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(command)
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Failed to execute DDL command: {str(e)}"
    cur.close()
    conn.close()
    return f"Command succeeded"


def run_sql_query(connection_uri: str, query: str) -> str:
    """
    Inserts data into a specified Neon database.
    Args:
        connection_uri: The connection URI for the Neon database
        query: The SQL query to execute
    Returns:
        the result of the SQL query
    """
    conn = psycopg2.connect(connection_uri)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(query)
        conn.commit()

        # Try to fetch results (for SELECT queries)
        try:
            records = cur.fetchall()
            return f"Query result: {records}"
        except psycopg2.ProgrammingError:
            # For INSERT/UPDATE/DELETE operations
            return f"Query executed successfully"
    except Exception as e:
        conn.rollback()
        return f"Failed to execute SQL query: {str(e)}"
    finally:
        cur.close()
        conn.close()
