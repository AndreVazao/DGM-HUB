# Arranque local do DGM-HUB

Usa `Start-DGM-HUB.cmd` na raiz do repositório. O launcher:

1. Verifica o DGM-MAT local em `127.0.0.1:8181/health`.
2. Se necessário, inicia o executável instalado `installed/DGM-MAT.exe`; usa `main.py` apenas como fallback de desenvolvimento.
3. Verifica a liveness do Hub em `127.0.0.1:8771/api/health/live` (ou `DGM_HUB_PORT` se definido).
4. Só inicia um servidor novo se a porta estiver livre; não cria uma segunda instância quando a porta está ocupada.
5. Abre o cockpit no browser.

Segurança operacional:
- Ambos os serviços ficam limitados a loopback (`127.0.0.1`).
- Não inicia Ollama nem FCC automaticamente; continuam controlados pelos botões do Hub.
- Não termina processos nem substitui instalações existentes.
- Não instala dependências automaticamente.
- Os logs de arranque ficam em `runtime/multichat/logs`.
- O endpoint de liveness não consulta fornecedores externos; a disponibilidade de cada fornecedor é apresentada separadamente no cockpit.

Configuração opcional:
- `DGM_MAT_ROOT`: caminho da instalação DGM-MAT.
- `DGM_PYTHON_EXECUTABLE`: caminho do Python com FastAPI e Uvicorn.
- `DGM_HUB_PORT`: porta loopback do Hub; por omissão, 8771.
