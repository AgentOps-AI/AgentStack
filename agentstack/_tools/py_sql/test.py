from sql import Table
from __init__ import construct_sql_query

def test_query_construction():
    """Test query construction without a real database"""
    
    # Define our test table structure
    users = Table('users')
    
    print("\n=== Testing SELECT queries ===")
    # Test basic select
    query, params = construct_sql_query(
        "select",
        "users",
        columns=[users.name, users.age],
        where=users.age > 18
    )
    print("Select users over 18:")
    print(f"Query: {query}")
    print(f"Params: {params}")
    
    # Test select with multiple conditions
    query, params = construct_sql_query(
        "select",
        "users",
        columns=[users.name, users.email],
        where=(users.age > 18) & (users.active == True)
    )
    print("\nSelect active users over 18:")
    print(f"Query: {query}")
    print(f"Params: {params}")
    
    print("\n=== Testing INSERT queries ===")
    query, params = construct_sql_query(
        "insert",
        "users",
        values=[["John Doe", 25, "john@example.com", True]]
    )
    print("Insert new user:")
    print(f"Query: {query}")
    print(f"Params: {params}")
    
    print("\n=== Testing UPDATE queries ===")
    query, params = construct_sql_query(
        "update",
        "users",
        columns=[users.active],
        values=[False],
        where=users.age < 18
    )
    print("Deactivate users under 18:")
    print(f"Query: {query}")
    print(f"Params: {params}")
    
    print("\n=== Testing DELETE queries ===")
    query, params = construct_sql_query(
        "delete",
        "users",
        where=users.active == False
    )
    print("Delete inactive users:")
    print(f"Query: {query}")
    print(f"Params: {params}")

if __name__ == "__main__":
    test_query_construction()