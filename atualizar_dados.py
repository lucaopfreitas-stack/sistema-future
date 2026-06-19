#!/usr/bin/env python3
"""
Atualiza estoque e situação dos produtos Future via API do Tiny.
Preserva todos os preços (custo, pvenda, pabc) — nunca sobrescreve.
Salva snapshot diário no Supabase para tracking de vendas.
"""
import urllib.request, urllib.parse, json, time, subprocess, sys, os
from datetime import datetime

SUPA_URL = 'https://bdmwvujqldwgeuwfpqaf.supabase.co'
SUPA_KEY = os.environ.get('SUPABASE_SVC_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJkbXd2dWpxbGR3Z2V1d2ZwcWFmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MTgwNTI1NywiZXhwIjoyMDk3MzgxMjU3fQ.8M40M0aqse0PazAUPPsRpDAwjSZ-raUBJBDlGPWm_EI')

PASTA  = os.path.dirname(os.path.abspath(__file__))
BASE   = os.path.join(PASTA, 'base_produtos.json')
BUILD  = '/tmp/build_dashboard.py'
TOKEN  = os.environ.get('TINY_TOKEN', 'd8a8a4fc6a4780024ee22abc81a7bddcd3d51e6eadb80018f6a64ec8fb2be9da')
API    = 'https://api.tiny.com.br/api2/'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}')
    sys.stdout.flush()

def tiny_post(endpoint, params, retries=3):
    params = {**params, 'token': TOKEN, 'formato': 'JSON'}
    data   = urllib.parse.urlencode(params).encode()
    for tentativa in range(retries):
        try:
            req = urllib.request.Request(API + endpoint, data=data)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except Exception as e:
            if tentativa < retries - 1:
                time.sleep(2 ** tentativa)
            else:
                raise e

def buscar_produtos_tiny():
    """Busca todas as páginas de produtos Future."""
    todos = {}
    pagina = 1
    while True:
        resp  = tiny_post('produtos.pesquisa.php', {'pesquisa': 'Future', 'pagina': pagina})
        ret   = resp.get('retorno', {})
        if ret.get('status') != 'OK':
            break
        prods = ret.get('produtos', [])
        if not prods:
            break
        for item in prods:
            p    = item['produto']
            nome = p.get('nome', '')
            if 'Future' not in nome:  # ignora produtos sem "Future" no nome (ex: 1677-N)
                continue
            sku = str(p.get('codigo', '')).strip()
            if not sku or '-' in sku:
                continue
            try:
                sku = str(int(float(sku)))
            except:
                continue
            todos[sku] = {
                'id_tiny':  str(p['id']),
                'nome':     nome,
                'situacao': p.get('situacao', 'A'),
            }
        n_pags = int(ret.get('numero_paginas', 1))
        log(f'  Página {pagina}/{n_pags} — {len(prods)} produtos')
        if pagina >= n_pags:
            break
        pagina += 1
        time.sleep(0.3)
    return todos

def buscar_estoque(id_tiny):
    """Retorna saldo de estoque. Retorna None em erro (não sobrescreve valor anterior)."""
    for tentativa in range(3):
        try:
            resp = tiny_post('produto.obter.estoque.php', {'id': id_tiny})
            ret  = resp.get('retorno', {})
            # se a API retornou erro (rate limit, etc.), aguarda e tenta de novo
            if ret.get('status') == 'Erro':
                time.sleep(2 ** tentativa * 2)
                continue
            prod = resp.get('produto') or ret.get('produto', {})
            if not prod:
                time.sleep(1)
                continue
            return int(float(str(prod.get('saldo', 0))))
        except Exception as e:
            if tentativa < 2:
                time.sleep(2)
    return None

def main():
    log('=== Iniciando atualização de estoque ===')

    # Carregar base atual
    with open(BASE, encoding='utf-8') as f:
        base = json.load(f)

    log(f'Base carregada: {len(base["produtos"])} produtos')

    # Buscar produtos do Tiny
    log('Buscando produtos no Tiny...')
    tiny = buscar_produtos_tiny()
    log(f'Tiny retornou {len(tiny)} SKUs Future')

    # Atualizar estoque para cada produto da base
    atualizados = 0
    erros       = 0
    for sku, p in base['produtos'].items():
        if sku not in tiny:
            continue
        id_tiny = tiny[sku]['id_tiny']
        est     = buscar_estoque(id_tiny)
        if est is None:
            erros += 1
            continue
        p['est']      = est
        p['situacao'] = tiny[sku]['situacao']
        atualizados  += 1
        time.sleep(0.4)  # respeitar rate limit Tiny

    log(f'Estoque atualizado: {atualizados} produtos | Erros: {erros}')

    # Salvar base preservando preços
    base['gerado_em']        = datetime.now().isoformat()
    base['total_produtos']   = len(base['produtos'])
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(base, f, ensure_ascii=False, indent=2)
    log('base_produtos.json salvo')

    # Regenerar dashboard
    if os.path.exists(BUILD):
        log('Gerando dashboard...')
        subprocess.run([sys.executable, BUILD], check=True)
        log('Dashboard atualizado ✓')
    else:
        log(f'AVISO: build_dashboard.py não encontrado em {BUILD}')

    # Salvar snapshot no Supabase para tracking de vendas
    try:
        from supabase import create_client
        sb = create_client(SUPA_URL, SUPA_KEY)
        snapshots = {sku: p.get('est', 0) for sku, p in base['produtos'].items()}
        data_hoje = datetime.now().strftime('%Y-%m-%d')
        sb.table('estoque_historico').upsert(
            {'data': data_hoje, 'snapshots': snapshots},
            on_conflict='data'
        ).execute()
        log(f'Snapshot salvo no Supabase ({len(snapshots)} SKUs) ✓')
    except Exception as e:
        log(f'AVISO: Falha ao salvar snapshot Supabase: {e}')

    log('=== Atualização concluída ===')

if __name__ == '__main__':
    main()
