"""
Test script to trigger the AI assistant error using Playwright
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_ai_chat():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to app
        print("[*] Navigating to http://localhost:5000...")
        page.goto("http://localhost:5000")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Close tutorial if it appears
        try:
            # Try clicking the X button
            close_button = page.locator("#tutorial-overlay button:has-text('✕')")
            if close_button.is_visible(timeout=2000):
                close_button.click()
                time.sleep(0.5)
        except:
            try:
                # Try Skip button
                skip_button = page.locator("text=Skip")
                if skip_button.is_visible(timeout=2000):
                    skip_button.click()
                    time.sleep(0.5)
            except:
                # Press Escape key
                page.keyboard.press("Escape")
                time.sleep(0.5)

        # Click on AI assistant to expand it
        print("[*] Expanding AI assistant...")
        ai_header = page.locator("#ai-assistant-bottom .ai-assistant-header")
        if ai_header.is_visible():
            ai_header.click()
            time.sleep(1)

        # Type a message
        print("[*] Typing test message...")
        ai_input = page.locator("#ai-input-bottom")
        ai_input.fill("Hello, can you help me?")
        time.sleep(0.5)

        # Set up request/response monitoring
        print("[*] Sending message and monitoring response...")

        def handle_response(response):
            if '/chat' in response.url:
                print(f"\n[RESPONSE] Status: {response.status}")
                print(f"[RESPONSE] URL: {response.url}")
                try:
                    json_data = response.json()
                    print(f"[RESPONSE] JSON: {json_data}")
                except:
                    print(f"[RESPONSE] Text: {response.text()}")

        page.on("response", handle_response)

        # Click send button
        send_button = page.locator("button:has-text('Send')")
        send_button.click()

        # Wait for response
        time.sleep(3)

        # Check for error dialogs
        error_dialog = page.locator("text=AI AGENT FAILURE")
        if error_dialog.is_visible():
            print("\n[ERROR] ❌ AI AGENT FAILURE dialog appeared!")
            error_text = page.locator("body").inner_text()
            print(f"[ERROR] Full error: {error_text}")

        # Take screenshot
        print("\n[*] Taking screenshot...")
        page.screenshot(path="ai_chat_test.png", full_page=True)

        print("\n[DONE] Keeping browser open for 10 seconds...")
        time.sleep(10)

        browser.close()

if __name__ == "__main__":
    test_ai_chat()
