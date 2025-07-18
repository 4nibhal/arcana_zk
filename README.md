# Arcana ZK Protocol

Zero-Knowledge proof generation and verification service using Noir and Barretenberg with offline signing for enhanced security.


# WARNING!!!
- Use it at your own risk
- Solidity Verifier in barretenberg is not production ready
- THIS CODE IS NOT READY PRODUCTION

## Overview

Arcana ZK Protocol provides a complete ZK proof workflow:
- Circuit registration and compilation using Noir
- ZK proof generation using Barretenberg
- On-chain verification with offline signing
- Multi-network support (Sapphire, Ethereum)

## Features

- **ZK Proof Generation**: Real Noir/Barretenberg integration
- **Offline Signing**: Private keys never leave user devices
- **Multi-Network**: Sapphire Testnet/Mainnet, Ethereum Sepolia/Mainnet
- **Circuit Management**: Register, compile, deploy circuits
- **Universal ABI**: Compatible verifier contracts across networks

## Installation

### Prerequisites

- Python 3.12+
- uv (Python package manager)
- Docker (for containerized deployment)
- Oasis CLI (for ROFL deployment and build)

### Setup

```bash

# Install dependencies
uv sync

# Activate environment
source .venv/bin/activate
```

### API Endpoints

- `POST /register` - Register and compile circuit
- `POST /deploy` - Create unsigned deployment transaction
- `POST /proof` - Generate proof and create verification transaction
- `POST /broadcast` - Broadcast signed transaction
- `GET /circuits` - List circuits
- `GET /status` - Service status

## Architecture

### Offline Signing Flow

1. **Circuit Registration**: Register and compile circuit
2. **Deployment**: Create unsigned deployment transaction
3. **Client Signing**: User signs transaction offline
4. **Broadcast**: Service broadcasts pre-signed transaction
5. **Proof Generation**: Generate ZK proof
6. **Verification**: Create and broadcast verification transaction

### Security

- **Zero Key Exposure**: All signing done offline
- **Universal ABI**: Same interface for all verifiers
- **Network Encryption**: Automatic Sapphire encryption when applicable

## Development

### Docker Deployment

```bash
# Build image
docker build -t arcana-zk-protocol .

# Or download from dockerHub
docker pull 4nibhal/arcana-zk-protocol:latest

# Run container
docker run -p 8000:8000 arcana-zk-protocol # if you build local

docker run -p 8000:8000 4nibhal/arcana-zk-protocol # if you pull from docker hub


# Once docker is running, you need to define some env vars
export SAPPHIRE_KEY="0x-YOUR-PRIVATE-KEY-HERE"
export API_URL="URL-HERE" # DEFAULT EXAMPLE_SDK_USE POINT TO "localhost:8000" check [example_sdk_use.py]

# Run exampe_sdk_use agaisnt docker ( test all endpoints with sample circuit )
uv run example_sdk_use.py
```


### ROFL deployment

- Actually you need access for your own ROFL node, to be able to expose the ports
- You can check doc to know how to deploy here: "https://docs.oasis.io/build/rofl/quickstart#roflize-the-bot"

## Configuration

### Networks

- `sapphire_testnet`: https://testnet.sapphire.oasis.dev
- `sapphire_mainnet`: https://sapphire.oasis.io
- `ethereum_sepolia`: https://sepolia.etherscan.io
- `ethereum_mainnet`: https://mainnet.infura.io/v3/YOUR_PROJECT_ID
```

## Package Management

This project uses `uv` for Python package management:

- **Dependencies**: Managed in `pyproject.toml`
- **Lock file**: `uv.lock` ensures reproducible builds
- **SDK**: `arcana_sdk/` package with its own `pyproject.toml`
- **Installation**: `uv sync` installs all dependencies

## License

MIT License - see LICENSE file for details. 