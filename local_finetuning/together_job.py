"""Upload, quote, inspect, or export a Together job. Never starts paid training."""
import argparse
import json
from pathlib import Path

MODEL = "Qwen/Qwen3.5-9B"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="Read credentials from this file without changing it")
    commands = parser.add_subparsers(dest="command", required=True)
    upload = commands.add_parser("upload")
    upload.add_argument("file", type=Path)
    commands.add_parser("file-status").add_argument("file_id")
    preview = commands.add_parser("preview")
    preview.add_argument("file_id")
    preview.add_argument("--top-k", type=int, default=50)
    estimate = commands.add_parser("estimate")
    estimate.add_argument("--training-file", required=True)
    estimate.add_argument("--validation-file", required=True)
    commands.add_parser("status").add_argument("job_id")
    download = commands.add_parser("download")
    download.add_argument("job_id")
    download.add_argument("--checkpoint", choices=["merged", "adapter"], default="merged")
    download.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.env_file:
        if not args.env_file.is_file():
            parser.error("Credential file does not exist")
        from dotenv import load_dotenv
        load_dotenv(args.env_file, override=True)
    from together import Together

    client = Together(max_retries=0)
    if args.command == "upload":
        result = client.files.upload(file=str(args.file), purpose="fine-tune", check=True)
    elif args.command == "file-status":
        result = client.files.retrieve(args.file_id)
    elif args.command == "preview":
        result = client.fine_tuning.preview(
            model=MODEL, training_file=args.file_id, top_k=args.top_k,
            train_on_inputs=False, training_method="sft",
        )
    elif args.command == "estimate":
        result = client.fine_tuning.estimate_price(
            training_file=args.training_file, validation_file=args.validation_file,
            model=MODEL, n_epochs=1, n_evals=1,
            training_method={"method": "sft", "train_on_inputs": "auto"},
            training_type={"type": "Lora", "lora_r": 16, "lora_alpha": 32},
        )
    elif args.command == "status":
        result = client.fine_tuning.retrieve(id=args.job_id)
    else:
        if args.output.exists():
            parser.error("Output already exists; choose a new path.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        response = client.fine_tuning.content(ft_id=args.job_id, checkpoint=args.checkpoint)
        response.write_to_file(str(args.output))
        print(f"Saved {args.output}; verify and extract this archive before conversion.")
        return
    print(result.model_dump_json(indent=2) if hasattr(result, "model_dump_json") else json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
