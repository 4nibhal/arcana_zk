# Arcana ZK Protocol SDK

A minimal Python SDK for interacting with the Arcana ZK Protocol API, enabling zero-knowledge proof generation and verification on Oasis Sapphire networks.

## Overview

The Arcana ZK SDK provides a streamlined interface for building privacy-preserving applications with zero-knowledge proofs on Oasis Sapphire networks.

### Key Features

- **ZK Proof Generation** - Real Noir/Barretenberg integration
- **Offline Signing** - Private keys never leave your device
- **Multi-Network Support** - Sapphire Testnet/Mainnet/Localnet
- **Circuit Management** - Register, compile, deploy circuits
- **Universal ABI** - Compatible verifier contracts across networks
- **Minimal Dependencies** - Only essential packages required

## Installation

This SDK is part of the Arcana ZK Protocol project and uses `uv` for dependency management.

### Prerequisites

- **Python 3.9+**
- **uv** (Python package manager)
- **Git** (for cloning the repository)

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd arcana_zk

# Install dependencies using uv
uv sync

# Activate virtual environment
source .venv/bin/activate
```

The SDK will be available as an internal package within the project.

## Quick Start

### Initialize Client

```python
import os
from arcana_sdk import create_client

# Create client with explicit API endpoint
API_URL = os.getenv("API_URL", "http://localhost:8000")
client = create_client(API_URL)
```

### Health Check

```python
# Verify API connectivity
health = client.health_check()
print(f"API Status: {health['status']}")
```

### Circuit Registration

```python
import time
from pathlib import Path

# Load real circuit files from your project
circuit_path = Path("circuits/noir")
nargo_toml_path = circuit_path / "Nargo.toml"
main_nr_path = circuit_path / "src" / "main.nr"

# Read circuit files
with open(nargo_toml_path, 'r') as f:
    nargo_toml = f.read()

with open(main_nr_path, 'r') as f:
    main_nr = f.read()

# Register circuit with unique ID
circuit_id = f"circuit_demo_{int(time.time())}"

result = client.register_circuit(
    circuit_id=circuit_id,
    nargo_toml=nargo_toml,
    main_nr=main_nr,
    description="Demo circuit - x != y",
    network="sapphire_testnet"
)
print(f"Circuit registered: {result['circuit_id']}")
```

### Deployment Transaction

```python
import os
from eth_account import Account

# Get private key from environment
SAPPHIRE_KEY = os.getenv("SAPPHIRE_KEY")
if not SAPPHIRE_KEY:
    raise ValueError("SAPPHIRE_KEY environment variable required")

account = Account.from_key(SAPPHIRE_KEY)
user_address = account.address

print(f"Using address: {user_address}")

# Create unsigned deployment transaction
deployment_tx = client.create_deployment_transaction(
    circuit_id=circuit_id,
    user_address=user_address,
    network="sapphire_testnet"
)

# Sign and broadcast
signed_tx = account.sign_transaction(deployment_tx["unsigned_transaction"])

broadcast_result = client.broadcast_transaction(
    circuit_id=circuit_id,
    signed_transaction=signed_tx.raw_transaction.hex(),
    network="sapphire_testnet",
    transaction_type="deployment"
)

print(f"Deployment broadcasted: {broadcast_result['transaction_hash']}")
verifier_address = broadcast_result.get("verifier_address")
print(f"Contract deployed at: {verifier_address}")
```

### Proof Generation

```python
# Circuit expects: fn main(x: Field, y: pub Field) { assert(x != y); }
inputs = {"x": 5, "y": 10}  # Private inputs
public_inputs = [10]  # Public input for verification

print(f"Generating proof with inputs: {inputs}")
print(f"Public inputs: {public_inputs}")
print(f"Verifier address: {verifier_address}")
print(f"User address: {user_address}")

# Generate ZK proof
proof_result = client.generate_proof(
    circuit_id=circuit_id,
    inputs=inputs,
    public_inputs=public_inputs,
    verifier_address=verifier_address,
    user_address=user_address,
    network="sapphire_testnet"
)

# Sign and broadcast verification transaction
signed_verification = account.sign_transaction(proof_result["unsigned_transaction"])

verification_result = client.broadcast_transaction(
    circuit_id=circuit_id,
    signed_transaction=signed_verification.raw_transaction.hex(),
    network="sapphire_testnet",
    transaction_type="verification",
    verifier_address=proof_result.get("verifier_address"),
    public_inputs=proof_result.get("public_inputs")
)

