#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phantom_env import load_system_config, resolve_model_path


class LLMService:
    def __init__(self, model_path=None, port=8080):
        config = load_system_config()
        self.model_path = resolve_model_path(model_path)
        self.port = port
        if config.get("ai", {}).get("server_port") and port == 8080:
            self.port = int(config["ai"]["server_port"])
        self.model = None
        self.tokenizer = None
        self.ready = False
        
    def load_model(self):
        print(f"Loading LLM from {self.model_path}...")

        candidate = Path(self.model_path).expanduser()
        if candidate.is_file() and candidate.suffix == ".gguf":
            self.model_path = candidate
            print(f"Found GGUF model: {self.model_path}")
            return self._load_llama_cpp()

        gguf_files = sorted(candidate.glob("*.gguf")) if candidate.is_dir() else []
        if gguf_files:
            self.model_path = gguf_files[0]
            print(f"Found GGUF model: {self.model_path}")
            return self._load_llama_cpp()

        hf_path = candidate / "model.safetensors"
        if hf_path.exists():
            self.model_path = candidate
            return self._load_huggingface()

        print(f"No supported model found at {candidate}")
        return False
        
    def _load_llama_cpp(self):
        try:
            from llama_cpp import Llama
            
            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
            self.ready = True
            print("GGUF model loaded via llama.cpp!")
            return True
        except ImportError:
            print("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            print(f"Failed to load GGUF: {e}")
            return False
            
    def _load_huggingface(self):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            print("Loading HuggingFace model...")
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForCausalLM.from_pretrained(
                str(self.model_path),
                device_map="cpu",
                torch_dtype="float32"
            )
            self.ready = True
            print("HuggingFace model loaded!")
            return True
        except Exception as e:
            print(f"Failed to load HF model: {e}")
            return False
            
    def generate(self, prompt, max_tokens=128, temp=0.7):
        if not self.ready:
            return {"error": "Model not loaded"}
            
        try:
            if hasattr(self.model, 'create_chat_completion'):
                response = self.model.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temp
                )
                return {"response": response['choices'][0]['message']['content']}
            else:
                inputs = self.tokenizer(prompt, return_tensors="pt")
                outputs = self.model.generate(**inputs, max_new_tokens=max_tokens, temperature=temp)
                result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                return {"response": result}
        except Exception as e:
            return {"error": str(e)}
        
    def natural_to_bash(self, text):
        system_prompt = """Tu sei un assistente che converte comandi in linguaggio naturale in comandi bash precisi.
Rispondi SOLO con il comando bash, niente spiegazioni.
Se il comando potrebbe essere pericoloso, aggiungi '#' prima."""
        
        prompt = f"{system_prompt}\n\nConversione: \"{text}\"\nComando:"
        result = self.generate(prompt, max_tokens=64, temp=0.3)
        
        if "response" in result:
            lines = result["response"].split("\n")
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith("Conversione") and not line.startswith("Tu"):
                    if line.startswith("#"):
                        line = line[1:].strip()
                    return line
        return None
        
    def start_server(self):
        if not self.ready:
            print("Cannot start server: model not loaded")
            return
            
        from http.server import HTTPServer, BaseHTTPRequestHandler
        
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path != "/health":
                    self.send_response(404)
                    self.end_headers()
                    return

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                payload = {
                    "ready": self.service.ready,
                    "model_path": str(self.service.model_path),
                    "port": self.service.port,
                }
                self.wfile.write(json.dumps(payload).encode())

            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body)
                    result = self.service.generate(
                        data.get("prompt", ""),
                        data.get("max_tokens", 128),
                        data.get("temperature", 0.7)
                    )
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
                    
            def log_message(self, format, *args):
                pass
                
        Handler.service = self
        
        server = HTTPServer(("127.0.0.1", self.port), Handler)
        print(f"LLM server running on http://127.0.0.1:{self.port}")
        server.serve_forever()

if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else None
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    
    service = LLMService(model_path, port)
    service.load_model()
    service.start_server()
