FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /opt/CosyVoice

# Update package sources and install dependencies
RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list
RUN apt-get update -y
RUN apt-get -y install git unzip git-lfs g++ nginx




# Set CUDA environment variables
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

# Disable DeepSpeed JIT compilation
ENV DS_BUILD_OPS=0
ENV DS_BUILD_FUSED_ADAM=0
ENV DS_BUILD_CPU_ADAM=0
ENV DS_BUILD_UTILS=0

# Fix MKL threading layer conflict with OpenMP
ENV MKL_THREADING_LAYER=GNU
ENV MKL_SERVICE_FORCE_INTEL=1

# Create a fake nvcc to satisfy DeepSpeed CUDA checks (only for inference, not training)
RUN mkdir -p /usr/local/cuda/bin && \
    echo '#!/bin/bash\necho "Cuda compilation tools, release 12.1, V12.1.105"' > /usr/local/cuda/bin/nvcc && \
    chmod +x /usr/local/cuda/bin/nvcc


# Copy only requirements for installation
COPY requirements.txt .
RUN pip3 install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
    
# Copy application code
COPY . /opt/CosyVoice
RUN chmod +x /opt/CosyVoice/start.sh

# We only pre-generate gRPC files with a temporary copy
COPY runtime/python/grpc/cosyvoice.proto /tmp/cosyvoice.proto
RUN mkdir -p /tmp/grpc && \
    cd /tmp/grpc && \
    python3 -m grpc_tools.protoc -I/tmp --python_out=. --grpc_python_out=. /tmp/cosyvoice.proto

# Configure Nginx (copy config file for installation)
COPY nginx.conf /etc/nginx/sites-enabled/cosyvoice
RUN rm -f /etc/nginx/sites-enabled/default

# Expose ports
EXPOSE 50001 8085

# Start services - script is mounted via volume
CMD ["/opt/CosyVoice/start.sh"]

