FROM python:3.8-bullseye
RUN pip3 install atheris
# RUN apt-get update && apt-get install -y \
#     liblzma-dev \ 
#     make \ 
#     clang \ 
#     git \
#  && rm -rf /var/lib/apt/lists/*
COPY . /detools
WORKDIR /detools
RUN git submodule init && git submodule update
RUN python3 -m pip install . && chmod +x fuzz/fuzz.py
