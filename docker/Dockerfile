FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential autoconf automake libtool pkg-config git ca-certificates gawk python3 apertium lttoolbox lttoolbox-dev hfst libhfst-dev cg3 apertium-dev gettext zip unzip && rm -rf /var/lib/apt/lists/*
WORKDIR /opt
RUN git clone https://github.com/apertium/apertium-kaz.git && cd apertium-kaz && git checkout 95c6dd0d8536ee69a7058634b03a3e82100b6b6e && ./autogen.sh && make -j8

