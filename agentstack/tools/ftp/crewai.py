from crewai_tools import tool
from .commonn import upload_files


upload_files = tool("Upload Files to FTP Server")(upload_files)
