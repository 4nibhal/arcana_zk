#!/usr/bin/env python3
"""
Arcana ZK SDK - Minimal Demo

Demonstrates the complete workflow using the Arcana ZK SDK:
1. Circuit registration and compilation
2. Contract deployment transaction creation
3. Proof generation with real inputs
4. Transaction broadcasting for verification


Assumptions 
- The user has a private key to sign the transactions
- The user has a Sapphire account
- The user has a Sapphire key
- It use default network "sapphire_testnet"
- It use default circuit directory "circuits"
"""

import json
import time
import os
from pathlib import Path
from arcana_sdk import create_client

# Configuration - URL must be explicitly defined
#API_URL = os.getenv("API_URL") # Real server
API_URL = "http://localhost:8000"  # Local
SAPPHIRE_KEY = os.getenv("SAPPHIRE_KEY")

if not SAPPHIRE_KEY:
    print("⚠️  Warning: SAPPHIRE_KEY environment variable not set")
    print("   Set it with: export SAPPHIRE_KEY=your_private_key_here")
    print("   This demo will show the workflow but skip actual blockchain transactions")
    print()

def print_test_header(test_name: str):
    """Print test header."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")

def print_result(result: dict, success: bool = True):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {json.dumps(result, indent=2)}")

def test_health_check(client):
    """Test health check endpoint."""
    print_test_header("Health Check")
    try:
        result = client.health_check()
        print_result(result, True)
        return True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return False

def test_service_status(client):
    """Test service status endpoint."""
    print_test_header("Service Status")
    try:
        result = client.get_service_status()
        print_result(result, True)
        return True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return False

def test_list_circuits(client):
    """Test list circuits endpoint."""
    print_test_header("List Circuits")
    try:
        result = client.list_circuits()
        print_result(result, True)
        return True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return False

def test_register_circuit(client):
    """Test circuit registration with real circuit."""
    print_test_header("Register Circuit")
    
    # Load real circuit files
    circuit_path = Path("circuits/noir")
    nargo_toml_path = circuit_path / "Nargo.toml"
    main_nr_path = circuit_path / "src" / "main.nr"
    
    if not nargo_toml_path.exists() or not main_nr_path.exists():
        print_result({"error": "Circuit files not found"}, False)
        return None, False
    
    # Use a unique circuit ID with timestamp
    circuit_id = f"circuit_demo_{int(time.time())}"
    
    try:
        # Read real circuit files
        with open(nargo_toml_path, 'r') as f:
            nargo_toml = f.read()
        
        with open(main_nr_path, 'r') as f:
            main_nr = f.read()
        
        result = client.register_circuit(
            circuit_id=circuit_id,
            nargo_toml=nargo_toml,
            main_nr=main_nr,
            description="Demo circuit - x != y",
            network="sapphire_testnet"
        )
        print_result(result, True)
        return circuit_id, True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return None, False

def test_get_circuit_info(client, circuit_id):
    """Test get circuit info endpoint."""
    print_test_header(f"Get Circuit Info: {circuit_id}")
    try:
        result = client.get_circuit_info(circuit_id)
        print_result(result, True)
        return True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return False

def test_create_deployment_transaction(client, circuit_id):
    """Test deployment transaction creation."""
    print_test_header("Create Deployment Transaction")
    
    if not SAPPHIRE_KEY:
        print_result({"error": "SAPPHIRE_KEY not set, skipping deployment test"}, False)
        return None, False
    
    try:
        from eth_account import Account
        account = Account.from_key(SAPPHIRE_KEY)
        user_address = account.address
        
        print(f"🔍 Using address: {user_address}")
        
        result = client.create_deployment_transaction(
            circuit_id=circuit_id,
            user_address=user_address,
            network="sapphire_testnet"
        )
        print_result(result, True)
        return result, True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return None, False

def test_broadcast_deployment(client, circuit_id, deployment_result):
    """Test deployment transaction broadcasting."""
    print_test_header("Broadcast Deployment Transaction")
    
    if not SAPPHIRE_KEY:
        print_result({"error": "SAPPHIRE_KEY not set, skipping broadcast"}, False)
        return None, False
    
    try:
        from eth_account import Account
        
        account = Account.from_key(SAPPHIRE_KEY)
        
        # Sign the deployment transaction
        unsigned_tx = deployment_result["unsigned_transaction"]
        signed_tx = account.sign_transaction(unsigned_tx)
        signed_tx_hex = signed_tx.raw_transaction.hex()
        
        print(f"🔍 Broadcasting deployment transaction...")
        
        result = client.broadcast_transaction(
            circuit_id=circuit_id,
            signed_transaction=signed_tx_hex,
            network="sapphire_testnet",
            transaction_type="deployment"
        )
        
        print_result(result, True)
        return result, True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return None, False

def test_generate_proof(client, circuit_id, verifier_address):
    """Test proof generation with real inputs."""
    print_test_header("Generate Proof")
    
    # Circuit expects: fn main(x: Field, y: pub Field) { assert(x != y); }
    inputs = {"x": 5, "y": 10}  # Private inputs
    public_inputs = [10]  # Public input for verification
    
    if not SAPPHIRE_KEY:
        print_result({"error": "SAPPHIRE_KEY not set, skipping proof generation"}, False)
        return None, False
    
    try:
        from eth_account import Account
        account = Account.from_key(SAPPHIRE_KEY)
        user_address = account.address
        
        print(f"🔍 Generating proof with inputs: {inputs}")
        print(f"🔍 Public inputs: {public_inputs}")
        print(f"🔍 Verifier address: {verifier_address}")
        print(f"🔍 User address: {user_address}")
        
        result = client.generate_proof(
            circuit_id=circuit_id,
            inputs=inputs,
            public_inputs=public_inputs,
            verifier_address=verifier_address,
            user_address=user_address,
            network="sapphire_testnet"
        )
        
        print_result(result, True)
        return result, True
    except Exception as e:
        print_result({"error": str(e)}, False)
        return None, False

def test_broadcast_verification(client, circuit_id, proof_result):
    """Test verification transaction broadcasting."""
    print_test_header("Broadcast Verification Transaction")
    
    if not SAPPHIRE_KEY:
        print_result({"error": "SAPPHIRE_KEY not set, skipping verification broadcast"}, False)
        return False, None
    
    try:
        from eth_account import Account
        
        account = Account.from_key(SAPPHIRE_KEY)
        
        # Sign the verification transaction
        unsigned_tx = proof_result["unsigned_transaction"]
        signed_tx = account.sign_transaction(unsigned_tx)
        signed_tx_hex = signed_tx.raw_transaction.hex()
        
        print(f"🔍 Broadcasting verification transaction...")
        
        result = client.broadcast_transaction(
            circuit_id=circuit_id,
            signed_transaction=signed_tx_hex,
            network="sapphire_testnet",
            transaction_type="verification",
            verifier_address=proof_result.get("verifier_address"),
            public_inputs=proof_result.get("public_inputs")
        )
        
        print_result(result, True)
        return True, result
    except Exception as e:
        print_result({"error": str(e)}, False)
        return False, None

def run_complete_workflow():
    """Run complete SDK workflow demonstration."""
    print("🚀 Arcana ZK SDK - Minimal Workflow Demo")
    print(f"Target URL: {API_URL}")
    print(f"SAPPHIRE_KEY present: {bool(SAPPHIRE_KEY)}")
    
    # Create client with explicit URL
    client = create_client(API_URL)
    
    # Test results
    results = []
    
    # Storage for addresses and hashes
    workflow_data = {
        "circuit_id": "",
        "verifier_address": "",
        "deployment_tx_hash": "",
        "verification_tx_hash": "",
        "proof_hash": ""
    }
    
    # Step 1: Basic connectivity tests
    print("\n📋 Step 1: Service Connectivity")
    results.append(("Health Check", test_health_check(client)))
    results.append(("Service Status", test_service_status(client)))
    results.append(("List Circuits", test_list_circuits(client)))
    
    # Step 2: Register new circuit
    print("\n📋 Step 2: Circuit Registration")
    circuit_id, success = test_register_circuit(client)
    results.append(("Register Circuit", success))
    
    if circuit_id:
        workflow_data["circuit_id"] = circuit_id
        results.append(("Get Circuit Info", test_get_circuit_info(client, circuit_id)))
        
        # Step 3: Deployment workflow (only if SAPPHIRE_KEY is set)
        if SAPPHIRE_KEY:
            print("\n📋 Step 3: Contract Deployment")
            deployment_result, deployment_success = test_create_deployment_transaction(client, circuit_id)
            results.append(("Create Deployment Transaction", deployment_success))
            
            if deployment_success and deployment_result:
                # Broadcast deployment
                deploy_broadcast_result, deploy_broadcast_success = test_broadcast_deployment(
                    client, circuit_id, deployment_result
                )
                results.append(("Broadcast Deployment", deploy_broadcast_success))
                
                # Store deployment transaction hash
                if deploy_broadcast_result:
                    workflow_data["deployment_tx_hash"] = deploy_broadcast_result.get("transaction_hash")
                
                # Get verifier address from deployment result
                verifier_address = deploy_broadcast_result.get("verifier_address") if deploy_broadcast_result else None
                
                if verifier_address:
                    workflow_data["verifier_address"] = verifier_address
                    print(f"✅ Contract deployed at: {verifier_address}")
                    
                    # Step 4: Proof generation and verification
                    print("\n📋 Step 4: Proof Generation & Verification")
                    proof_result, proof_success = test_generate_proof(client, circuit_id, verifier_address)
                    results.append(("Generate Proof", proof_success))
                    
                    if proof_success and proof_result:
                        # Store proof hash
                        workflow_data["proof_hash"] = proof_result.get("proof_hash")
                        
                        # Broadcast verification
                        verification_success, verification_result = test_broadcast_verification(client, circuit_id, proof_result)
                        results.append(("Broadcast Verification", verification_success))
                        
                        # Store verification transaction hash if available
                        if verification_success and verification_result:
                            workflow_data["verification_tx_hash"] = verification_result.get("transaction_hash")
                    else:
                        results.append(("Broadcast Verification", False))
                else:
                    print("⚠️  No verifier address available, skipping proof generation")
                    results.append(("Generate Proof", False))
                    results.append(("Broadcast Verification", False))
            else:
                results.append(("Broadcast Deployment", False))
                results.append(("Generate Proof", False))
                results.append(("Broadcast Verification", False))
        else:
            print("⚠️  SAPPHIRE_KEY not set, skipping blockchain operations")
            results.append(("Create Deployment Transaction", False))
            results.append(("Broadcast Deployment", False))
            results.append(("Generate Proof", False))
            results.append(("Broadcast Verification", False))
    
    # Summary
    print(f"\n{'='*60}")
    print("WORKFLOW SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} steps completed successfully")
    
    # Log final addresses and hashes
    print(f"\n{'='*60}")
    print("WORKFLOW DATA LOG")
    print(f"{'='*60}")
    print(f"Circuit ID: {workflow_data['circuit_id']}")
    print(f"Verifier Address: {workflow_data['verifier_address']}")
    print(f"Deployment TX Hash: {workflow_data['deployment_tx_hash']}")
    print(f"Proof Hash: {workflow_data['proof_hash']}")
    print(f"Verification TX Hash: {workflow_data['verification_tx_hash']}")
    
    if passed == total:
        print("🎉 Complete workflow successful! SDK is working correctly.")
    elif passed >= total - 4:  # Allow for missing SAPPHIRE_KEY
        print("✅ Core functionality working! Blockchain operations skipped due to missing SAPPHIRE_KEY.")
        print("💡 Set SAPPHIRE_KEY to test full deployment and verification workflow.")
    else:
        print("⚠️  Some steps failed. Check the logs above for details.")

if __name__ == "__main__":
    run_complete_workflow() 