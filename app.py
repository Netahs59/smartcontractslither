from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Slither API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_contract():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data'}), 400
            
        contract_code = data.get('contract', '')
        if not contract_code:
            return jsonify({'error': 'Missing contract field'}), 400
            
        # For now, return success without Slither
        return jsonify({
            'success': True,
            'message': 'Contract received successfully',
            'contract_length': len(contract_code),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Let Railway handle the port
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
