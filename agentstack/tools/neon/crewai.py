from crewai_tools import tool
from .common import create_database, execute_sql_ddl, run_sql_query

create_database = tool("Create Neon Project and Database")(create_database)
execute_sql_ddl = tool("Execute SQL DDL")(execute_sql_ddl)
run_sql_query = tool("Execute SQL DML")(run_sql_query)
