FROM ubuntu:24.04

WORKDIR /app

# Install system dependencies including Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    wget \
    ca-certificates \
    bash \
    jq \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Install Solidity compiler
RUN add-apt-repository ppa:ethereum/ethereum && \
    apt-get update && \
    apt-get install -y solc && \
    rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install Nargo using noirup
RUN curl -L https://raw.githubusercontent.com/noir-lang/noirup/main/install | bash
ENV PATH="/root/.nargo/bin:${PATH}"
RUN bash -c "source ~/.bashrc && noirup -v 1.0.0-beta.4"

# Install bb using bbup
RUN curl -L https://raw.githubusercontent.com/AztecProtocol/aztec-packages/refs/heads/master/barretenberg/bbup/install | bash
ENV PATH="/root/.bb:${PATH}"
RUN bash -c "source ~/.bashrc && bbup"

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application code
COPY . .

# Create circuits directory
RUN mkdir -p circuits

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 