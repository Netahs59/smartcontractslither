import os
import git
import requests
import tempfile
import shutil
import subprocess
import json
from pathlib import Path

class GitHubRepoHandler:
    def __init__(self):
        self.temp_dir = None
        
    def clone_repo(self, repo_url, access_token=None, branch='main'):
        """Clone GitHub repository to temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        
        try:
            # Handle private repos with access token
            if access_token and access_token.strip():
                # Extract repo parts from URL
                if repo_url.startswith('https://github.com/'):
                    repo_path = repo_url.replace('https://github.com/', '')
                    auth_url = f"https://{access_token}@github.com/{repo_path}"
                else:
                    auth_url = repo_url  # Assume it's already formatted
            else:
                auth_url = repo_url
                
            print(f"Cloning repository from: {repo_url}")
            print(f"Branch: {branch}")
            
            # Clone repository
            repo = git.Repo.clone_from(auth_url, self.temp_dir, branch=branch)
            print(f"Successfully cloned to: {self.temp_dir}")
            return self.temp_dir
            
        except Exception as e:
            self.cleanup()
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    def get_contract_files(self, contracts_path='contracts/'):
        """Extract Solidity files from cloned repository"""
        if not self.temp_dir:
            raise Exception("No repository cloned")
            
        # Try the specified path first
        contracts_dir = Path(self.temp_dir) / contracts_path.strip('/')
        
        # If specified path doesn't exist, try common locations
        if not contracts_dir.exists():
            common_paths = ['contracts/', 'src/', 'solidity/', './']
            for common_path in common_paths:
                test_path = Path(self.temp_dir) / common_path
                if test_path.exists() and any(test_path.rglob("*.sol")):
                    contracts_dir = test_path
                    print(f"Found contracts in: {common_path}")
                    break
            else:
                raise Exception(f"No Solidity files found in {contracts_path} or common directories")
        
        # Find all .sol files
        sol_files = list(contracts_dir.rglob("*.sol"))
        
        if not sol_files:
            raise Exception(f"No .sol files found in {contracts_dir}")
            
        print(f"Found {len(sol_files)} Solidity files")
        
        contract_data = []
        for sol_file in sol_files:
            try:
                with open(sol_file, 'r', encoding='utf-8') as f:
                    contract_data.append({
                        'name': sol_file.name,
                        'path': str(sol_file.relative_to(Path(self.temp_dir))),
                        'content': f.read()
                    })
            except Exception as e:
                print(f"Warning: Could not read {sol_file}: {e}")
        
        return contract_data
    
    def run_slither_analysis(self, contracts_path='contracts/'):
        """Run Slither analysis on cloned repository"""
        if not self.temp_dir:
            raise Exception("No repository cloned")
            
        contracts_dir = os.path.join(self.temp_dir, contracts_path.strip('/'))
        
        # If contracts directory doesn't exist, try to find it
        if not os.path.exists(contracts_dir):
            for common_path in ['contracts', 'src', 'solidity', '.']:
                test_path = os.path.join(self.temp_dir, common_path)
                if os.path.exists(test_path):
                    contracts_dir = test_path
                    break
        
        try:
            print(f"Running Slither on: {contracts_dir}")
            
            # Run slither with JSON output
            result = subprocess.run([
                'slither', 
                contracts_dir,
                '--json', '-'
            ], capture_output=True, text=True, timeout=300, cwd=self.temp_dir)
            
            if result.returncode == 0 or result.stdout:
                # Slither often returns non-zero even on success
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return structured error
                    return {
                        'error': 'Slither analysis completed but output was not valid JSON',
                        'raw_output': result.stdout,
                        'stderr': result.stderr
                    }
            else:
                return {
                    'error': 'Slither analysis failed',
                    'stderr': result.stderr,
                    'stdout': result.stdout,
                    'returncode': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {'error': 'Slither analysis timed out after 5 minutes'}
        except FileNotFoundError:
            return {'error': 'Slither not installed or not found in PATH'}
        except Exception as e:
            return {'error': f'Unexpected error running Slither: {str(e)}'}
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up: {self.temp_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up {self.temp_dir}: {e}")
            self.temp_dir = None
