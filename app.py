"""
Arcana ZK Protocol - Noir Generator Service

Minimalist ZK proof generation service for Noir circuits.
"""

import os
import json
import logging
import subprocess
import tempfile
import base64
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# =============================================================================
# CONFIGURATION
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Service configuration."""
    CIRCUITS_DIR = "circuits"
    PROOFS_DIR = "proofs"
    NARGO_PATH = "nargo"
    BB_PATH = "bb"

# Initialize directories
for directory in [Config.CIRCUITS_DIR, Config.PROOFS_DIR]:
    os.makedirs(directory, exist_ok=True)

# =============================================================================
# MODELS
# =============================================================================

class CircuitRequest(BaseModel):
    """Circuit registration request."""
    circuit_id: str = Field(..., description="Unique circuit identifier")
    nargo_toml: str = Field(..., description="Nargo.toml content")
    main_nr: str = Field(..., description="Main.nr circuit code")
    description: Optional[str] = None
    network: str = Field(default="sapphire_testnet", description="Target network")

class ProofRequest(BaseModel):
    """Proof generation request."""
    circuit_id: str = Field(..., description="Circuit ID")
    inputs: Dict[str, Any] = Field(..., description="Private inputs")
    public_inputs: List[int] = Field(..., description="Public inputs")
    verifier_address: str = Field(..., description="Verifier contract address")
    network: str = Field(default="sapphire_testnet", description="Target network")
    user_address: str = Field(..., description="User's address")

class TransactionRequest(BaseModel):
    """Transaction broadcast request."""
    circuit_id: str = Field(..., description="Circuit ID")
    network: str = Field(..., description="Target network")
    signed_transaction: str = Field(..., description="Signed transaction hex")
    transaction_type: str = Field(..., description="'deployment' or 'verification'")
    verifier_address: Optional[str] = None
    public_inputs: Optional[List[int]] = None

class CircuitInfo(BaseModel):
    """Circuit information."""
    circuit_id: str
    description: Optional[str]
    created_at: datetime
    status: str
    verifier_address: Optional[str]
    proof_count: int
    network: str

# =============================================================================
# CORE SERVICES
# =============================================================================

class CircuitManager:
    """Manages circuit registration and compilation."""
    
    def __init__(self):
        self.circuits_dir = Path(Config.CIRCUITS_DIR)
        self.circuits_dir.mkdir(exist_ok=True)
    
    def register_circuit(self, request: CircuitRequest) -> Dict[str, Any]:
        """Register a new circuit."""
        logger.info(f"Registering circuit: {request.circuit_id}")
        
        circuit_path = self.circuits_dir / request.circuit_id
        
        try:
            # Clean existing circuit
            if circuit_path.exists():
                import shutil
                shutil.rmtree(circuit_path)
            
            # Create circuit structure
            src_path = circuit_path / "src"
            src_path.mkdir(parents=True, exist_ok=True)
            
            # Write circuit files
            (circuit_path / "Nargo.toml").write_text(request.nargo_toml)
            (src_path / "main.nr").write_text(request.main_nr)
            
            # Create default Prover.toml
            import toml
            prover_toml = {"x": 1, "y": 2}
            (circuit_path / "Prover.toml").write_text(toml.dumps(prover_toml))
            
            # Validate circuit
            self._validate_circuit(circuit_path)
            
            # Save metadata
            metadata = {
                "description": request.description,
                "created_at": datetime.now().isoformat(),
                "status": "registered",
                "verifier_address": None,
                "proof_count": 0,
                "network": request.network
            }
            
            (circuit_path / "metadata.json").write_text(json.dumps(metadata, indent=2))
            
            logger.info(f"Circuit {request.circuit_id} registered successfully")
            return {"status": "success", "circuit_id": request.circuit_id}
            
        except Exception as e:
            logger.error(f"Circuit registration failed: {str(e)}")
            if circuit_path.exists():
                import shutil
                shutil.rmtree(circuit_path)
            raise HTTPException(status_code=400, detail=str(e))
    
    def _validate_circuit(self, circuit_path: Path) -> None:
        """Validate circuit using nargo check."""
        try:
            subprocess.run(
                [Config.NARGO_PATH, "check"],
                cwd=circuit_path,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("Circuit validation successful")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Circuit validation failed: {e.stderr}")
    
    def get_circuit_info(self, circuit_id: str) -> CircuitInfo:
        """Get circuit information."""
        circuit_path = self.circuits_dir / circuit_id
        
        if not circuit_path.exists():
            raise HTTPException(status_code=404, detail=f"Circuit {circuit_id} not found")
        
        metadata_path = circuit_path / "metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
        else:
            metadata = {
                "description": None,
                "created_at": datetime.now().isoformat(),
                "status": "registered",
                "verifier_address": None,
                "proof_count": 0,
                "network": "sapphire_testnet"
            }
        
        return CircuitInfo(circuit_id=circuit_id, **metadata)
    
    def list_circuits(self) -> List[CircuitInfo]:
        """List all registered circuits."""
        circuits = []
        for circuit_dir in self.circuits_dir.iterdir():
            if circuit_dir.is_dir():
                try:
                    circuits.append(self.get_circuit_info(circuit_dir.name))
                except Exception as e:
                    logger.warning(f"Failed to get info for circuit {circuit_dir.name}: {e}")
        return circuits

class ProofGenerator:
    """Handles ZK proof generation."""
    
    def __init__(self):
        self.proofs_dir = Path(Config.PROOFS_DIR)
        self.proofs_dir.mkdir(exist_ok=True)
    
    def generate_proof(self, circuit_id: str, inputs: Dict[str, Any]) -> str:
        """Generate a ZK proof for the given circuit and inputs."""
        logger.info(f"Generating proof for circuit: {circuit_id}")
        
        circuit_path = Path(Config.CIRCUITS_DIR) / circuit_id
        if not circuit_path.exists():
            raise Exception(f"Circuit {circuit_id} not found")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Copy circuit to temp directory
                import shutil
                shutil.copytree(circuit_path, tmpdir, dirs_exist_ok=True)
                temp_circuit_path = Path(tmpdir)
                
                # Write Prover.toml from inputs
                import toml
                prover_toml_path = temp_circuit_path / "Prover.toml"
                prover_toml_path.write_text(toml.dumps(inputs))
                
                # Compile circuit
                logger.info("Compiling circuit...")
                subprocess.run(
                    [Config.NARGO_PATH, "compile"],
                    cwd=temp_circuit_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Execute circuit
                logger.info("Executing circuit...")
                subprocess.run(
                    [Config.NARGO_PATH, "execute"],
                    cwd=temp_circuit_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Check files exist
                witness_path = temp_circuit_path / "target" / "noir.gz"
                acir_path = temp_circuit_path / "target" / "noir.json"
                
                if not witness_path.exists():
                    raise Exception(f"Witness file not found at {witness_path}")
                if not acir_path.exists():
                    raise Exception(f"ACIR file not found at {acir_path}")
                
                # Generate proof
                logger.info("Generating proof...")
                proof_output_dir = temp_circuit_path / "proof_output"
                proof_output_dir.mkdir(exist_ok=True)
                
                subprocess.run(
                    [
                        Config.BB_PATH,
                        "prove",
                        "-b", str(acir_path),
                        "-w", str(witness_path),
                        "-o", str(proof_output_dir),
                    ],
                    cwd=temp_circuit_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Read proof
                proof_file = proof_output_dir / "proof"
                if not proof_file.exists():
                    # Try alternative names
                    for alt_name in ["proof.bin", "proof.hex", "proof.json"]:
                        alt_path = proof_output_dir / alt_name
                        if alt_path.exists():
                            proof_file = alt_path
                            break
                    else:
                        files = list(proof_output_dir.iterdir())
                        raise Exception(f"Proof file not found. Available: {[f.name for f in files]}")
                
                proof_bytes = proof_file.read_bytes()
                if len(proof_bytes) == 0:
                    raise Exception("Generated proof is empty")
                
                proof_b64 = base64.b64encode(proof_bytes).decode('utf-8')
                logger.info(f"Proof generated successfully, size: {len(proof_bytes)} bytes")
                
                return proof_b64
                
            except subprocess.CalledProcessError as e:
                raise Exception(f"Proof generation failed: {e.stderr}")
            except Exception as e:
                raise Exception(f"Proof generation error: {str(e)}")

class BlockchainManager:
    """Manages blockchain interactions."""
    
    def __init__(self):
        self.rpc_urls = {
            "sapphire_mainnet": "https://sapphire.oasis.io",
            "sapphire_testnet": "https://testnet.sapphire.oasis.dev",
            "ethereum_mainnet": "https://mainnet.infura.io/v3/YOUR_PROJECT_ID",
            "ethereum_sepolia": "https://sepolia.etherscan.io"
        }
    
    def create_unsigned_transaction(self, to_address: str, data: bytes, user_address: str, network: str) -> Dict[str, Any]:
        """Create unsigned transaction for offline signing."""
        try:
            from web3 import Web3
            
            rpc_url = self.rpc_urls.get(network)
            if not rpc_url:
                raise Exception(f"Unsupported network: {network}")
            
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                raise Exception(f"Failed to connect to {network}")
            
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(user_address))
            gas_price = w3.eth.gas_price
            
            transaction = {
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': gas_price,
                'to': Web3.to_checksum_address(to_address),
                'data': data.hex(),
                'from': Web3.to_checksum_address(user_address),
                'value': 0
            }
            
            # Estimate gas
            from typing import cast
            from web3.types import TxParams
            estimated_gas = w3.eth.estimate_gas(cast(TxParams, transaction))
            transaction['gas'] = estimated_gas
            
            return {
                "status": "success",
                "unsigned_transaction": transaction,
                "network": network,
                "user_address": user_address,
                "to_address": to_address
            }
            
        except Exception as e:
            logger.error(f"Failed to create transaction: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def broadcast_signed_transaction(self, signed_transaction_hex: str, network: str) -> Dict[str, Any]:
        """Broadcast a signed transaction."""
        try:
            from web3 import Web3
            
            rpc_url = self.rpc_urls.get(network)
            if not rpc_url:
                raise Exception(f"Unsupported network: {network}")
            
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                raise Exception(f"Failed to connect to network")
            
            # Decode signed transaction
            if signed_transaction_hex.startswith('0x'):
                signed_transaction_hex = signed_transaction_hex[2:]
            
            # Send raw transaction
            tx_hash = w3.eth.send_raw_transaction(bytes.fromhex(signed_transaction_hex))
            
            # Wait for receipt
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            verified = tx_receipt.get('status') == 1
            
            # Extract contract address for deployment
            contract_address = None
            if tx_receipt.get('to') is None:
                contract_address = tx_receipt.get('contractAddress')
                if contract_address:
                    contract_address = Web3.to_checksum_address(contract_address)
            
            return {
                "status": "success",
                "verified": verified,
                "transaction_hash": tx_hash.hex(),
                "gas_used": tx_receipt.get('gasUsed', 0),
                "block_number": tx_receipt.get('blockNumber', 0),
                "contract_address": contract_address
            }
            
        except Exception as e:
            logger.error(f"Failed to broadcast transaction: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def create_unsigned_deployment_transaction(self, bytecode: str, network: str, user_address: str) -> Dict[str, Any]:
        """Create unsigned deployment transaction."""
        try:
            from web3 import Web3
            
            rpc_url = self.rpc_urls.get(network)
            if not rpc_url:
                raise Exception(f"Unsupported network: {network}")
            
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                raise Exception(f"Failed to connect to {network}")
            
            nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(user_address))
            gas_price = w3.eth.gas_price
            
            transaction = {
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': gas_price,
                'data': bytes.fromhex(bytecode),
                'from': Web3.to_checksum_address(user_address),
                'value': 0
            }
            
            # Estimate gas
            from typing import cast
            from web3.types import TxParams
            estimated_gas = w3.eth.estimate_gas(cast(TxParams, transaction))
            transaction['gas'] = estimated_gas
            
            return {
                "status": "success",
                "unsigned_transaction": transaction,
                "network": network,
                "user_address": user_address
            }
            
        except Exception as e:
            logger.error(f"Failed to create deployment transaction: {str(e)}")
            return {"status": "error", "error": str(e)}

class ContractManager:
    """Manages contract compilation."""
    
    def __init__(self):
        self.blockchain_manager = BlockchainManager()

    def compile_circuit(self, circuit_id: str) -> dict:
        """Compile circuit and generate verifier."""
        circuit_path = Path(Config.CIRCUITS_DIR) / circuit_id
        target_dir = circuit_path / "target"
        vk_dir = target_dir / "vk"
        verifier_path = target_dir / "verifier.sol"
        
        logger.info(f"Compiling circuit: {circuit_id}")
        
        try:
            # Compile circuit
            subprocess.run(
                [Config.NARGO_PATH, "compile"],
                cwd=str(circuit_path.absolute()),
                check=True,
                capture_output=True,
                text=True
            )
            
            # Generate verification key
            vk_dir.mkdir(exist_ok=True)
            noir_json_path = target_dir / "noir.json"
            subprocess.run([
                Config.BB_PATH, "write_vk",
                "-b", str(noir_json_path.absolute()),
                "-o", str(vk_dir.absolute())
            ], check=True, capture_output=False, text=True)
            
            # Generate Solidity verifier
            vk_file_path = vk_dir / "vk"
            subprocess.run([
                Config.BB_PATH, "write_solidity_verifier",
                "-k", str(vk_file_path.absolute()),
                "-o", str(verifier_path.absolute())
            ], check=True, capture_output=False, text=True)
            
            # Compile Solidity contract
            verifier_source = verifier_path.read_text()
            
            with tempfile.TemporaryDirectory() as compile_dir:
                temp_verifier_path = Path(compile_dir) / "Verifier.sol"
                temp_verifier_path.write_text(verifier_source)
                
                subprocess.run([
                    "solc",
                    "--bin",
                    "--optimize",
                    "--optimize-runs", "200",
                    str(temp_verifier_path),
                    "-o", compile_dir
                ], cwd=compile_dir, capture_output=True, text=True, check=True)
                
                bin_files = list(Path(compile_dir).glob("*.bin"))
                if not bin_files:
                    raise Exception("No compiled bytecode found")
                
                bytecode = bin_files[0].read_text().strip()
                if bytecode.startswith('0x'):
                    bytecode = bytecode[2:]
                
                return {
                    "status": "success", 
                    "verifier_path": str(verifier_path), 
                    "bytecode": bytecode,
                    "circuit_id": circuit_id
                }
                
        except subprocess.CalledProcessError as e:
            raise Exception(f"Compilation failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"Contract compilation failed: {str(e)}")

# =============================================================================
# SERVICE INSTANCES
# =============================================================================

circuit_manager = CircuitManager()
proof_generator = ProofGenerator()
contract_manager = ContractManager()
blockchain_manager = BlockchainManager()

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Arcana ZK Protocol",
    description="Minimalist ZK proof generation service",
    version="0.1.0"
)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "arcana-zk",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/circuits", response_model=List[CircuitInfo])
async def list_circuits():
    """List all registered circuits."""
    return circuit_manager.list_circuits()

@app.get("/circuits/{circuit_id}", response_model=CircuitInfo)
async def get_circuit_info(circuit_id: str):
    """Get circuit information."""
    return circuit_manager.get_circuit_info(circuit_id)

@app.post("/register")
async def register_circuit(request: CircuitRequest):
    """Register and compile a circuit."""
    try:
        # Register circuit
        circuit_manager.register_circuit(request)
        
        # Compile circuit
        result = contract_manager.compile_circuit(request.circuit_id)
        
        return {
            "status": "success",
            "circuit_id": request.circuit_id,
            "message": "Circuit registered and compiled successfully",
            "verifier_path": result["verifier_path"],
            "bytecode": result["bytecode"],
            "network": request.network
        }
        
    except Exception as e:
        logger.error(f"Circuit registration failed: {str(e)}")
        return {"status": "error", "detail": str(e)}

@app.post("/deploy")
async def create_deployment_transaction(request: Dict[str, str]):
    """Create unsigned deployment transaction."""
    try:
        circuit_id = request["circuit_id"]
        user_address = request["user_address"]
        network = request.get("network", "sapphire_mainnet")
        
        # Get bytecode from existing compilation
        circuit_path = Path(Config.CIRCUITS_DIR) / circuit_id
        target_dir = circuit_path / "target"
        verifier_path = target_dir / "verifier.sol"
        
        if not verifier_path.exists():
            raise Exception(f"Circuit {circuit_id} not compiled. Register it first.")
        
        # Read bytecode
        with tempfile.TemporaryDirectory() as compile_dir:
            temp_verifier_path = Path(compile_dir) / "Verifier.sol"
            temp_verifier_path.write_text(verifier_path.read_text())
            
            subprocess.run([
                "solc",
                "--bin",
                "--optimize",
                "--optimize-runs", "200",
                str(temp_verifier_path),
                "-o", compile_dir
            ], cwd=compile_dir, capture_output=True, text=True, check=True)
            
            bin_files = list(Path(compile_dir).glob("*.bin"))
            if not bin_files:
                raise Exception("No compiled bytecode found")
            
            bytecode = bin_files[0].read_text().strip()
            if bytecode.startswith('0x'):
                bytecode = bytecode[2:]
        
        # Create unsigned deployment transaction
        tx_result = blockchain_manager.create_unsigned_deployment_transaction(
            bytecode, network, user_address
        )
        
        if tx_result["status"] != "success":
            raise Exception(f"Failed to create deployment transaction: {tx_result.get('error')}")
        
        return {
            "status": "success",
            "circuit_id": circuit_id,
            "unsigned_transaction": tx_result["unsigned_transaction"],
            "network": network,
            "message": "Deployment transaction created for offline signing"
        }
        
    except Exception as e:
        logger.error(f"Failed to create deployment transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/proof")
async def generate_proof_and_transaction(request: ProofRequest):
    """Generate proof and create unsigned transaction."""
    try:
        # Generate proof
        proof_b64 = proof_generator.generate_proof(request.circuit_id, request.inputs)
        
        # Prepare call data
        proof_bytes = base64.b64decode(proof_b64)
        public_inputs_bytes = b''.join(input_val.to_bytes(32, 'big') for input_val in request.public_inputs)
        call_data = proof_bytes + public_inputs_bytes
        
        # Create unsigned transaction
        tx_result = blockchain_manager.create_unsigned_transaction(
            request.verifier_address,
            call_data,
            request.user_address,
            request.network
        )
        
        if tx_result["status"] != "success":
            raise Exception(f"Failed to create transaction: {tx_result.get('error')}")
        
        # Update metadata
        circuit_path = Path(Config.CIRCUITS_DIR) / request.circuit_id
        metadata_path = circuit_path / "metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
            metadata["proof_count"] += 1
            metadata["last_modified"] = datetime.now().isoformat()
            metadata_path.write_text(json.dumps(metadata, indent=2))
        
        return {
            "status": "success",
            "circuit_id": request.circuit_id,
            "proof_hash": hashlib.sha256(proof_b64.encode()).hexdigest(),
            "proof_size": len(proof_b64),
            "unsigned_transaction": tx_result["unsigned_transaction"],
            "network": request.network,
            "verifier_address": request.verifier_address,
            "public_inputs": request.public_inputs,
            "message": "Proof generated and transaction created for offline signing"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate proof: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/broadcast")
async def broadcast_transaction(request: TransactionRequest):
    """Broadcast a signed transaction."""
    try:
        # Broadcast signed transaction
        result = blockchain_manager.broadcast_signed_transaction(
            request.signed_transaction,
            request.network
        )
        
        if result["status"] != "success":
            raise Exception(f"Failed to broadcast transaction: {result.get('error')}")
        
        # Handle deployment vs verification
        if request.transaction_type == "deployment":
            # Update circuit metadata
            circuit_path = Path(Config.CIRCUITS_DIR) / request.circuit_id
            metadata_path = circuit_path / "metadata.json"
            if metadata_path.exists():
                metadata = json.loads(metadata_path.read_text())
                metadata["status"] = "deployed"
                metadata["verifier_address"] = result.get("contract_address")
                metadata["last_modified"] = datetime.now().isoformat()
                metadata_path.write_text(json.dumps(metadata, indent=2))
            
            return {
                "status": "success",
                "circuit_id": request.circuit_id,
                "verifier_address": result.get("contract_address"),
                "network": request.network,
                "transaction_hash": result.get("transaction_hash"),
                "gas_used": result.get("gas_used", 0),
                "message": "Contract deployed successfully"
            }
        
        else:  # verification
            return {
                "status": "success",
                "verified": result.get("verified", False),
                "circuit_id": request.circuit_id,
                "verifier_address": request.verifier_address,
                "network": request.network,
                "transaction_hash": result.get("transaction_hash"),
                "gas_used": result.get("gas_used", 0),
                "message": "Transaction broadcast successfully" if result.get("verified") else "Transaction failed"
            }
        
    except Exception as e:
        logger.error(f"Failed to broadcast transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_service_status():
    """Get service status."""
    circuits = circuit_manager.list_circuits()
    
    return {
        "status": "operational",
        "statistics": {
            "total_circuits": len(circuits),
            "total_proofs": sum(c.proof_count for c in circuits),
            "deployed_circuits": len([c for c in circuits if c.verifier_address])
        },
        "supported_networks": list(blockchain_manager.rpc_urls.keys()),
        "timestamp": datetime.now().isoformat()
    } 