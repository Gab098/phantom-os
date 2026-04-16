#!/usr/bin/env python3
import json
import subprocess
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import load_system_config, resolve_model_path

class PhantomTerminal:
    def __init__(self):
        self.config = load_system_config()
        self.llm_path = resolve_model_path(self.config.get("ai", {}).get("model_path"))
        self.server_port = int(self.config.get("ai", {}).get("server_port", 8080))
        self.server_url = f"http://127.0.0.1:{self.server_port}"
        self.history = []
        self.context = []
        self.model = None
        self.tokenizer = None
        
    def load_model(self):
        print(f"Loading model from {self.llm_path}...")
        try:
            model_path = Path(self.llm_path)
            if model_path.is_file() and model_path.suffix == ".gguf":
                from llama_cpp import Llama

                self.model = Llama(
                    model_path=str(model_path),
                    n_ctx=2048,
                    n_threads=os.cpu_count() or 4,
                    verbose=False
                )
            else:
                from transformers import AutoModelForCausalLM, AutoTokenizer

                self.tokenizer = AutoTokenizer.from_pretrained(str(model_path))
                self.model = AutoModelForCausalLM.from_pretrained(
                    str(model_path),
                    device_map="cpu",
                    torch_dtype="float32"
                )
            print("Model loaded successfully!")
            return True
        except Exception as e:
            print(f"Warning: Model not found at {self.llm_path}")
            print(f"Error: {e}")
            self.model = None
            self.tokenizer = None
            return False

    def _natural_to_bash_via_server(self, prompt: str) -> str | None:
        request_body = json.dumps({
            "prompt": (
                "Convert the following request into a single safe bash command. "
                f"Output only the command. Request: {prompt}"
            ),
            "max_tokens": 64,
            "temperature": 0.2,
        }).encode()
        request = urllib.request.Request(
            self.server_url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError):
            return None

        if "response" not in payload:
            return None
        return self._extract_command(payload["response"])
            
    def natural_to_bash(self, prompt: str) -> str:
        if not self.model:
            return self._natural_to_bash_via_server(prompt)
            
        system_prompt = """You are a bash command generator. 
Convert natural language to precise bash commands.
Only output the command, no explanation.
If dangerous, prefix with '# WARNING: '"""
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nCommand:"
        
        if hasattr(self.model, "create_chat_completion"):
            response = self.model.create_chat_completion(
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=64,
                temperature=0.3,
            )
            result = response["choices"][0]["message"]["content"]
        else:
            inputs = self.tokenizer(full_prompt, return_tensors="pt")
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=64,
                temperature=0.3,
                do_sample=True
            )
            result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return self._extract_command(result)
    
    def _extract_command(self, output: str) -> str:
        lines = output.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('Command') and not line.startswith('```'):
                return line
        return None
        
    def execute(self, command: str, confirm: bool = True) -> tuple:
        if confirm:
            print(f"\n[DRY RUN] Would execute: {command}")
            response = input("Execute? (y/n): ")
            if response.lower() != 'y':
                return False, "Cancelled by user"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def run(self):
        self.load_model()
        print("\n=== PhantomTerminal v0.1 ===")
        print("Type 'exit' to quit, 'help' for commands\n")
        
        while True:
            try:
                prompt = input("phantom@os~$ ").strip()
                if not prompt:
                    continue
                    
                if prompt.lower() in ['exit', 'quit']:
                    break
                if prompt.lower() == 'help':
                    print("Commands: exit, help, clear, history")
                    continue
                if prompt.lower() == 'clear':
                    os.system('clear')
                    continue
                    
                command = self.natural_to_bash(prompt)
                if not command:
                    print("Could not generate command")
                    continue
                    
                print(f"\nGenerated: {command}")
                success, output = self.execute(command)
                print(output)
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                break

if __name__ == "__main__":
    terminal = PhantomTerminal()
    terminal.run()
