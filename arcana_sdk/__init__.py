"""
Arcana ZK Protocol SDK

Minimal SDK for interacting with the Arcana ZK Protocol API.
"""

import requests
from typing import Dict, List, Optional, Any


class ArcanaZKClient:
    """Minimal SDK client for Arcana ZK Protocol."""
    
    def __init__(self, base_url: str):
        """Initialize the Arcana ZK client."""
        if not base_url:
            raise ValueError("base_url is required")
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._make_request("GET", "/")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status."""
        return self._make_request("GET", "/status")
    
    def list_circuits(self) -> List[Dict[str, Any]]:
        """List all registered circuits."""
        response = self._make_request("GET", "/circuits")
        return response if isinstance(response, list) else []
    
    def get_circuit_info(self, circuit_id: str) -> Dict[str, Any]:
        """Get information about a specific circuit."""
        return self._make_request("GET", f"/circuits/{circuit_id}")
    
    def register_circuit(
        self,
        circuit_id: str,
        nargo_toml: str,
        main_nr: str,
        description: Optional[str] = None,
        network: str = "sapphire_testnet"
    ) -> Dict[str, Any]:
        """Register a new circuit."""
        data = {
            "circuit_id": circuit_id,
            "nargo_toml": nargo_toml,
            "main_nr": main_nr,
            "description": description,
            "network": network
        }
        return self._make_request("POST", "/register", data)
    
    def create_deployment_transaction(
        self,
        circuit_id: str,
        user_address: str,
        network: str = "sapphire_testnet"
    ) -> Dict[str, Any]:
        """Create unsigned deployment transaction."""
        data = {
            "circuit_id": circuit_id,
            "user_address": user_address,
            "network": network
        }
        return self._make_request("POST", "/deploy", data)
    
    def generate_proof(
        self,
        circuit_id: str,
        inputs: Dict[str, Any],
        public_inputs: List[int],
        verifier_address: str,
        user_address: str,
        network: str = "sapphire_testnet"
    ) -> Dict[str, Any]:
        """Generate proof and create unsigned transaction."""
        data = {
            "circuit_id": circuit_id,
            "inputs": inputs,
            "public_inputs": public_inputs,
            "verifier_address": verifier_address,
            "user_address": user_address,
            "network": network
        }
        return self._make_request("POST", "/proof", data)
    
    def broadcast_transaction(
        self,
        circuit_id: str,
        signed_transaction: str,
        network: str,
        transaction_type: str,
        verifier_address: Optional[str] = None,
        public_inputs: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Broadcast a signed transaction."""
        data = {
            "circuit_id": circuit_id,
            "signed_transaction": signed_transaction,
            "network": network,
            "transaction_type": transaction_type,
            "verifier_address": verifier_address,
            "public_inputs": public_inputs
        }
        return self._make_request("POST", "/broadcast", data)
    

def create_client(base_url: str) -> ArcanaZKClient:
    """Create an Arcana ZK client instance."""
    return ArcanaZKClient(base_url)