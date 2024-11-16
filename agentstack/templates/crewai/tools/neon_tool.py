import os
from crewai_tools import tool
from dotenv import load_dotenv
from neon import Neon

load_dotenv()

NEON_API_KEY = os.getenv('NEON_API_KEY')
neon_client = Neon(api_key=NEON_API_KEY)

@tool("Create Project")
def create_project(project_name: str) -> str:
    """
    Creates a new Neon project.
    Args:
        project_name: Name of the project to create
    Returns:
        Project ID and status message
    """
    try:
        project = neon_client.projects.create(name=project_name)
        return f"Project created successfully. Project ID: {project.id}"
    except Exception as e:
        return f"Failed to create project: {str(e)}"

@tool("Create Database")
def create_database(project_id: str, database_name: str) -> str:
    """
    Creates a new database in specified Neon project.
    Args:
        project_id: ID of the project
        database_name: Name of the database to create
    Returns:
        Status message about database creation
    """
    try:
        result = neon_client.databases.create(
            project_id=project_id,
            name=database_name
        )
        return f"Database {database_name} created successfully"
    except Exception as e:
        return f"Failed to create database: {str(e)}"

@tool("List Databases")
def list_databases(project_id: str) -> str:
    """
    Lists all databases in specified Neon project.
    Args:
        project_id: ID of the project
    Returns:
        List of database names
    """
    try:
        databases = neon_client.databases.list(project_id=project_id)
        return "\n".join([db.name for db in databases])
    except Exception as e:
        return f"Failed to list databases: {str(e)}"

@tool("Delete Database")
def delete_database(project_id: str, database_name: str) -> str:
    """
    Deletes a database from specified Neon project.
    Args:
        project_id: ID of the project
        database_name: Name of the database to delete
    Returns:
        Status message about database deletion
    """
    try:
        neon_client.databases.delete(
            project_id=project_id,
            name=database_name
        )
        return f"Database {database_name} deleted successfully"
    except Exception as e:
        return f"Failed to delete database: {str(e)}"
