"""
Complete Chain Test - Test every link from backend to frontend

Tests:
1. Backend can emit events
2. SocketIO server receives and queues events
3. WebSocket clients can connect
4. WebSocket clients receive events
5. Event data structure is correct
"""

import sys
import time
import threading
sys.path.insert(0, 'C:\\Users\\jpswi\\Research-Assistant-Tool-')

def test_backend_emit():
    """Test 1: Backend can emit without errors."""
    print("\n" + "="*80)
    print("TEST 1: Backend Emit")
    print("="*80)

    from web_ui.app import app, socketio

    try:
        with app.app_context():
            socketio.emit('processing_update', {
                'message': 'Test',
                'progress': 50,
                'data': {'event': 'test'}
            })
            print("[PASS] Backend emit completed without error")
            return True
    except Exception as e:
        print(f"[FAIL] Backend emit failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_client_connection():
    """Test 2: Client can connect to WebSocket."""
    print("\n" + "="*80)
    print("TEST 2: Client Connection")
    print("="*80)

    import socketio as sio_client

    client = sio_client.Client()
    connected = False

    @client.event
    def connect():
        nonlocal connected
        connected = True
        print("[PASS] Client connected to WebSocket")

    try:
        client.connect('http://localhost:5000')
        time.sleep(1)

        if connected:
            client.disconnect()
            return True
        else:
            print("[FAIL] Client did not connect")
            return False

    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        return False


def test_event_reception():
    """Test 3: Client receives events from server."""
    print("\n" + "="*80)
    print("TEST 3: Event Reception (Backend -> Frontend)")
    print("="*80)

    import socketio as sio_client
    from web_ui.app import app, socketio as server_socketio

    client = sio_client.Client()
    events_received = []

    @client.event
    def connect():
        print("[INFO] Client connected, waiting for events...")

    @client.on('processing_update')
    def on_update(data):
        print(f"[RECEIVED] processing_update: {data}")
        events_received.append(('processing_update', data))

    @client.on('document_processed')
    def on_complete(data):
        print(f"[RECEIVED] document_processed: {data}")
        events_received.append(('document_processed', data))

    try:
        # Connect client
        client.connect('http://localhost:5000')
        time.sleep(1)

        # Emit test event from server
        def emit_test():
            time.sleep(0.5)
            with app.app_context():
                print("[EMIT] Server emitting test event...")
                server_socketio.emit('processing_update', {
                    'message': 'Test message',
                    'progress': 75,
                    'data': {'event': 'test'}
                })
                time.sleep(0.5)
                server_socketio.emit('document_processed', {
                    'document_id': 'test-123'
                })

        # Emit in background thread
        emit_thread = threading.Thread(target=emit_test)
        emit_thread.start()

        # Wait for events
        time.sleep(2)
        emit_thread.join()

        # Check results
        client.disconnect()

        if len(events_received) >= 2:
            print(f"[PASS] Received {len(events_received)} events")
            return True
        else:
            print(f"[FAIL] Only received {len(events_received)} events (expected 2)")
            return False

    except Exception as e:
        print(f"[FAIL] Event reception test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_event_structure():
    """Test 4: Events have correct data structure."""
    print("\n" + "="*80)
    print("TEST 4: Event Data Structure")
    print("="*80)

    import socketio as sio_client
    from web_ui.app import app, socketio as server_socketio

    client = sio_client.Client()
    received_data = []

    @client.on('processing_update')
    def on_update(data):
        received_data.append(data)

    try:
        client.connect('http://localhost:5000')
        time.sleep(0.5)

        # Emit structured event
        with app.app_context():
            server_socketio.emit('processing_update', {
                'message': 'Processing step',
                'progress': 60,
                'data': {
                    'event': 'claim_added',
                    'claim_id': 'test-claim'
                }
            })

        time.sleep(1)
        client.disconnect()

        if len(received_data) > 0:
            data = received_data[0]

            # Verify structure
            checks = [
                ('message' in data, "Has 'message' field"),
                ('progress' in data, "Has 'progress' field"),
                ('data' in data, "Has 'data' field"),
                (isinstance(data.get('data'), dict), "'data' is dict"),
                ('event' in data.get('data', {}), "data.event exists")
            ]

            all_pass = True
            for check, desc in checks:
                if check:
                    print(f"[PASS] {desc}")
                else:
                    print(f"[FAIL] {desc}")
                    all_pass = False

            return all_pass
        else:
            print("[FAIL] No events received")
            return False

    except Exception as e:
        print(f"[FAIL] Structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*80)
    print("COMPLETE WEBSOCKET CHAIN TEST")
    print("="*80)
    print("\nTesting every link from backend emit to frontend receive...")

    results = []

    # Test 1: Backend emit
    results.append(("Backend Emit", test_backend_emit()))

    # Test 2: Client connection
    results.append(("Client Connection", test_client_connection()))

    # Test 3: Event reception
    results.append(("Event Reception", test_event_reception()))

    # Test 4: Event structure
    results.append(("Event Structure", test_event_structure()))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:.<40} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed - WebSocket chain is working!")
        return 0
    else:
        print("\n[FAILURE] Some tests failed - WebSocket chain is broken")
        return 1


if __name__ == '__main__':
    sys.exit(main())
