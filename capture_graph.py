#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Capture screenshot of the graph visualization for testing
"""
import asyncio
from playwright.async_api import async_playwright
import sys
import io

# Fix Windows console encoding issues
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def capture_graph():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})

        # Capture console logs
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            # Navigate to the web interface
            print("Loading web interface...")
            await page.goto('http://localhost:5000', wait_until='load', timeout=30000)

            # Wait for D3.js to finish rendering
            print("Waiting for graph to render...")
            await page.wait_for_selector('#graph-svg', timeout=10000)
            await asyncio.sleep(5)  # Give D3 animation time to complete

            # Take screenshot
            screenshot_path = 'graph_screenshot.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot saved to {screenshot_path}")

            # Get some stats from the page
            stats = await page.evaluate('''() => {
                return {
                    nodes: document.querySelector('#stat-nodes')?.textContent || '-',
                    claims: document.querySelector('#stat-claims')?.textContent || '-',
                    version: document.querySelector('#version-build')?.textContent || '-'
                }
            }''')
            print(f"Stats: {stats}")

            # Print console logs
            print("\n=== Browser Console Logs ===")
            for log in console_logs:
                print(log)

        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(capture_graph())
