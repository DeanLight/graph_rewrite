ARG UBUNTU_VER=22.04
FROM ubuntu:${UBUNTU_VER}
ENV DEBIAN_FRONTEND=noninteractive

# Install basic system utilities.
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
      jq \
      python3-pip


### python

ARG CONDA_VER=latest
ARG OS_TYPE=x86_64
ARG PY_VER=3.9
# miniconda with correct python version
ARG CONDA_VER
ARG OS_TYPE
# Install miniconda to /miniconda
RUN curl -LO "http://repo.continuum.io/miniconda/Miniconda3-${CONDA_VER}-Linux-${OS_TYPE}.sh"
RUN bash Miniconda3-${CONDA_VER}-Linux-${OS_TYPE}.sh -p /miniconda -b
RUN rm Miniconda3-${CONDA_VER}-Linux-${OS_TYPE}.sh
ENV PATH=/miniconda/bin:${PATH}
RUN conda update -y conda

### Install Python packages listed in 'requirements.txt' using pip.
COPY . graph_rewrite
RUN pip install -e graph_rewrite

# USER jovyan
# WORKDIR /home/jovyan

#RUN python /spanner_workbench/src/rgxlog-interpreter/src/rgxlog/stdlib/nlp.py
#RUN python /spanner_workbench/src/rgxlog-interpreter/src/rgxlog/stdlib/rust_spanner_regex.py
