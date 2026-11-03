# Auditoria C:\CloneZIP — 2026-11-02

## Resultado executivo

- Foram encontrados 10 arquivos compactados e um ficheiro de diagnóstico `bash.exe.stackdump`.
- O ZIP `awesome-free-llm-apis-main.zip` **não contém centenas de API keys**. Contém um catálogo/documentação com 16 fornecedores, endpoints, modelos e ligações para cada utilizador criar a sua própria chave.
- Não foram importadas credenciais de terceiros, não foram usados tokens de teste e não foram impressas chaves.
- Foram integrados no DGM-HUB dois endpoints anónimos sem API key: **Kilo Gateway** e **LLM7**. Ambos ficam opcionais; o funcionamento do Hub não depende deles.
- Nenhum ZIP foi executado ou instalado. A análise foi feita diretamente aos metadados e READMEs dentro dos arquivos.

## APIs — catálogo e configuração

Fonte: `awesome-free-llm-apis-main.zip`, `data.json`, data de atualização indicada no próprio ficheiro: 2026-10-05.

16 fornecedores catalogados:
- APIs dos próprios fornecedores: Aion Labs, Cohere, Google Gemini, Mistral AI, Z AI.
- Gateways/inference: Cloudflare Workers AI, Groq, Hugging Face, Kilo Code, LLM7.io, ModelScope, NVIDIA NIM, Ollama Cloud, OpenRouter, OVHcloud AI Endpoints, SiliconFlow.

### Integrados e testados no Hub

| Provider | Endpoint | Acesso | Modelo configurado | Resultado |
|---|---|---|---|---|
| Kilo | `https://api.kilo.ai/api/gateway` | Anónimo, sem chave, modelo gratuito | `openrouter/free` | E2E OK; o router selecionou `nvidia/nemotron-3.5-super-vl:free` |
| LLM7 | `https://api.llm7.io/v1` | Anónimo, sem chave | `gpt-oss:20b` | E2E OK |

Teste real enviado através de `POST /api/chat` do DGM-HUB:
- Pedido: responder com `API_HUB_OK | 19 x 23 = 437`.
- Kilo: resposta correta, estado `ok`, 5,73 s.
- LLM7: resposta correta, estado `ok`, 3,61 s.
- Nenhum cabeçalho Authorization ou API key foi enviado.
- Os providers estão disponíveis no cockpit e podem ser ligados/desligados individualmente.
- Ambos permanecem opcionais. Codex, Claude e DGM-MAT continuam independentes.
- Kilo usa um router de modelos gratuitos; modelo concreto, disponibilidade e limites podem variar. O parâmetro `reasoning_effort=low` foi usado para favorecer a resposta final visível.
- LLM7 anónimo respondeu com `gpt-oss:20b`; modelos premium listados no endpoint não foram selecionados.

### Não integrados nesta fase

- **OVHcloud AI Endpoints**: o endpoint anónimo respondeu, mas os modelos com preço zero que foram identificados são sobretudo safety, Whisper/transcrição, TTS e imagem; os modelos de chat gerais consultados apresentavam preço diferente de zero. Não foi configurado como provider de chat para evitar custos.
- **Groq, Cohere, Mistral, Gemini, Aion, Z AI, Cloudflare, Hugging Face, ModelScope, NVIDIA NIM, Ollama Cloud, OpenRouter, SiliconFlow**: exigem chave, conta, créditos, verificação ou condições específicas. O ZIP só fornece links e instruções; não cria chaves. Podem ser adicionados mais tarde com chaves criadas pelo André e guardadas localmente.
- O catálogo assinala condições de privacidade/treino para alguns tiers gratuitos e limitações regionais. É necessário rever as condições atuais de cada fornecedor antes de enviar dados pessoais ou confidenciais.

## Outros arquivos — avaliação

