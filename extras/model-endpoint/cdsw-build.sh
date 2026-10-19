#!/bin/bash
set -eu

echo "Checking model in build snapshot..."
echo "90defe5e1199ac4265916a362b47f6d0ecc24430c97fd047851445842da53a04  model/Unet.onnx" | sha256sum -c -

pip3 install -r requirements.txt
