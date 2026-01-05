#### will be the primary directory where the qwen 2.5 7b CPT will be conducted

Project will have two enviorments to maximize resources efficieny 

Expected project folder structure (cab be susceptible to changes)

```text
qwen2.5-cpt-project/
├── local_workspace/                    # RUN THIS ON YOUR PC
│   ├── raw_data/                       # Original PDFs, dumps (Heavy files)
│   ├── processed_data/                 # Cleaned JSONL/Parquet files
│   ├── new_tokenizer/                  # Output of your new language tokenizer
│   ├── .env                            # HF_TOKEN, WANDB_API_KEY (Keep local!)
│   └── scripts/
│       ├── 1_clean_and_format.py       # Convert raw text to training format
│       ├── 2_train_new_tokenizer.py    # Train tokenizer on new langs
│       ├── 3_merge_tokenizers.py       # Merge new tokens into Qwen's tokenizer
│       └── 4_push_to_hub.py            # Upload processed data & tokenizer to HF
│
├── remote_workspace/                   # COPY THIS TO VAST.AI
│   ├── artifacts/                      # Folder for saved adapters/models
│   ├── setup_vast.sh                   # One-click install script for Vast.ai
│   ├── train_cpt_unsloth.py            # Main Unsloth training script
│   └── unsloth_config.yaml             # Hyperparameters (Learning rate, LoRA rank)
│
└── README.md                           # Documentation (you're here)
```