print(f"Proof verified: {verification_result['transaction_hash']}")
```

## Complete Workflow Example

```python
#!/usr/bin/env python3
"""
Complete Arcana ZK SDK workflow demonstration
"""

import json
import time
import os
from pathlib import Path
from arcana_sdk import create_client

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
SAPPHIRE_KEY = os.getenv("SAPPHIRE_KEY")

def run_complete_workflow():
    """Run complete SDK workflow demonstration."""
    print("Arcana ZK SDK - Complete Workflow Demo")
    print(f"Target URL: {API_URL}")
    print(f"SAPPHIRE_KEY present: {bool(SAPPHIRE_KEY)}")
    
    # Create client
    client = create_client(API_URL)
    
    # Step 1: Health check
    print("\nStep 1: Service Connectivity")
    health = client.health_check()
    print(f"API Status: {health['status']}")
    
    # Step 2: Register circuit
    print("\nStep 2: Circuit Registration")
    circuit_path = Path("circuits/noir")
    nargo_toml_path = circuit_path / "Nargo.toml"
    main_nr_path = circuit_path / "src" / "main.nr"
    
    with open(nargo_toml_path, 'r') as f:
        nargo_toml = f.read()
    
    with open(main_nr_path, 'r') as f:
        main_nr = f.read()
    
    circuit_id = f"circuit_demo_{int(time.time())}"
    
    result = client.register_circuit(
        circuit_id=circuit_id,
        nargo_toml=nargo_toml,
        main_nr=main_nr,
        description="Demo circuit - x != y",
        network="sapphire_testnet"
    )
    print(f"Circuit registered: {result['circuit_id']}")
    
    # Step 3: Deploy contract (if SAPPHIRE_KEY is set)
    if SAPPHIRE_KEY:
        print("\nStep 3: Contract Deployment")
        from eth_account import Account
        account = Account.from_key(SAPPHIRE_KEY)
        
        deployment_tx = client.create_deployment_transaction(
            circuit_id=circuit_id,
            user_address=account.address,
            network="sapphire_testnet"
        )
        
        signed_tx = account.sign_transaction(deployment_tx["unsigned_transaction"])
        
        broadcast_result = client.broadcast_transaction(
            circuit_id=circuit_id,
            signed_transaction=signed_tx.raw_transaction.hex(),
            network="sapphire_testnet",
            transaction_type="deployment"
        )
        
        verifier_address = broadcast_result.get("verifier_address")
        print(f"Contract deployed at: {verifier_address}")
        
        # Step 4: Generate and verify proof
        print("\nStep 4: Proof Generation & Verification")
        inputs = {"x": 5, "y": 10}
        public_inputs = [10]
        
        proof_result = client.generate_proof(
            circuit_id=circuit_id,
            inputs=inputs,
            public_inputs=public_inputs,
            verifier_address=verifier_address,
            user_address=account.address,
            network="sapphire_testnet"
        )
        
        signed_verification = account.sign_transaction(proof_result["unsigned_transaction"])
        
        verification_result = client.broadcast_transaction(
            circuit_id=circuit_id,
            signed_transaction=signed_verification.raw_transaction.hex(),
            network="sapphire_testnet",
            transaction_type="verification",
            verifier_address=proof_result.get("verifier_address"),
            public_inputs=proof_result.get("public_inputs")
        )
        
        print(f"Proof verified: {verification_result['transaction_hash']}")
        print("Complete workflow successful!")
    else:
        print("SAPPHIRE_KEY not set, skipping blockchain operations")

if __name__ == "__main__":
    run_complete_workflow()
```

## API Reference

### Client Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `health_check()` | Check API connectivity | `Dict[str, Any]` |
| `get_service_status()` | Get service statistics | `Dict[str, Any]` |
| `list_circuits()` | List all circuits | `List[Dict[str, Any]]` |
| `get_circuit_info(circuit_id)` | Get circuit details | `Dict[str, Any]` |

### Core Operations

#### `register_circuit(circuit_id, nargo_toml, main_nr, description=None, network="sapphire_testnet")`

Register a new Noir circuit for ZK proof generation.

**Parameters:**
- `circuit_id` (str): Unique identifier for the circuit
- `nargo_toml` (str): Nargo.toml configuration file content
- `main_nr` (str): Main.nr circuit implementation
- `description` (str, optional): Circuit description
- `network` (str): Target network

**Example:**
```python
# Load circuit files from your project
circuit_path = Path("circuits/noir")
with open(circuit_path / "Nargo.toml", 'r') as f:
    nargo_toml = f.read()
