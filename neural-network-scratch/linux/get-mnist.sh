#!/usr/bin/env bash
# Download and unpack MNIST into ./data. Built by clavexis — github.com/clavexis
set -euo pipefail
mkdir -p data && cd data
BASE="https://ossci-datasets.s3.amazonaws.com/mnist"
for f in train-images-idx3-ubyte train-labels-idx1-ubyte t10k-images-idx3-ubyte t10k-labels-idx1-ubyte; do
  if [ ! -f "$f" ]; then
    echo "Downloading $f..."
    curl -fsSL "$BASE/$f.gz" -o "$f.gz" && gunzip -f "$f.gz"
  fi
done
echo "MNIST ready in ./data — train with:  ./neuralnet --mnist ./data --epochs 20"
