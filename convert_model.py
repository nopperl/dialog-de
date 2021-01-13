#!/usr/bin/env python3
from transformers.convert_pytorch_checkpoint_to_tf2 import convert_pt_checkpoint_to_tf

checkpoint_dir = "save/pretrain/ToD-BERT-German-JNT-apex-2/checkpoint-145000/pytorch_model.bin"
convert_pt_checkpoint_to_tf("distilbert", f"{checkpoint_dir}/pytorch_model.bin", f"{checkpoint_dir}/config.json", f"{checkpoint_dir}/tf_model.h5")
