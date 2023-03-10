ARG UBUNTU_VER=20.04
FROM ubuntu:${UBUNTU_VER}
ENV DEBIAN_FRONTEND=noninteractive

# # Install basic system utilities.
RUN apt-get update -y && apt-get install -y \
      build-essential \
      g++ \
      cmake \
      git-all \
      vim \
      default-jre \
      gawk \
      curl \
      wget \
      jq 

# ### python

# install miniconda, taken from
# https://github.com/ContinuumIO/docker-images/blob/master/miniconda3/debian/Dockerfile
ARG CONDA_VERSION=py310_22.11.1-1
ARG DEFAULT_PYTHON_VERSION=3.9
RUN set -x && \
    MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-${CONDA_VERSION}-Linux-x86_64.sh"; \
    SHA256SUM="00938c3534750a0e4069499baf8f4e6dc1c2e471c86a59caa0dd03f4a9269db6"; \
    wget "${MINICONDA_URL}" -O miniconda.sh -q && \
    echo "${SHA256SUM} miniconda.sh" > shasum && \
    if [ "${CONDA_VERSION}" != "latest" ]; then sha256sum --check --status shasum; fi && \
    mkdir -p /opt && \
    bash miniconda.sh -b -p /opt/conda && \
    rm miniconda.sh shasum && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate base" >> ~/.bashrc && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    /opt/conda/bin/conda clean -afy && \
    /opt/conda/bin/conda install -y python=${DEFAULT_PYTHON_VERSION}

ENV PATH="$PATH:/opt/conda/bin"


# ### Install Python packages listed in 'requirements.txt' using pip.


# USER jovyan
WORKDIR /home/jovyan

COPY . graph_rewrite
RUN pip install -e graph_rewrite

CMD ["/bin/bash"]