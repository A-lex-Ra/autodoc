# Autodoc

Autodoc is a daemon that watches your source code repositories and automatically updates documentation using AI.

## Setup

1.  **Prerequisites**:
    *   Python 3.10+
    *   [Ollama](https://ollama.com/) installed and running.
    *   Pull the default model: `ollama pull gpt-oss:20b`

2.  **Installation**:
    ```bash
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

3.  **Initialize Database**:
    ```bash
    python -m src.cli init-db
    ```

## Usage

### 1. Register a Repository
Register a source folder to watch and a destination folder for docs.
```bash
python -m src.cli register "\path\to\your\src" "\path\to\your\docs" --name "my-project"
```

### 2. Start the Watcher & Server
Run the daemon/server.
```bash
python src.cli serve
```
The server runs on `http://127.0.0.1:8000`.

### 3. Usage Flow
- Make changes in your source folder and commit them:
    ```bash
    git add .
    git commit -m "Added a new login feature"
    ```
- The watcher (checking every 60s) will detect the new commit.
- It will send the diff to Ollama.
- Ollama generates documentation updates.
- Autodoc applies these changes to your `docs` folder.

## Troubleshooting
- **Ollama Connection**: Ensure `ollama serve` is running.
