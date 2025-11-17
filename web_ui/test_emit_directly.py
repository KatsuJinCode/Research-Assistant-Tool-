"""
Direct Emit Test - Bypass frontend, test backend emission directly
"""

import sys
sys.path.insert(0, 'C:\\Users\\jpswi\\Research-Assistant-Tool-')

from web_ui.app import app, socketio
import time

def test_direct_emit():
    """Test emitting directly from Flask app context."""
    print("="*80)
    print("DIRECT WEBSOCKET EMIT TEST")
    print("="*80)

    with app.app_context():
        print("\n[TEST 1] Emitting processing_update with app context...")
        socketio.emit('processing_update', {
            'message': 'Test message',
            'progress': 50,
            'data': {'event': 'test'}
        })
        print("[OK] Emit completed without error")

        time.sleep(1)

        print("\n[TEST 2] Emitting document_processed with app context...")
        socketio.emit('document_processed', {
            'document_id': 'test-doc-123'
        })
        print("[OK] Emit completed without error")

    print("\n" + "="*80)
    print("EMIT TEST COMPLETE")
    print("="*80)
    print("\nIf you have a browser open to http://localhost:5000,")
    print("check the console - you should see these test events")

if __name__ == '__main__':
    test_direct_emit()
