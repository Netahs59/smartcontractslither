from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import tempfile
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'Slither Static Analysis API',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/analyze', methods=['POST'])
def analyze_contract():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
            
        contract_code = data.get('contract', '')
        contract_name = data.get('name', 'Unknown')
        
        if not contract_code:
            return jsonify({'error': 'Contract code required'}), 400
        
        # Validate contract size
        lines = contract_code.split('\n')
        if len(lines) > 500:
            return jsonify({'error': f'Contract too large: {len(lines)} lines (max 500)'}), 400
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sol', delete=False) as f:
            f.write(contract_code)
            temp_file = f.name
        
        try:
            # Run Slither analysis
            result = subprocess.run([
                'slither', temp_file, 
                '--json', '-',
                '--disable-color',
                '--filter-paths', 'node_modules'
            ], capture_output=True, text=True, timeout=60)
            
            # Cleanup temp file
            os.unlink(temp_file)
            
            if result.stdout:
                slither_results = json.loads(result.stdout)
                detectors = slither_results.get('detectors', [])
                
                # Process and categorize findings
                findings_summary = {
                    'total_detectors': len(detectors),
                    'high_severity': len([d for d in detectors if d.get('impact') == 'High']),
                    'medium_severity': len([d for d in detectors if d.get('impact') == 'Medium']),
                    'low_severity': len([d for d in detectors if d.get('impact') == 'Low']),
                    'informational': len([d for d in detectors if d.get('impact') == 'Informational'])
                }
                
                return jsonify({
                    'success': True,
                    'contract_name': contract_name,
                    'lines_analyzed': len(lines),
                    'slither_results': slither_results,
                    'summary': findings_summary,
                    'raw_findings': detectors,
                    'timestamp': datetime.now().isoformat(),
                    'analysis_type': 'slither_static_analysis'
                })
            else:
                # Slither failed but we can still provide basic info
                return jsonify({
                    'success': True,
                    'contract_name': contract_name,
                    'lines_analyzed': len(lines),
                    'slither_results': None,
                    'summary': {'error': 'Slither analysis failed', 'stderr': result.stderr},
                    'timestamp': datetime.now().isoformat(),
                    'analysis_type': 'basic_analysis'
                })
                
        except subprocess.TimeoutExpired:
            os.unlink(temp_file)
            return jsonify({
                'success': False,
                'error': 'Analysis timeout (60 seconds)',
                'contract_name': contract_name
            }), 408
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
