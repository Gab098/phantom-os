# AI Layer - PhantomOS

## Components

### LLM Server (`llm_server.py`)
REST API per il modello locale Qwen3.5-0.8B.  
Usage: `python3 llm_server.py [model_path] [port]`

### Terminal (`phantom_terminal.py`)
Interfaccia CLI che converte linguaggio naturale in comandi bash.

### NLP (`locale_manager.py`)
Gestione multilingua per il terminale AI.

## Setup

```bash
# Usa il modello incluso nel repository oppure un percorso personalizzato
python3 llm_server.py ../Qwen3.5-0.8B-BF16.gguf

# Validazione progetto
cd ..
make validate
make dev-setup
make smoke
```

## API

```json
POST http://localhost:8080
{
  "prompt": "mostra i processi in esecuzione",
  "max_tokens": 64,
  "temperature": 0.7
}
```

```json
GET http://localhost:8080/health
{
  "ready": true,
  "model_path": "/path/to/model.gguf",
  "port": 8080
}
```

## Benchmark

- Qwen3.5-0.8B: ~3s/token su CPU
- Phi-3-mini: ~4s/token su CPU
- TinyLlama: ~2s/token ma qualità inferiore
