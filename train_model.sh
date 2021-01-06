#!/bin/sh

cd ToD-BERT
CUDA_VISIBLE_DEVICES=0 python my_tod_pretraining.py \
    --task=usdl \
    --model_type=distilbert \
    --model_name_or_path=distilbert-base-german-cased \
    --output_dir=../save/pretrain/ToD-BERT-JNT \
    --do_train \
    --do_eval \
    --mlm \
    --evaluate_during_training \
    --save_steps=2500 --logging_steps=1000 \
    --per_gpu_train_batch_size=8 --per_gpu_eval_batch_size=8 \
    --add_rs_loss \
    --max_seq_length 512 \
    --data_path ../data \
    --dataset '["reddit"]' \
    --holdout_dataset '["reddit"]'
