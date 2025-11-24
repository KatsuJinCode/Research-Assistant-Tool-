"""
Test script to inspect AI panel placement using Playwright
"""
from playwright.sync_api import sync_playwright
import time
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_ai_panel():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to app
        print("[*] Navigating to http://localhost:5000...")
        page.goto("http://localhost:5000")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Take screenshot
        print("[*] Taking screenshot...")
        page.screenshot(path="ai_panel_test.png", full_page=True)

        # Find all elements with "AI Research Assistant" text
        print("\n[SEARCH] Looking for 'AI Research Assistant' elements...")
        elements = page.locator("text=AI Research Assistant").all()
        print(f"Found {len(elements)} elements with 'AI Research Assistant' text")

        for i, elem in enumerate(elements):
            print(f"\n--- Element {i+1} ---")

            # Get bounding box
            box = elem.bounding_box()
            if box:
                print(f"Position: x={box['x']}, y={box['y']}, width={box['width']}, height={box['height']}")

            # Get parent info
            parent = elem.locator("xpath=..")
            parent_id = parent.get_attribute("id")
            parent_class = parent.get_attribute("class")
            print(f"Parent ID: {parent_id}")
            print(f"Parent class: {parent_class}")

            # Check if visible
            visible = elem.is_visible()
            print(f"Visible: {visible}")

            # Get computed style for positioning
            if parent_id:
                style_info = page.evaluate(f'''() => {{
                    const elem = document.getElementById('{parent_id}');
                    if (!elem) return null;
                    const style = window.getComputedStyle(elem);
                    return {{
                        position: style.position,
                        display: style.display,
                        left: style.left,
                        right: style.right,
                        top: style.top,
                        bottom: style.bottom,
                        zIndex: style.zIndex
                    }};
                }}''')
                print(f"Computed style: {style_info}")

        # Check sidebar structure
        print("\n[SIDEBAR] Checking sidebar structure...")
        sidebar = page.locator("#sidebar")
        if sidebar.count() > 0:
            children = sidebar.locator("> *").all()
            print(f"Sidebar has {len(children)} direct children:")
            for i, child in enumerate(children):
                child_id = child.get_attribute("id")
                child_class = child.get_attribute("class")
                print(f"  {i+1}. ID: {child_id}, Class: {child_class}")

        # Check for old chat panel
        print("\n[OLD PANEL] Checking for #chat-panel...")
        old_panel = page.locator("#chat-panel")
        if old_panel.count() > 0:
            print("[ERROR] OLD PANEL STILL EXISTS!")
            visible = old_panel.is_visible()
            print(f"   Visible: {visible}")
            style = page.evaluate('''() => {
                const elem = document.getElementById('chat-panel');
                if (!elem) return null;
                const style = window.getComputedStyle(elem);
                return {
                    display: style.display,
                    visibility: style.visibility,
                    opacity: style.opacity
                };
            }''')
            print(f"   Computed style: {style}")
        else:
            print("[OK] Old panel not found")

        # Check for new panel
        print("\n[NEW PANEL] Checking for #ai-assistant-bottom...")
        new_panel = page.locator("#ai-assistant-bottom")
        if new_panel.count() > 0:
            print("[OK] NEW PANEL EXISTS!")
            visible = new_panel.is_visible()
            print(f"   Visible: {visible}")
            box = new_panel.bounding_box()
            if box:
                print(f"   Position: x={box['x']}, y={box['y']}")
        else:
            print("[ERROR] New panel not found")

        print("\n[DONE] Screenshot saved to ai_panel_test.png")
        print("Keeping browser open for 10 seconds for manual inspection...")
        time.sleep(10)

        browser.close()

if __name__ == "__main__":
    test_ai_panel()
