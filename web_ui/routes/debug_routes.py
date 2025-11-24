"""
Debug Routes Blueprint

Handles debugging agent status and controls.
Routes: /api/debug/*
"""

from flask import Blueprint, jsonify
import logging

from web_ui.shared import get_debug_agent

logger = logging.getLogger(__name__)

debug_bp = Blueprint('debug', __name__, url_prefix='/api/debug')


@debug_bp.route('/status', methods=['GET'])
def debug_status():
    """Get debugging agent status"""
    try:
        debug_agent = get_debug_agent()
        if debug_agent is None:
            return jsonify({'error': 'Debug agent not initialized'}), 500
        status = debug_agent.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting debug status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/toggle', methods=['POST'])
def debug_toggle():
    """Toggle debugging agent on/off"""
    try:
        debug_agent = get_debug_agent()
        if debug_agent is None:
            return jsonify({'error': 'Debug agent not initialized'}), 500
        enabled = debug_agent.toggle()
        return jsonify({
            'enabled': enabled,
            'message': f"Debugging agent {'enabled' if enabled else 'disabled'}"
        })
    except Exception as e:
        logger.error(f"Error toggling debug agent: {str(e)}")
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/enable', methods=['POST'])
def debug_enable():
    """Enable debugging agent"""
    try:
        debug_agent = get_debug_agent()
        if debug_agent is None:
            return jsonify({'error': 'Debug agent not initialized'}), 500
        debug_agent.enable()
        return jsonify({
            'enabled': True,
            'message': 'Debugging agent enabled'
        })
    except Exception as e:
        logger.error(f"Error enabling debug agent: {str(e)}")
        return jsonify({'error': str(e)}), 500


@debug_bp.route('/disable', methods=['POST'])
def debug_disable():
    """Disable debugging agent"""
    try:
        debug_agent = get_debug_agent()
        if debug_agent is None:
            return jsonify({'error': 'Debug agent not initialized'}), 500
        debug_agent.disable()
        return jsonify({
            'enabled': False,
            'message': 'Debugging agent disabled'
        })
    except Exception as e:
        logger.error(f"Error disabling debug agent: {str(e)}")
        return jsonify({'error': str(e)}), 500
