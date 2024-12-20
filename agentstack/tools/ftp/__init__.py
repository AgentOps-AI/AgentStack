import os
from ftplib import FTP

HOST = os.getenv('FTP_HOST')
USER = os.getenv('FTP_USER')
PASSWORD = os.getenv("FTP_PASSWORD")
PATH = '/'


if not HOST:
    raise Exception(
        "Host domain has not been provided.\n Did you set the FTP_HOST in you project's .env file?"
    )

if not USER:
    raise Exception("User has not been provided.\n Did you set the FTP_USER in you project's .env file?")

if not PASSWORD:
    raise Exception(
        "Password has not been provided.\n Did you set the FTP_PASSWORD in you project's .env file?"
    )


def upload_files(file_paths: list[str]):
    """
    Upload a list of files to the FTP server.

    Args:
        file_paths: A list of file paths to upload to the FTP server.
    Returns:
        bool: True if all files were uploaded successfully, False otherwise.
    """

    assert HOST and USER and PASSWORD  # appease type checker

    result = True
    # Loop through each file path in the list
    for file_path in file_paths:
        # Establish FTP connection
        with FTP(HOST) as ftp:
            try:
                # Login to the server
                ftp.login(user=USER, passwd=PASSWORD)
                print(f"Connected to FTP server: {HOST}")

                # Change to the desired directory on the server
                ftp.cwd(PATH)

                # Open the file in binary mode for reading
                with open(file_path, 'rb') as file:
                    # Upload the file
                    ftp.storbinary(f'STOR {file_path}', file)
                    print(f"Successfully uploaded {file_path} to {PATH}")

            except Exception as e:
                print(f"An error occurred: {e}")
                result = False

    return result
