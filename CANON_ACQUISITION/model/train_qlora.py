#!/usr/bin/env python3
"""CANON-brain QLoRA fine-tune — run ONCE on the DGX A100 (needs a CUDA GPU).

Target base is a 3B model so the merged result quantizes to a ~2 GB GGUF that
runs on a laptop CPU with NO GPU (see export_gguf.py). 3B QLoRA uses well under
one A100 80GB; ~20-40 min for 2 epochs on this dataset.

  python train_qlora.py \
      --base Qwen/Qwen2.5-3B-Instruct \
      --data data/train.jsonl --out out/canon-brain-3b

Data rows are chat objects: {"messages":[system,user,assistant], ...} from
build_dataset.py. The assistant turn is the supervised target.

IMPORTANT env notes (see SETUP_DGX.md):
  * Needs CUDA-enabled torch (torch.cuda.is_available() must be True) — a
    "+cpu" torch build cannot use the A100 and bitsandbytes 4-bit needs CUDA.
  * torchvision is NOT needed; if a broken torchvision is installed it will
    crash the transformers import — uninstall it (pip uninstall -y torchvision)
    or use a clean env.
"""
import argparse
import os
import sys

# Belt-and-suspenders: stop transformers from importing a (possibly broken)
# torchvision. Must be set before transformers is imported.
os.environ.setdefault("TRANSFORMERS_NO_TORCHVISION", "1")
# reduce fragmentation OOMs on the shared A100
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

import torch  # noqa: E402


def die(msg):
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="Qwen/Qwen2.5-3B-Instruct",
                    help="3B keeps the CPU/GGUF build small. Qwen2.5-3B-Instruct (Apache-2.0) or Llama-3.2-3B-Instruct.")
    ap.add_argument("--data", default="data/train.jsonl")
    ap.add_argument("--out", default="out/canon-brain-3b")
    ap.add_argument("--epochs", type=float, default=1.0)   # 48k correct-by-construction rows; 1 epoch is plenty
    ap.add_argument("--bsz", type=int, default=8)
    ap.add_argument("--grad-accum", type=int, default=2)   # effective batch 16
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--maxlen", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=401)
    ap.add_argument("--max-samples", type=int, default=0,
                    help="cap training rows (0=all). Data is repetitive+correct-by-construction, "
                         "so a shuffled subset (e.g. 8000) trains the behaviour fast.")
    ap.add_argument("--grad-ckpt", action="store_true",
                    help="enable gradient checkpointing (saves VRAM, ~1.5x slower). Off by default "
                         "since bsz*maxlen is small enough to fit without it.")
    ap.add_argument("--packing", action="store_true",
                    help="enable sequence packing — OFF by default; it needs flash-attn, "
                         "else eager attention builds an O(L^2) mask and OOMs.")
    ap.add_argument("--no-4bit", action="store_true",
                    help="skip bitsandbytes 4-bit (plain LoRA in bf16; needs more VRAM but no bnb).")
    a = ap.parse_args()

    if not torch.cuda.is_available():
        die("torch.cuda.is_available() is False — this torch build cannot use the A100.\n"
            "       Fix: make a CUDA env (see SETUP_DGX.md):\n"
            "         conda create -n canon python=3.11 -y && conda activate canon\n"
            "         pip install torch --index-url https://download.pytorch.org/whl/cu124\n"
            "         pip install transformers peft trl bitsandbytes accelerate datasets sentencepiece")
    print(f"CUDA OK: {torch.cuda.get_device_name(0)}  (torch {torch.__version__}, cuda {torch.version.cuda})")

    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer, SFTConfig

    tok = AutoTokenizer.from_pretrained(a.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    quant_cfg = None
    if not a.no_4bit:
        from transformers import BitsAndBytesConfig
        quant_cfg = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                       bnb_4bit_compute_dtype=torch.bfloat16,
                                       bnb_4bit_use_double_quant=True)
    # sdpa = PyTorch's fused scaled-dot-product attention: fast, built in, no
    # flash-attn install. (eager is ~10-15x slower; flash-attn2 needs compiling.)
    model = AutoModelForCausalLM.from_pretrained(
        a.base, quantization_config=quant_cfg, device_map="auto",
        torch_dtype=torch.bfloat16, attn_implementation="sdpa")
    if quant_cfg is not None:
        model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"]))
    model.config.use_cache = False   # required with gradient checkpointing
    model.print_trainable_parameters()

    ds = load_dataset("json", data_files=a.data, split="train")
    if a.max_samples and a.max_samples < len(ds):
        ds = ds.shuffle(seed=a.seed).select(range(a.max_samples))
        print(f"using a shuffled subset of {a.max_samples} rows")

    def fmt(ex):
        return {"text": tok.apply_chat_template(ex["messages"], tokenize=False,
                                                add_generation_prompt=False)}
    ds = ds.map(fmt, remove_columns=ds.column_names)

    # trl/transformers rename & drop SFTConfig args across versions — pass only
    # the kwargs THIS installed SFTConfig actually accepts (no crash on drift).
    import dataclasses
    import inspect
    try:
        valid = {f.name for f in dataclasses.fields(SFTConfig)}
    except TypeError:
        valid = set(inspect.signature(SFTConfig.__init__).parameters)

    want = dict(
        output_dir=a.out, num_train_epochs=a.epochs,
        per_device_train_batch_size=a.bsz, gradient_accumulation_steps=a.grad_accum,
        learning_rate=a.lr, lr_scheduler_type="cosine", warmup_ratio=0.03,
        logging_steps=20, save_strategy="epoch", bf16=True, seed=a.seed,
        packing=a.packing, dataset_text_field="text", report_to="none",
        gradient_checkpointing=a.grad_ckpt,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )
    if "max_length" in valid:
        want["max_length"] = a.maxlen           # newer trl
    elif "max_seq_length" in valid:
        want["max_seq_length"] = a.maxlen       # older trl
    dropped = sorted(k for k in want if k not in valid)
    if dropped:
        print("note: SFTConfig ignoring unsupported args:", dropped)
    cfg = SFTConfig(**{k: v for k, v in want.items() if k in valid})

    try:
        trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, processing_class=tok)
    except TypeError:
        trainer = SFTTrainer(model=model, args=cfg, train_dataset=ds, tokenizer=tok)
    trainer.train()
    trainer.save_model(a.out)
    tok.save_pretrained(a.out)
    print("saved LoRA adapter ->", a.out)
    print("next: python export_gguf.py --base", a.base, "--adapter", a.out,
          "--llama-cpp $HOME/llama.cpp --quant Q4_K_M")


if __name__ == "__main__":
    main()
