#!/usr/bin/env python3
"""
CANON brain — QLoRA fine-tune (NVIDIA DGX A100 / any CUDA GPU).

Teaches an open model to generate validated HMI widget proposals from a machine
model + intent. 7B fits comfortably on one A100 80GB; 32B fits with QLoRA.

  python train_qlora.py \
      --base Qwen/Qwen2.5-Coder-7B-Instruct \
      --data data/train.jsonl --out out/canon-brain

Then merge/serve (see README) and point server/server.py at it.
"""
import argparse, torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    ap.add_argument("--data", default="data/train.jsonl")
    ap.add_argument("--out",  default="out/canon-brain")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--bsz", type=int, default=4)
    ap.add_argument("--lr", type=float, default=2e-4)
    a=ap.parse_args()

    tok=AutoTokenizer.from_pretrained(a.base)
    if tok.pad_token is None: tok.pad_token=tok.eos_token

    bnb=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                           bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    model=AutoModelForCausalLM.from_pretrained(a.base, quantization_config=bnb,
                                               device_map="auto", torch_dtype=torch.bfloat16)
    model=prepare_model_for_kbit_training(model)
    lora=LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
                    target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])
    model=get_peft_model(model, lora); model.print_trainable_parameters()

    ds=load_dataset("json", data_files=a.data, split="train")
    def fmt(ex): return {"text": tok.apply_chat_template(ex["messages"], tokenize=False)}
    ds=ds.map(fmt, remove_columns=ds.column_names)

    cfg=SFTConfig(output_dir=a.out, num_train_epochs=a.epochs, per_device_train_batch_size=a.bsz,
                  gradient_accumulation_steps=4, learning_rate=a.lr, lr_scheduler_type="cosine",
                  warmup_ratio=0.03, logging_steps=10, save_strategy="epoch", bf16=True,
                  max_seq_length=2048, packing=True, report_to="none")
    trainer=SFTTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tok)
    trainer.train()
    trainer.save_model(a.out); tok.save_pretrained(a.out)
    print("saved LoRA adapter to", a.out)

if __name__=="__main__": main()
