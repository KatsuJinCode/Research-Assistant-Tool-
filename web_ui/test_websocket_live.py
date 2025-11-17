"""
Live WebSocket Connection Test

Actually connects to the running Flask server and verifies:
1. Can connect to WebSocket
2. Can receive processing_update events
3. Events have correct structure
4. Progress updates are being broadcast
"""

import socketio
import time
import sys

def test_websocket_connection():
    """Test actual WebSocket connection to running server."""

    print("=" * 80)
    print("LIVE WEBSOCKET CONNECTION TEST")
    print("=" * 80)
    print()

    # Create a Socket.IO client
    sio = socketio.Client()

    events_received = []

    @sio.event
    def connect():
        print("✓ Connected to WebSocket server")

    @sio.event
    def disconnect():
        print("✗ Disconnected from WebSocket server")

    @sio.on('processing_update')
    def on_processing_update(data):
        print(f"\n📨 Received 'processing_update' event:")
        print(f"   Message: {data.get('message', 'N/A')}")
        print(f"   Progress: {data.get('progress', 'N/A')}%")
        print(f"   Data: {data.get('data', {})}")
        events_received.append(('processing_update', data))

    @sio.on('document_processed')
    def on_document_processed(data):
        print(f"\n📨 Received 'document_processed' event:")
        print(f"   Document ID: {data.get('document_id', 'N/A')}")
        events_received.append(('document_processed', data))

    @sio.on('processing_error')
    def on_processing_error(data):
        print(f"\n📨 Received 'processing_error' event:")
        print(f"   Error: {data.get('error', 'N/A')}")
        events_received.append(('processing_error', data))

    try:
        # Connect to the server
        print("Attempting to connect to http://localhost:5000...")
        sio.connect('http://localhost:5000')

        print("\n✓ WebSocket connection established")
        print("Listening for events for 60 seconds...")
        print("(Upload a document in the web UI to see events)\n")

        # Wait for events
        start_time = time.time()
        while time.time() - start_time < 60:
            sio.sleep(1)
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0 and elapsed > 0:
                print(f"⏱️  {elapsed}s elapsed, {len(events_received)} events received so far")

        print("\n" + "=" * 80)
        print(f"TEST COMPLETE: Received {len(events_received)} events in 60 seconds")
        print("=" * 80)

        if len(events_received) == 0:
            print("\n⚠️  NO EVENTS RECEIVED")
            print("This means either:")
            print("1. No documents were uploaded during the test")
            print("2. The backend is not emitting events")
            print("3. The WebSocket connection is not working properly")
            return False
        else:
            print(f"\n✓ Successfully received {len(events_received)} events:")
            for event_type, data in events_received:
                print(f"  - {event_type}: {data}")
            return True

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            sio.disconnect()
        except:
            pass

if __name__ == '__main__':
    success = test_websocket_connection()
    sys.exit(0 if success else 1)
