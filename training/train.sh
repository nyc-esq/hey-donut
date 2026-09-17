#!/bin/bash
pip install --quiet --no-cache-dir tensorboard 'datasets==2.19.0' 'fsspec<=2024.3.1' audiomentations mmap_ninja pymicro-features soundfile librosa 2>&1 | tail -1
cd /w
nice -n 15 python -m microwakeword.model_train_eval \
  --training_config=/w/training_parameters.yaml \
  --train 1 \
  --restore_checkpoint 1 \
  --test_tf_nonstreaming 0 \
  --test_tflite_nonstreaming 0 \
  --test_tflite_nonstreaming_quantized 0 \
  --test_tflite_streaming 0 \
  --test_tflite_streaming_quantized 1 \
  --use_weights "best_weights" \
  mixednet \
  --pointwise_filters "64,64,64,64" \
  --repeat_in_block  "1, 1, 1, 1" \
  --mixconv_kernel_sizes '[5], [7,11], [9,15], [23]' \
  --residual_connection "0,0,0,0" \
  --first_conv_filters 32 \
  --first_conv_kernel_size 5 \
  --stride 3
echo "TRAINING-EXIT=$?"
