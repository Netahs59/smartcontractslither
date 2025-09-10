@app.route('/debug', methods=['POST'])
def debug():
    print("DEBUG ROUTE HIT")
    data = request.get_json()
    print(f"Received data: {data}")
    return jsonify({
        'received_data': data,
        'headers': dict(request.headers),
        'method': request.method
    })
@app.route('/analyze', methods=['POST'])
def analyze_contract():
    try:
        # Add detailed logging
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request data: {request.get_data()}")
        
        data = request.json
        print(f"Parsed JSON: {data}")
        
        if not data:
            print("No JSON data received")
            return jsonify({'error': 'No JSON data received'}), 400
            
        contract_code = data.get('contract')
        contract_name = data.get('name', 'Unknown')
        
        print(f"Contract code length: {len(contract_code) if contract_code else 0}")
        
        if not contract_code:
            print("Contract code is missing or empty")
            return jsonify({'error': 'Contract code required'}), 400
        
        # Rest of your existing code...
        
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        print(f"Exception type: {type(e).__name__}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
