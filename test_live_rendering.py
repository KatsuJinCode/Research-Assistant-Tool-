#!/usr/bin/env python3
"""
Test incremental graph rendering by monitoring the live page during document processing
"""
import asyncio
from playwright.async_api import async_playwright
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

async def main():
    print("Connecting to existing server at http://localhost:5000...")

    async with async_playwright() as p:
        # Launch headless browser so it doesn't interfere with user's work
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})

        # Enable console logging
        async def on_console(msg):
            # Only show logs related to graph rendering
            text = msg.text
            if any(keyword in text for keyword in ['addNodeIncremental', 'renderGraph', 'Initialized position', 'Preserving']):
                print(f"  [BROWSER] {text}")

        page = await context.new_page()
        page.on('console', on_console)

        try:
            # Load the page
            print("\n1. Loading page...")
            await page.goto('http://localhost:5000', wait_until='networkidle', timeout=10000)
            await page.wait_for_selector('#graph-svg', timeout=5000)
            await asyncio.sleep(1)

            # Take initial screenshot
            print("\n2. Taking initial screenshot (empty graph)...")
            await page.screenshot(path='test_01_initial.png', full_page=False)
            print("  Saved: test_01_initial.png")

            # Clear database
            print("\n3. Clearing database...")
            await page.evaluate('''() => {
                return fetch('/api/clear-all', {method: 'DELETE'})
                    .then(r => r.json());
            }''')
            await asyncio.sleep(1)

            # Take screenshot of empty graph
            print("\n4. Taking screenshot of cleared graph...")
            await page.screenshot(path='test_02_cleared.png', full_page=False)
            print("  Saved: test_02_cleared.png")

            # Upload a document
            print("\n5. Uploading document (children.pdf)...")
            file_input = await page.query_selector('#file-input')
            await file_input.set_input_files('C:\\Users\\jpswi\\Research-Assistant-Tool-\\web_ui\\uploads\\children.pdf')

            upload_btn = await page.query_selector('#upload-btn')
            await upload_btn.click()

            print("\n6. Monitoring graph updates...")
            print("   Watching for nodes to appear...\n")

            screenshot_count = 2
            last_node_count = 0

            # Monitor for 120 seconds or until complete (long enough to see behavior)
            for i in range(120):
                await asyncio.sleep(1)

                # Get current node count and positions
                node_info = await page.evaluate('''() => {
                    const circles = document.querySelectorAll('#graph-svg circle');
                    const nodes = Array.from(circles).map((c, i) => {
                        const transform = c.parentElement.getAttribute('transform');
                        const match = transform ? transform.match(/translate\\(([^,]+),([^)]+)\\)/) : null;
                        return {
                            index: i,
                            x: match ? parseFloat(match[1]) : null,
                            y: match ? parseFloat(match[2]) : null
                        };
                    });
                    return {
                        count: nodes.length,
                        nodes: nodes
                    };
                }''')

                node_count = node_info['count']

                # If node count changed, take screenshot and show positions
                if node_count != last_node_count:
                    screenshot_count += 1
                    filename = f'test_{screenshot_count:02d}_nodes_{node_count}.png'
                    await page.screenshot(path=filename, full_page=False)

                    print(f"\n  TIME: {i}s | NODES: {node_count} | Screenshot: {filename}")

                    # Show first 3 node positions (handle None values)
                    for node in node_info['nodes'][:3]:
                        x = node['x'] if node['x'] is not None else 0
                        y = node['y'] if node['y'] is not None else 0
                        print(f"    Node {node['index']}: ({x:.1f}, {y:.1f})")

                    last_node_count = node_count

                # Check if processing is complete
                status = await page.evaluate('''() => {
                    return document.querySelector('#status-text')?.textContent || '';
                }''')

                if 'complete' in status.lower():
                    print("\n  ✓ Processing complete!")
                    break

            # Final screenshot
            await asyncio.sleep(2)
            screenshot_count += 1
            final_file = f'test_{screenshot_count:02d}_final.png'
            await page.screenshot(path=final_file, full_page=False)
            print(f"\n7. Final screenshot: {final_file}")

            # Get final node positions
            final_positions = await page.evaluate('''() => {
                const circles = document.querySelectorAll('#graph-svg circle');
                return Array.from(circles).map((c, i) => {
                    const transform = c.parentElement.getAttribute('transform');
                    const match = transform ? transform.match(/translate\\(([^,]+),([^)]+)\\)/) : null;
                    return {
                        index: i,
                        x: match ? parseFloat(match[1]) : null,
                        y: match ? parseFloat(match[2]) : null
                    };
                });
            }''')

            print("\n" + "="*60)
            print("TEST COMPLETE")
            print("="*60)
            print(f"Final node count: {len(final_positions)}")
            print("\nFinal positions:")
            for node in final_positions:
                x = node['x'] if node['x'] is not None else 0
                y = node['y'] if node['y'] is not None else 0
                print(f"  Node {node['index']}: ({x:.1f}, {y:.1f})")

            # Check if nodes are all at (0,0) or None
            at_origin = sum(1 for n in final_positions if (n['x'] is None or n['x'] == 0) and (n['y'] is None or n['y'] == 0))
            if at_origin > 0:
                print(f"\n⚠️  WARNING: {at_origin} nodes are at origin (0,0)")
            else:
                print("\n✓ All nodes have non-zero positions")

            # Headless mode - no need to keep browser open
            print("\nTest complete - closing browser...")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
