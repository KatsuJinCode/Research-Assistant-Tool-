#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test incremental graph updates by uploading a document and capturing screenshots
"""
import asyncio
from playwright.async_api import async_playwright
import sys
import io
import time
import requests
from pathlib import Path

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_incremental_graph():
    # First clear any existing data
    print("Clearing existing graph data...")
    try:
        response = requests.delete('http://localhost:5000/api/clear-all', timeout=5)
        print(f"  Cleared: {response.json()}")
    except Exception as e:
        print(f"  Warning: Could not clear data: {e}")

    time.sleep(2)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Capture console logs
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        screenshot_num = 0

        try:
            # Navigate to the web interface
            print("\n1. Loading web interface...")
            await page.goto('http://localhost:5000', wait_until='load', timeout=30000)
            await page.wait_for_selector('#graph-svg', timeout=10000)
            await asyncio.sleep(2)

            # Take initial screenshot
            screenshot_num += 1
            screenshot_path = f'test_screenshot_{screenshot_num:02d}_empty.png'
            await page.screenshot(path=screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            # Find test PDF
            test_pdf = Path('web_ui/uploads/children.pdf')
            if not test_pdf.exists():
                print(f"  ERROR: Test PDF not found at {test_pdf}")
                return

            print(f"\n2. Uploading document: {test_pdf}")

            # Upload the document
            file_input = await page.query_selector('#file-input')
            await file_input.set_input_files(str(test_pdf.absolute()))

            # Click upload button
            upload_btn = await page.query_selector('#upload-btn')
            await upload_btn.click()

            print("  Upload initiated, capturing screenshots during processing...")

            # Monitor for node additions and take screenshots
            nodes_seen = set()
            last_node_count = 0

            for i in range(60):  # Monitor for up to 60 seconds
                await asyncio.sleep(1)

                # Get current node count
                node_count = await page.evaluate('''() => {
                    const svg = document.querySelector('#graph-svg');
                    const circles = svg ? svg.querySelectorAll('circle') : [];
                    return circles.length;
                }''')

                # If node count changed, take a screenshot
                if node_count != last_node_count:
                    screenshot_num += 1
                    screenshot_path = f'test_screenshot_{screenshot_num:02d}_nodes_{node_count}.png'
                    await page.screenshot(path=screenshot_path)
                    print(f"  Screenshot saved: {screenshot_path} (nodes: {node_count})")
                    last_node_count = node_count

                # Check if processing is complete
                status_text = await page.evaluate('''() => {
                    const status = document.querySelector('#status-text');
                    return status ? status.textContent : '';
                }''')

                if 'complete' in status_text.lower() or 'success' in status_text.lower():
                    print("  Processing complete!")
                    break

                # Timeout check
                if i >= 59:
                    print("  WARNING: Timeout waiting for processing")

            # Take final screenshot
            await asyncio.sleep(3)
            screenshot_num += 1
            screenshot_path = f'test_screenshot_{screenshot_num:02d}_final.png'
            await page.screenshot(path=screenshot_path)
            print(f"  Screenshot saved: {screenshot_path}")

            # Print relevant console logs
            print("\n=== Relevant Console Logs ===")
            for log in console_logs:
                if 'buildUnified' in log or 'addNodeIncremental' in log or 'link' in log.lower():
                    print(log)

            print(f"\n=== Test Complete ===")
            print(f"Total screenshots: {screenshot_num}")

            # Keep browser open for inspection
            print("\nBrowser will stay open for 10 seconds for inspection...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_incremental_graph())
