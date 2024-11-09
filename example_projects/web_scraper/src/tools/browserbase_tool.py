# from crewai_tools import BrowserbaseLoadTool
#
# browserbase = BrowserbaseLoadTool(text_content=True)

from browserbase import Browserbase
import os
from playwright.sync_api import Playwright, sync_playwright

api_key = os.getenv('BROWSERBASE_API_KEY', None)
browserbase = Browserbase(api_key=api_key)

@tool
def download_from_url(playwright: Playwright) -> None:
    with sync_playwright() as playwright:
        # Create a session on Browserbase
        session = bb.sessions.create(project_id=BROWSERBASE_PROJECT_ID)
        assert session.id is not None
        assert session.status == "RUNNING", f"Session status is {session.status}"

        # Connect to the remote session
        connect_url = session.connect_url
        browser = playwright.chromium.connect_over_cdp(connect_url)
        context = browser.contexts[0]
        page = context.pages[0]

        # Set up CDP session for download behavior
        client = context.new_cdp_session(page)
        client.send(  # pyright: ignore
            "Browser.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": "downloads",
                "eventsEnabled": True,
            },
        )

        # Navigate to the download test page
        page.goto("https://browser-tests-alpha.vercel.app/api/download-test")

        # Start download and wait for it to complete
        with page.expect_download() as download_info:
            page.locator("#download").click()
        download = download_info.value

        # Check for download errors
        download_error = download.failure()
        if download_error:
            raise Exception(f"Download for session {session.id} failed: {download_error}")

        page.close()
        browser.close()

        # Verify the download
        zip_buffer = get_download(session.id)
        if len(zip_buffer) == 0:
            raise Exception(f"Download buffer is empty for session {session.id}")

        zip_file = zipfile.ZipFile(io.BytesIO(zip_buffer))
        zip_entries = zip_file.namelist()
        mp3_entry = next((entry for entry in zip_entries if download_re.match(entry)), None)

        if not mp3_entry:
            raise Exception(
                f"Session {session.id} is missing a file matching '{download_re.pattern}' in its zip entries: {zip_entries}"
            )

        expected_file_size = 6137541
        actual_file_size = zip_file.getinfo(mp3_entry).file_size
        assert (
            actual_file_size == expected_file_size
        ), f"Expected file size {expected_file_size}, but got {actual_file_size}"

        print("Download test passed successfully!")
