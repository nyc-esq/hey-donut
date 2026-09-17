# Plain python base: let microWakeWord install its OWN tensorflow.
# Do NOT start from tensorflow/tensorflow - it ships tensorflow-cpu and the
# resulting double-install collides at the C++ ABI level.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      git wget ffmpeg libsndfile1 build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone --depth 1 https://github.com/kahrendt/microWakeWord.git
RUN pip install --no-cache-dir -e /opt/microWakeWord

RUN git clone --depth 1 https://github.com/rhasspy/piper-sample-generator.git
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# fail the build early if the import is broken
RUN python -c "import tensorflow as tf; print('TF', tf.__version__)" \
 && python -c "from microwakeword import train; print('microwakeword train OK')"

WORKDIR /w
