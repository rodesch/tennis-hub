# Onboarding: Tennis Hub - 2026-02-21

## Entendimento da Tarefa
Continuar desenvolvimento do Tennis Hub - site de informações de tênis com FastAPI backend + vanilla SPA frontend.

## Stack
- **Backend**: Python 3.12, FastAPI, httpx, SQLite cache, uvicorn
- **Frontend**: Vanilla JS SPA, no framework
- **API**: TennisApi1 via RapidAPI (free tier, aggressive caching)
- **Port**: 5004
- **Docker**: docker-compose.yml presente e configurado

## Arquivos Relevantes
- `app/main.py` - Endpoints FastAPI (rankings, results, calendar, h2h, draws, player, search)
- `app/tennis_client.py` - HTTP client com cache integrado
- `app/cache.py` - SQLite cache manager
- `app/config.py` - Config e TTLs
- `templates/index.html` - HTML da SPA (7 seções)
- `static/css/style.css` - Estilos completos
- `static/js/app.js` - Lógica frontend, fetch, render

## Estado Atual

### Completo
- Backend FastAPI com todos os 7 endpoints
- Cache SQLite funcional
- Estrutura HTML da SPA
- Renderers: Rankings (tabela), Results (match cards), Calendar (card grid), Player (profile), Search

### INCOMPLETO - JSON fallback
- `renderH2H()` - linha 205-208 app.js - mostra JSON bruto
- `renderDraws()` - linha 226-228 app.js - mostra JSON bruto

### MISSING
- `.env` com RAPIDAPI_KEY - serviço não consegue rodar
- Serviço não está rodando (testado: http://localhost:5004 falhou)
- Sem git history próprio (tennis-site não está commitado no repo pai)

## Riscos
- API shape desconhecido para H2H e Draws (TennisApi1 pode retornar diferentes formatos)
- Sem RAPIDAPI_KEY não podemos testar com dados reais
- Free tier tem limite de calls - cache é crítico

## OPEN: Qual é "o plano" referenciado pelo usuário?
Não encontrei documento de plano. Precisa confirmar com usuário.

## Próximos Passos Prováveis
1. Obter RAPIDAPI_KEY e criar .env
2. Implementar renderH2H() com UI adequada
3. Implementar renderDraws() com bracket visual
4. Testar serviço localmente
5. Deploy via docker-compose
6. Configurar no Caddy/Tailscale (padrão do dev setup)
