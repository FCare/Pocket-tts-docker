FROM nvidia/cuda:12.9.1-cudnn-runtime-ubuntu24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv git \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir \
        torch \
        --index-url https://download.pytorch.org/whl/cu129

WORKDIR /app

RUN git clone https://github.com/kyutai-labs/pocket-tts.git \
    && git -C pocket-tts checkout d529606ced20a8de5afc8740a170169858a8afb3

COPY pocket-tts.patch .
RUN git -C pocket-tts apply ../pocket-tts.patch

RUN pip install --no-cache-dir -e pocket-tts

ENTRYPOINT ["pocket-tts"]