| Arquivo | O que é | Decisão |
|---|---|---|
| `moli-x86_64-pc-windows-msvc.zip` | Moli Browser: browser headless para agentes, com CLI, CDP e WebDriver; binário Windows incluído | **Candidato útil** para futura automação web/DGM-MAT e alternativa a ferramentas de browser. Não executar ainda: falta validar assinatura, origem do binário, permissões e isolamento. |
| `prime-agent-0.10.0.zip` | Agente de coding/research com subagentes, daemon, memória e melhoria contínua do harness | **Estudar conceitos**, não instalar. Sobrepõe-se ao objetivo central do DGM-MAT e pode criar dois cérebros/orquestradores. |
| `the-delegation-0.2.0.zip` | Simulador 3D de escritório multiagente, editor de equipas e fluxos PR/review | **Referência visual/UX muito relevante** para o futuro escritório virtual. Requer Gemini BYOK e stack WebGPU/Three.js; não instalar no PC atual nem substituir o DGM-HUB. |
| `hypit-0.3.1.zip` | Ferramenta/linguagem para agentes criarem vídeos com workflows, captions, B-roll e efeitos | **Útil futuramente** para um departamento de vídeo/conteúdo. Requer Node 22.15+, ferramentas/modelos e serviços de geração; não é prioridade do cockpit. |
| `deepbeepmeep_Wan2GP-main.zip` | Interface de geração de vídeo/imagem/áudio com modelos diffusion | **Não instalar no PC atual**: requer GPU/VRAM; README refere mínimo de 6 GB de VRAM para alguns modelos. |
| `Fooocus-2.5.5.zip` | Interface de geração de imagens SDXL | **Não instalar agora**: requer GPU NVIDIA com pelo menos 4 GB VRAM segundo o README; o PC atual é demasiado limitado para ser uma dependência fiável. |
| `open-webui-0.12.3.zip` | Plataforma self-hosted de chat/modelos, canais, agentes, memória, ferramentas e MCP | **Não instalar**: sobrepõe-se ao DGM-HUB e acrescenta uma stack pesada. O código pode servir de referência pontual. |
| `langchain-langchain-core-1.6.12.zip` | Biblioteca/framework Python para aplicações e agentes LLM | **Não instalar como aplicação**. Usar apenas integrações específicas se surgir uma necessidade concreta no DGM-MAT. |
| `ds-bot-0.1.7.tgz` | Plugin para DeepSeek Harness: bots persistentes, grupos, memória, browser e permissões | **Não instalar**: depende do DeepSeek Harness, que não é a nossa plataforma. Algumas ideias de permissões/memória podem ser estudadas. |
| `bash.exe.stackdump` | Dump de crash do Git Bash | **Diagnóstico antigo**, não é software nem API. Preservar até confirmar se já foi analisado; não é necessário para o Hub. |

## Alterações efetuadas no DGM-HUB

- `run_multichat.py`: providers Kilo e LLM7, ativação/desativação individual, verificação dos endpoints `/models`, chamadas OpenAI-compatible sem chave e tratamento de respostas vazias.
- `multichat.html`: dois cartões novos no cockpit e aviso para não enviar dados confidenciais a gateways externos.
- Estado persistido em `runtime/multichat/providers.json`.
- Backups: `run_multichat.py.bak-20261102-free-providers` e `multichat.html.bak-20261102-free-providers`.

## Segurança e limites

- Os dois gateways recebem o texto enviado pelo utilizador. Não enviar segredos, passwords, tokens, dados pessoais ou código privado sem avaliar primeiro os termos do fornecedor.
- Os modelos gratuitos podem mudar, ficar indisponíveis, limitar pedidos ou devolver respostas inconsistentes. O DGM-HUB não os usa como dependência obrigatória.
- Nenhum serviço pago foi ativado intencionalmente.
- Ollama continua desligado.
- Não houve instalação dos restantes ZIPs, nem commits, push ou merge.

## Validação técnica

- `python -m py_compile run_multichat.py`: passou após integração.
- E2E via Hub: Kilo e LLM7 responderam corretamente e concluíram a tarefa.
- Hub continua limitado a `127.0.0.1:8770`.
