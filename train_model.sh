#!/bin/sh
AMP=""
KMEANS=""
while [ ! -z "$1" ];do
   case "$1" in
        --amp)
          AMP=--fp16
          ;;
        --kmeans)
          KMEANS="--per_gpu_train_batch_size 4 \
              --per_gpu_eval_batch_size 8 \
              --negative_sampling_by_kmeans \
	      --nb_kmeans 100 \
	      --nb_addition_negresponse_per_sample 4"
          ;;
        *)
       echo "Incorrect flag provided"
   esac
shift
done

cd ToD-BERT
CUDA_VISIBLE_DEVICES=0 python my_tod_pretraining.py \
    --task=usdl \
    --model_type=distilbert \
    --model_name_or_path=distilbert-base-german-cased \
    --output_dir=../save/pretrain/ToD-BERT-German-JNT \
    --overwrite_output_dir \
    --do_train \
    --do_eval \
    --mlm \
    --evaluate_during_training \
    --save_steps=2500 --logging_steps=1000 \
    --save_total_limit 2 \
    --per_gpu_train_batch_size=8 --per_gpu_eval_batch_size=8 \
    --add_rs_loss \
    --max_seq_length 512 \
    --patience 5 \
    --data_path ../data \
    --dataset '["reddit"]' \
    --holdout_dataset '["reddit"]' \
    ${AMP} \
    ${KMEANS}
