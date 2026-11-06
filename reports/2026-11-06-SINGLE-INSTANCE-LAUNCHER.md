# DGM-HUB — proteção contra instâncias duplicadas (2026-11-06)

O launcher canónico `scripts/Start-DGM-HUB.ps1` é agora o único ponto de arranque do Hub.

- Um mutex por porta serializa chamadas concorrentes do launcher.
- Antes de arrancar DGM-MAT, o launcher procura processos `DGM-MAT.exe --headless` e `python main.py --headless` do repositório configurado. Se encontrar um, aguarda o health check e recusa criar outro processo se não ficar saudável.
- A proteção de porta existente continua a impedir que outro processo seja iniciado quando 8181 ou a porta do Hub já tem um listener sem health válido.
- O launcher legado `Start-DGM-HUB-MultiChat.ps1` delega agora no launcher canónico, em vez de iniciar o seu próprio Uvicorn.
- Ollama e FCC continuam fora do arranque automático.

Validação prevista: parser PowerShell sem erros e `tests/test_launcher_contract.py`.