with open(circuit_path / "src" / "main.nr", 'r') as f:
    main_nr = f.read()

result = client.register_circuit(
    circuit_id="my_circuit",
    nargo_toml=nargo_toml,
    main_nr=main_nr,
    description="My ZK circuit",
    network="sapphire_testnet"
)
```

#### `create_deployment_transaction(circuit_id, user_address, network="sapphire_testnet")`

Create unsigned deployment transaction for verifier contract.

**Parameters:**
- `circuit_id` (str): Circuit identifier
- `user_address` (str): Ethereum address for transaction signing
- `network` (str): Target network

**Example:**
```python
from eth_account import Account
account = Account.from_key(os.getenv("SAPPHIRE_KEY"))

deployment_tx = client.create_deployment_transaction(
    circuit_id="my_circuit",
    user_address=account.address,
    network="sapphire_testnet"
)
```

#### `generate_proof(circuit_id, inputs, public_inputs, verifier_address, user_address, network="sapphire_testnet")`

Generate ZK proof and create unsigned verification transaction.

**Parameters:**
- `circuit_id` (str): Circuit identifier
- `inputs` (Dict[str, Any]): Private input values for proof generation
- `public_inputs` (List[int]): Public input values for verification
- `verifier_address` (str): Deployed verifier contract address
- `user_address` (str): Ethereum address for transaction signing
- `network` (str): Target network

**Example:**
```python
# For circuit: fn main(x: Field, y: pub Field) { assert(x != y); }
proof_result = client.generate_proof(
    circuit_id="my_circuit",
    inputs={"x": 5, "y": 10},  # Private inputs
    public_inputs=[10],         # Public value for verification
    verifier_address="0x1234...",  # Deployed contract address
    user_address="0xabcd...",      # Your wallet address
    network="sapphire_testnet"
)
```

#### `broadcast_transaction(circuit_id, signed_transaction, network, transaction_type, verifier_address=None, public_inputs=None)`

Broadcast signed transaction to the network.

**Parameters:**
- `circuit_id` (str): Circuit identifier
- `signed_transaction` (str): Hex-encoded signed transaction
- `network` (str): Target network
- `transaction_type` (str): "deployment" or "verification"
- `verifier_address` (str, optional): Required for verification transactions
- `public_inputs` (List[int], optional): Required for verification transactions

**Example:**
```python
# Sign and broadcast deployment
signed_tx = account.sign_transaction(deployment_tx["unsigned_transaction"])
result = client.broadcast_transaction(
    circuit_id="my_circuit",
    signed_transaction=signed_tx.raw_transaction.hex(),
    network="sapphire_testnet",
    transaction_type="deployment"
)
```

## Network Support

| Network | Chain ID | RPC URL | Use Case |
|---------|----------|---------|----------|
| **sapphire_testnet** | `23295` | `https://testnet.sapphire.oasis.io` | Development & Testing |
| **sapphire_mainnet** | `23294` | `https://sapphire.oasis.io` | Production |
| **sapphire_localnet** | `23293` | `http://localhost:8545` | Local Development |

## Error Handling

The SDK provides clear error messages for common issues:

```python
try:
    result = client.register_circuit(...)
except Exception as e:
    print(f"Error: {str(e)}")
```

**Common Error Types:**
- **Network connectivity issues** - Check your internet connection and API URL
- **Invalid API responses** - Verify the backend service is running correctly
- **Missing required parameters** - Ensure all required fields are provided
- **Transaction failures** - Check gas fees, network status, and transaction parameters

## Security Considerations

| Security Aspect | Best Practice |
|----------------|---------------|
| **Private Key Management** | Never hardcode private keys in production code |
| **Network Selection** | Verify network parameters before broadcasting |
| **Input Validation** | Validate all inputs before proof generation |
| **Transaction Signing** | Use secure signing methods (hardware wallets recommended) |

## Dependencies

Managed by `uv` in the project's `pyproject.toml`:

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | `>=2.32.4` | HTTP client for API communication |
| `eth-account` | `>=0.13.7` | Ethereum account management |

## Development

The SDK is designed with minimal dependencies and explicit parameter requirements. All network operations require explicit URL specification to prevent hardcoded defaults.

### Design Principles

- **Security First**: Offline signing for maximum security
- **Minimal Dependencies**: Only essential packages
- **Explicit Configuration**: No hidden defaults
- **Error Handling**: Clear and actionable error messages

## License

**MIT License** - see [LICENSE](../LICENSE) file for details. 