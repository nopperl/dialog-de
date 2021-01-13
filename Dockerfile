# Apex installation part adapted from https://github.com/NVIDIA/apex/blob/master/examples/docker/Dockerfile
# Base image must at least have pytorch and CUDA installed.
ARG BASE_IMAGE=pytorch/pytorch:1.7.0-cuda11.0-cudnn8-devel
FROM $BASE_IMAGE
ARG BASE_IMAGE
RUN echo "Installing Apex on top of ${BASE_IMAGE}"
# make sure we don't overwrite some existing directory called "apex"
WORKDIR /tmp/unique_for_install
# uninstall Apex if present, twice to make absolutely sure :)
RUN pip uninstall -y apex || :
RUN pip uninstall -y apex || :
# SHA is something the user can touch to force recreation of this Docker layer,
# and therefore force cloning of the latest version of Apex
RUN apt-get update
RUN apt-get install git -y
RUN SHA=ToUcHMe git clone https://github.com/NVIDIA/apex.git
WORKDIR /tmp/unique_for_install/apex
RUN pip install -v --no-cache-dir --global-option="--cpp_ext" --global-option="--cuda_ext" .

# faiss installation part adapted from https://github.com/facebookresearch/faiss/blob/master/.circleci/Dockerfile.faiss_gpu
WORKDIR /tmp/unique_for_install
# Install python3, swig, and openblas.
RUN apt-get update && \
        apt-get install -y python3-dev python3-pip swig libopenblas-dev

# Install recent CMake.
RUN apt-get install -y wget && \
        wget -nv -O - https://github.com/Kitware/CMake/releases/download/v3.17.1/cmake-3.17.1-Linux-x86_64.tar.gz | tar xzf - --strip-components=1 -C /usr && \
        apt remove -y wget

# Install numpy/scipy/pytorch for python tests.
RUN pip install numpy scipy torch

RUN SHA=ToUcHmE git clone https://github.com/facebookresearch/faiss

WORKDIR /tmp/unique_for_install/faiss

RUN cmake -B build \
        -DFAISS_ENABLE_GPU=ON \
        -DFAISS_ENABLE_PYTHON=ON \
        -DBUILD_TESTING=ON \
        -DCMAKE_CUDA_FLAGS="-gencode arch=compute_61,code=sm_61" \
        .

RUN make -C build -j8
RUN cd build/faiss/python && python setup.py install

# Installation of dialog-de
WORKDIR /tmp/unique_for_install
COPY . /tmp/unique_for_install/dialog-de
WORKDIR /tmp/unique_for_install/dialog-de
RUN pip install -r requirements.txt
RUN pip install -e .
WORKDIR /workspace

