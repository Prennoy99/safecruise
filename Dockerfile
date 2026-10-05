# syntax=docker/dockerfile:1
#
# SafeCruise toolchain image: one image for the devcontainer and every CI job (ADR-000 D-20).
# Every external input is pinned by digest, version or SHA-256.

FROM ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55

ARG DEBIAN_FRONTEND=noninteractive
ARG UV_VERSION=0.12.23
ARG UV_SHA256=9167d72b3319674b6303c4cbe071854bba13ebdf3d76b1a7cbdc175471fb66d6
ARG MICROMAMBA_VERSION=2.9.0-0
ARG MICROMAMBA_SHA256=366cd9cd8be14df1ab8ed50352a82111082a36686b2d389fdb79a92c3fafb3e3
ARG SYSML_KERNEL_VERSION=0.62.0

# C toolchain (GCC 14, D-08), static analysis, CAN utilities, Python 3.12, Java 21.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc-14 g++-14 cmake ninja-build make \
      cppcheck clang-format \
      python3.12 python3.12-venv \
      openjdk-21-jre-headless \
      can-utils iproute2 \
      git ca-certificates curl bzip2 \
 && rm -rf /var/lib/apt/lists/* \
 && ln -s /usr/bin/gcov-14 /usr/local/bin/gcov

# uv, used only to install the locked Python dependencies.
RUN curl -fsSL --retry 5 --retry-all-errors --connect-timeout 30 --max-time 600 -o /tmp/uv.tgz \
      "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz" \
 && echo "${UV_SHA256}  /tmp/uv.tgz" | sha256sum -c - \
 && tar -xzf /tmp/uv.tgz -C /usr/local/bin --strip-components=1 \
 && rm /tmp/uv.tgz

# Python dependencies from uv.lock into /opt/venv.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=/usr/bin/python3.12 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy
COPY pyproject.toml uv.lock /tmp/deps/
RUN cd /tmp/deps \
 && touch README.md \
 && uv sync --frozen --no-install-project --no-cache \
 && rm -rf /tmp/deps
ENV PATH=/opt/venv/bin:${PATH}

# SysML v2 Pilot Implementation Jupyter kernel (conda-forge) in its own prefix.
RUN curl -fsSL --retry 5 --retry-all-errors --connect-timeout 30 --max-time 600 -o /usr/local/bin/micromamba \
      "https://github.com/mamba-org/micromamba-releases/releases/download/${MICROMAMBA_VERSION}/micromamba-linux-64" \
 && echo "${MICROMAMBA_SHA256}  /usr/local/bin/micromamba" | sha256sum -c - \
 && chmod +x /usr/local/bin/micromamba \
 && MAMBA_ROOT_PREFIX=/opt/mamba micromamba create -y -p /opt/sysml -c conda-forge \
      "jupyter-sysml-kernel=${SYSML_KERNEL_VERSION}" \
 && MAMBA_ROOT_PREFIX=/opt/mamba micromamba clean -a -y \
 && rm -rf /opt/mamba/pkgs
ENV JUPYTER_PATH=/opt/sysml/share/jupyter \
    SYSML_KERNEL_VERSION=${SYSML_KERNEL_VERSION}

WORKDIR /work
