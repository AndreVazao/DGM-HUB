# Arranque local do DGM-HUB

Usa Start-DGM-HUB.cmd na raiz do repositório. O launcher:

1. Verifica o health local do DGM-MAT em 127.0.0.1:8181.
2. Se necessário, inicia o executável instalado installed/DGM-MAT.exe; usa main.py apenas como fallback de desenvolvimento.
3. Verifica 127.0.0.1:8770/api/health e inicia o servidor FastAPI do Hub apenas se a porta estiver livre.
4. Abre o cockpit no browser.

Segurança operacional:
- Ambos os serviços ficam limitados a loopback (127.0.0.1).
- Não inicia Ollama nem FCC automaticamente; continuam controlados pelos botões do Hub.
- Não termina processos nem substitui instalações existentes.
- Se uma porta estiver ocupada sem health saudável, o launcher recusa iniciar uma segunda instância.
- Os logs de arranque ficam em runtime/multichat/logs.
- Não instala dependências automaticamente. Se FastAPI/Uvicorn não estiverem instalados, apresenta um erro explícito.

Configuração opcional:
- DGM_MAT_ROOT: caminho da instalação DGM-MAT.
- DGM_PYTHON_EXECUTABLE: caminho do Python com FastAPI e Uvicorn.
