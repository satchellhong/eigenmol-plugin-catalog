#!/bin/sh
# Setup template: a private Python environment built inside the plugin folder.
#
# EigenMol runs this from the plugin's own folder after the user approved it
# (Plugins ▸ Set up). It builds everything the plugin needs **inside this
# folder** and changes nothing else on the machine:
#
#   .tools/micromamba   a self-contained package manager (no conda needed)
#   .mamba/             its package cache, removed when the build finishes
#   env/                Python 3.12 with NumPy from conda-forge
#                       (replace NumPy with the packages your plugin needs)
#
# micromamba is pinned and checked against the SHA-256 its release publishes;
# conda-forge packages are verified by micromamba against the channel's own
# checksums. Pin exact versions of anything your results depend on. Removing the plugin removes the folder and all of it.
# Running this again is safe: a working environment is kept.
set -eu

DIR="${EIGENMOL_PLUGIN_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$DIR"

MICROMAMBA_VERSION="2.10.0-0"
NUMPY_VERSION="2"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)
    MAMBA_PLATFORM="osx-arm64"
    MAMBA_SHA256="c547639f5caf742236641c362746abb4a3505774753ecd08fe341643670c4c01"
    ;;
  Darwin-x86_64)
    MAMBA_PLATFORM="osx-64"
    MAMBA_SHA256="8421462a1ef1df9f7acd114f9e2a24c1332ce4f4e29f44465b4acb44e2755172"
    ;;
  Linux-x86_64)
    MAMBA_PLATFORM="linux-64"
    MAMBA_SHA256="701f39c06f8e6a670a0e186c8479b9e5c0502a2f0cda6cef65d83bdd2875e8bd"
    ;;
  Linux-aarch64|Linux-arm64)
    MAMBA_PLATFORM="linux-aarch64"
    MAMBA_SHA256="3bb56786e21b9b24024f599fe9185b4a59dc3f9f59937a42311ee583adbbb23c"
    ;;
  *)
    echo "This plugin's setup supports macOS (Apple silicon, Intel) and Linux (x86_64, arm64); this machine is $(uname -s) $(uname -m)." >&2
    exit 3
    ;;
esac

step() { echo "==> $*"; }

sha256_of() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    sha256sum "$1" | cut -d' ' -f1
  fi
}

mkdir -p .tools

if [ ! -x .tools/micromamba ]; then
  step "Downloading micromamba $MICROMAMBA_VERSION for $MAMBA_PLATFORM"
  curl -fsSL --retry 3 --proto '=https' --tlsv1.2 \
    "https://github.com/mamba-org/micromamba-releases/releases/download/$MICROMAMBA_VERSION/micromamba-$MAMBA_PLATFORM" \
    -o .tools/micromamba.part
  actual="$(sha256_of .tools/micromamba.part)"
  if [ "$actual" != "$MAMBA_SHA256" ]; then
    rm -f .tools/micromamba.part
    echo "micromamba does not match its published checksum (got $actual)." >&2
    exit 4
  fi
  mv .tools/micromamba.part .tools/micromamba
  chmod +x .tools/micromamba
fi

if [ ! -x env/bin/python ] || ! env/bin/python -c "import numpy" >/dev/null 2>&1; then
  rm -rf env
  step "Building the private Python environment from conda-forge"
  MAMBA_ROOT_PREFIX="$DIR/.mamba" .tools/micromamba create -y \
    -p "$DIR/env" -c conda-forge --override-channels \
    "python=3.12" "numpy=$NUMPY_VERSION"
  rm -rf "$DIR/.mamba/pkgs"
fi

step "Checking"
env/bin/python -c "import numpy; print('NumPy', numpy.__version__)"
echo "Set up finished. Everything is inside $DIR."
