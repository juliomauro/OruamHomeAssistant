# 1. Instalação

## 1.1 Container

Instalei pela loja de apps do ZimaOS (app "Home Assistant" da BigBearTechWorld). O compose equivalente, que também serve para Docker puro, está em [`config/compose.yaml`](../../config/compose.yaml):

```yaml
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    network_mode: host          # necessário para descoberta (Cast, mDNS, SSDP) e Bluetooth
    restart: unless-stopped
    cap_add: [NET_ADMIN, NET_RAW] # ping e scanner de rede
    environment:
      - TZ=America/Sao_Paulo
    volumes:
      - /DATA/AppData/homeassistant/config:/config
      - /etc/localtime:/etc/localtime:ro
      - /run/dbus:/run/dbus:ro
      - /media/4tb:/media/4tb:ro  # opcional: disco de mídia, só leitura
```

Pontos importantes:

- **`network_mode: host`** é obrigatório para o Cast, a descoberta de aparelhos e as integrações de ping.
- A porta é a **8123**.
- Os arquivos em `/config` pertencem ao root. Para editar, use `docker exec homeassistant ...` ou a interface.
- No ZimaOS, mudanças de volume são feitas pela interface do app. Se editar o compose na mão, o Zima sobrescreve.

```bash
docker compose -f config/compose.yaml up -d
docker logs -f homeassistant   # espere "Home Assistant initialized"
```

## 1.2 Primeiro acesso

1. Abra `http://IP_DO_SERVIDOR:8123`.
2. Crie o usuário dono (owner).
3. Escolha a localização da casa, que é usada pelo clima (`weather.casa`) e pelo nascer e pôr do sol.
4. Escolha a unidade (métrico) e a moeda (BRL).

## 1.3 Proxy reverso com Traefik (opcional)

Uso o Traefik com um certificado wildcard do Let's Encrypt para `*.example.com`, acessível só na LAN e pelo Tailscale. A rota fica no arquivo dinâmico do Traefik:

```yaml
http:
  routers:
    ha:
      rule: Host(`ha.example.com`)
      entryPoints: [websecure]
      service: ha
      tls: {}
  services:
    ha:
      loadBalancer:
        servers:
          - url: http://192.168.0.240:8123
```

O HA recusa conexões que chegam por proxy até você liberar o proxy. **No 2026.11 essa configuração mudou de lugar**:

- Ela agora fica em `.storage/http` e é editada pela interface: **Configurações > Sistema > Rede**, com "Usar X-Forwarded-For" ligado e o proxy confiável `172.17.0.0/16`, que é a rede Docker do Traefik.
- O bloco `http:` do `configuration.yaml` só é lido uma vez, na migração. Depois disso ele precisa **sair** do arquivo, senão aparece um reparo "ignored after migration".

Se a migração já rodou com valores errados, veja [Pegadinhas](10-pegadinhas.md#proxy-reverso-ignorado).

## 1.4 Marketplace (cards da comunidade)

No 2026.11 o HACS vem embutido, com o nome **Marketplace**. Não instale o HACS separado.

Instalei estes cards, que são usados nos painéis:

| Card | Uso |
|---|---|
| Mushroom (v5) | Cards de template, entidade e mídia |
| mini-graph-card | Gráficos compactos |
| card-mod | Ajustes de CSS (fontes grandes no tablet) |

Cada instalação pede para você aceitar na interface.

Integrações que não estão no Marketplace (Ex: `tplink_deco`) vão manualmente para `/config/custom_components/<nome>`, seguidas de um reinício do HA.

## 1.5 Backup

Em **Configurações > Sistema > Backups**:

- diário às 04:30, guardando 7 cópias;
- destinos: local + Google Drive (precisa da integração Google Drive, ver [Integrações](03-integracoes.md#google));
- criptografia ligada.

**Guarde a chave de criptografia no seu cofre de senhas.** Sem ela o backup não restaura.

Em instalação por container, o backup **não** aceita pastas extras nem add-ons. Se o assistente da interface marcar essas opções, o backup falha com "Addons and folders are not supported by core backup".

Atenção também: o assistente de backup sobrescreve destinos, horário e retenção. Depois de mexer nele, confira se as opções continuam como você quer.
