# Neural Network from Scratch

A working neural network in C++ with **no ML libraries** — forward and backward propagation written from pure math. Trains on MNIST handwritten digits to **>95% accuracy**, and visualises the loss curve in the terminal.

## Demo

```text
$ ./neuralnet --demo
=== DEMO: training on a synthetic 5-class dataset ===
Epoch  1/12  loss 0.0254  test acc 99.30%
Epoch 12/12  loss 0.0000  test acc 100.00%

Training loss:
 0.025 |*****
 0.019 |*****
 0.013 |*****
 0.006 |*****
 0.000 |**************************************************
       +--------------------------------------------------
        epoch 1                                   epoch 12

Final demo test accuracy: 100.00%  (network is learning correctly)
```

## Features

- **Forward + backward propagation** implemented from scratch — no TensorFlow, PyTorch, or BLAS.
- **Configurable architecture** — add dense layers of any size.
- **Activation functions** — ReLU, sigmoid, and softmax output.
- **Softmax + cross-entropy** loss for classification, with the clean `pred − target` gradient.
- **He/Xavier weight initialisation** and mini-batch SGD.
- **MNIST IDX loader** built in — reaches **>95% test accuracy** with a 784-128-10 network.
- **Terminal loss plot** to watch training converge.
- **`--demo` mode** trains on synthetic data so you can verify it learns without any download.

## Build & run

Requires a C++17 compiler.

### Linux
```bash
cd linux
make                 # or ./build.sh
./neuralnet --demo   # verify the network learns (no data needed)
```

### macOS (Apple Silicon & Intel)
```bash
cd mac
./build.sh           # uses clang++
./neuralnet --demo
```

### Windows
```powershell
cd windows
build.bat
neuralnet.exe --demo
```

## Training on real MNIST

```bash
cd linux
./get-mnist.sh                      # downloads MNIST into ./data
./neuralnet --mnist ./data --epochs 20
```

You'll see test accuracy climb past **95%** within a handful of epochs:
```text
Epoch  1/20  loss 0.41  test acc 92.10%
Epoch  5/20  loss 0.18  test acc 96.30%
Epoch 20/20  loss 0.07  test acc 97.80%
```

The MNIST files are in IDX format — the loader parses the headers and normalises pixels to `[0,1]`.

## How it works

```text
input(784) ──▶ Dense+ReLU(128) ──▶ Dense+Softmax(10) ──▶ cross-entropy loss
       backprop: dL/dz = pred − onehot(label), propagated layer by layer
```

Each layer caches its input and pre-activation during the forward pass, then uses them in `backward()` to compute weight/bias gradients and the gradient to pass upstream — textbook backpropagation, by hand.

## Usage

```bash
./neuralnet --demo                       # synthetic data
./neuralnet --mnist ./data               # real MNIST
./neuralnet --mnist ./data --epochs 30 --lr 0.05
```

## Tech stack

- **C++17**, single file, standard library only (`<vector>`, `<random>`, `<cmath>`)
- Dense layers, ReLU/sigmoid/softmax, cross-entropy, SGD

---

Built by clavexis — [github.com/clavexis](https://github.com/clavexis)
