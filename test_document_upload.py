"""
Test document upload to trigger and capture the NoneType error
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_document_upload():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to app
        print("[*] Navigating to http://localhost:5000...")
        page.goto("http://localhost:5000")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Close tutorial
        try:
            page.keyboard.press("Escape")
            time.sleep(0.5)
        except:
            pass

        # Create a small test document
        test_file = Path("test_doc.txt")
        test_file.write_text("""
This is a test document for debugging.

The main claim is that AI systems can process documents.
Another claim is that testing helps find bugs.
A third claim is that error messages should be informative.
""")

        print(f"[*] Created test file: {test_file.absolute()}")

        # Monitor for error dialogs
        error_found = False
        error_message = None

        def handle_dialog(dialog):
            nonlocal error_found, error_message
            if "AI AGENT FAILURE" in dialog.message:
                error_found = True
                error_message = dialog.message
                print(f"\n[ERROR CAPTURED] {dialog.message}")
            dialog.accept()

        page.on("dialog", handle_dialog)

        # Upload the file
        print("[*] Uploading test document...")
        file_input = page.locator("#file-input")
        file_input.set_input_files(str(test_file.absolute()))

        # Wait for processing
        print("[*] Waiting for processing...")
        time.sleep(10)

        # Take screenshot
        page.screenshot(path="upload_error_test.png", full_page=True)

        if error_found:
            print(f"\n[ERROR] Captured error dialog:")
            print(error_message)
            print("\n[*] Check Flask server logs for full traceback")
        else:
            print("[*] No error dialog appeared - upload may have succeeded")

        print("\n[*] Keeping browser open for 5 seconds...")
        time.sleep(5)

        browser.close()

        # Clean up test file
        test_file.unlink()

if __name__ == "__main__":
    test_document_upload()
