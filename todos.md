Watcher app/daemon that:
- allows to register source repo and destination folder to write docs (via cli)
- runs ai agent after each commit, generating patches for docs based on diff
- some configs, system prompt
- can run on windows, linux, macos (leverage python and assume ollama already running for model serving)

Server Features:
[] database for metadata (such as *src* -> *docs* repo mapping; "chats" with agent (context management, input/output))
[] built-in MCP for context management described above (dependency module with std AND http I/O)
[] (http & cli) endpoints for state view and control (like get *docs* diff for last *src* commit)
