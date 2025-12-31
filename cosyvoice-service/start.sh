#!/bin/bash

# Start Nginx
service nginx start

# Disable DeepSpeed operations to avoid CUDA compilation checks
export DS_BUILD_OPS=0
export DS_BUILD_FUSED_ADAM=0
export DS_BUILD_CPU_ADAM=0
export DS_BUILD_UTILS=0
export DS_BUILD_AIO=0
export DS_BUILD_SPARSE_ATTN=0

# Change to application directory
cd /opt/CosyVoice

# Generate gRPC files if they don't exist or proto file is newer
if [ ! -f runtime/python/grpc/cosyvoice_pb2.py ] || [ runtime/python/grpc/cosyvoice.proto -nt runtime/python/grpc/cosyvoice_pb2.py ]; then
    echo "Generating gRPC files..."
    cd runtime/python/grpc && python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. cosyvoice.proto
    cd /opt/CosyVoice
fi

# Build command with optional vLLM flag
CMD="python3 runtime/python/fastapi/server.py --port ${PORT:-50005} --model_dir ${MODEL_DIR:-./models/trained_models20250728/cosyvoice2/}"
if [ "${ENABLE_VLLM}" = "true" ]; then
    CMD="${CMD} --load_vllm"
    echo "Starting with vLLM acceleration enabled..."
else
    echo "Starting with standard inference..."
fi

$CMD &

# Wait for service to start and perform warmup
echo "Waiting for service to start..."
sleep 30

# Run warmup script
if [ -f /opt/CosyVoice/warmup.py ]; then
    echo "Running warmup inference..."
    python3 /opt/CosyVoice/warmup.py
    echo "Warmup complete. System ready!"
else
    echo "Warmup script not found, skipping warmup"
fi

# Keep container running
tail -f /dev/null
