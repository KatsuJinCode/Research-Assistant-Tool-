#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test incremental graph rendering by monitoring WebSocket events and taking screenshots
"""
import asyncio
from playwright.async_api import async_playwright
import sys
import io
import requests
from pathlib import Path
import time

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def test_visual_incremental():
    # Clear existing data
    print("Clearing database...")
    try:
        requests.delete('http://localhost:5000/api/clear-all', timeout=5)
    except:
        pass

    await asyncio.sleep(2)

    async with async_playwright() as p:
        # Launch visible browser
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        screenshots = []
        screenshot_num = 0

        # Capture console logs
        console_logs = []
        def log_handler(msg):
            text = msg.text
            console_logs.append(f"[{msg.type}] {text}")
            if 'renderGraph' in text or 'addNodeIncremental' in text:
                print(f"  {text}")

        page.on('console', log_handler)

        try:
            print("\n1. Loading page...")
            await page.goto('http://localhost:5000', wait_until='networkidle', timeout=30000)
            await page.wait_for_selector('#graph-svg', timeout=10000)
            await asyncio.sleep(2)

            # Initial screenshot
            screenshot_num += 1
            path = f'visual_test_{screenshot_num:02d}_empty.png'
            await page.screenshot(path=path, full_page=False)
            screenshots.append(path)
            print(f"  Screenshot: {path}")

            # Upload document
            print("\n2. Uploading document...")
            test_pdf = Path('web_ui/uploads/children.pdf')
            if not test_pdf.exists():
                print(f"ERROR: {test_pdf} not found")
                return

            file_input = await page.query_selector('#file-input')
            await file_input.set_input_files(str(test_pdf.absolute()))

            upload_btn = await page.query_selector('#upload-btn')
            await upload_btn.click()

            print("\n3. Monitoring node additions...")

            last_node_count = 0
            for i in range(90):  # 90 seconds max
                await asyncio.sleep(1)

                # Check node count
                node_count = await page.evaluate('''() => {
                    const circles = document.querySelectorAll('#graph-svg circle');
                    return circles.length;
                }''')

                # Get node positions for debugging
                if node_count > 0 and node_count != last_node_count:
                    positions = await page.evaluate('''() => {
                        const circles = document.querySelectorAll('#graph-svg circle');
                        return Array.from(circles).map((c, i) => {
                            const transform = c.parentElement.getAttribute('transform');
                            return {index: i, transform};
                        });
                    }''')

                    screenshot_num += 1
                    path = f'visual_test_{screenshot_num:02d}_nodes_{node_count}.png'
                    await page.screenshot(path=path, full_page=False)
                    screenshots.append(path)

                    print(f"\n  Nodes: {node_count}")
                    print(f"  Screenshot: {path}")
                    print(f"  Positions: {positions[:3]}")  # Show first 3

                    last_node_count = node_count

                # Check if complete
                status = await page.evaluate('''() => {
                    return document.querySelector('#status-text')?.textContent || '';
                }''')

                if 'complete' in status.lower():
                    print("\n  Processing complete!")
                    break

            # Final screenshot
            await asyncio.sleep(3)
            screenshot_num += 1
            path = f'visual_test_{screenshot_num:02d}_final.png'
            await page.screenshot(path=path, full_page=False)
            screenshots.append(path)
            print(f"\n  Final screenshot: {path}")

            # Print summary
            print(f"\n{'='*60}")
            print(f"TEST COMPLETE")
            print(f"{'='*60}")
            print(f"Screenshots captured: {len(screenshots)}")
            for s in screenshots:
                print(f"  - {s}")

            print("\nRelevant console logs:")
            for log in console_logs:
                if 'renderGraph' in log or 'addNode' in log or 'Creating' in log:
                    print(f"  {log}")

            # Keep browser open for inspection
            print("\n\nBrowser staying open for 15 seconds for inspection...")
            await asyncio.sleep(15)

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_visual_incremental())
