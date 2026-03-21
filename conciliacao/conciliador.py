import pandas as pd  # biblioteca para trabalhar com tabelas


def conciliar(extrato_banco, lancamentos_internos):
    """
    Compara o extrato do banco com os lançamentos internos e classifica
    cada transação em 3 categorias:

        ✅ Conciliado     — aparece nos dois lados (banco + interno)
        ⚠️  Só no banco   — está no extrato mas não foi lançado internamente
        ❌  Só no interno — foi lançado internamente mas não aparece no banco

    Parâmetros:
        extrato_banco       : DataFrame retornado pelo leitor_csv ou leitor_ofx
        lancamentos_internos: DataFrame com os lançamentos do seu sistema

    Retorna:
        Um dicionário com 3 DataFrames:
            'conciliados'   → transações que batem nos dois lados
            'so_no_banco'   → transações só no banco
            'so_no_interno' → transações só no interno
    """

    # ---------------------------------------------------------
    # PASSO 1 — Garantir que as colunas estão no formato certo
    # ---------------------------------------------------------
    # Antes de comparar, precisamos garantir que data e valor
    # estão exatamente no mesmo formato nos dois DataFrames.
    # Se um está com hora e outro sem hora, o merge não vai casar.

    extrato_banco = extrato_banco.copy()
    lancamentos_internos = lancamentos_internos.copy()

    # Converte datas para o mesmo formato (só a data, sem hora)
    extrato_banco['data'] = pd.to_datetime(
        extrato_banco['data']
    ).dt.normalize()

    lancamentos_internos['data'] = pd.to_datetime(
        lancamentos_internos['data']
    ).dt.normalize()

    # Arredonda valores para 2 casas decimais para evitar
    # diferenças como 100.999999 vs 101.00 quebrarem o match
    extrato_banco['valor'] = extrato_banco['valor'].round(2)
    lancamentos_internos['valor'] = lancamentos_internos['valor'].round(2)

    # Deixa descrição em maiúsculo nos dois lados
    extrato_banco['descricao'] = extrato_banco['descricao'].str.upper().str.strip()
    lancamentos_internos['descricao'] = lancamentos_internos['descricao'].str.upper().str.strip()

    print("=== Iniciando conciliação ===")
    print(f"Transações no banco:    {len(extrato_banco)}")
    print(f"Lançamentos internos:   {len(lancamentos_internos)}")

    # ---------------------------------------------------------
    # PASSO 2 — O merge (cruzamento das tabelas)
    # ---------------------------------------------------------
    # Aqui está o coração do sistema.
    #
    # pd.merge() cruza duas tabelas buscando linhas que combinam.
    # Usamos how='outer' para pegar TODAS as linhas dos dois lados,
    # mesmo as que não têm par.
    #
    # on=['data', 'valor'] significa: considere uma transação igual
    # se ela tiver a mesma data E o mesmo valor.
    #
    # indicator=True adiciona uma coluna '_merge' que diz de onde
    # veio cada linha:
    #   'both'       → estava nos dois lados (conciliado)
    #   'left_only'  → só no banco (extrato_banco é o "left")
    #   'right_only' → só no interno (lancamentos_internos é o "right")

    merged = pd.merge(
        extrato_banco,           # tabela da esquerda (left)
        lancamentos_internos,    # tabela da direita (right)
        on=['data', 'valor'],    # colunas usadas para casar as linhas
        how='outer',             # pega todos os registros dos dois lados
        suffixes=('_banco', '_interno'),  # renomeia colunas duplicadas
        indicator=True           # adiciona coluna _merge com a origem
    )

    # ---------------------------------------------------------
    # PASSO 3 — Separar os 3 grupos
    # ---------------------------------------------------------

    # ✅ Conciliados — aparecem nos dois lados
    conciliados = merged[
        merged['_merge'] == 'both'
    ].copy()

    # ⚠️ Só no banco — não foram lançados internamente
    so_no_banco = merged[
        merged['_merge'] == 'left_only'
    ].copy()

    # ❌ Só no interno — não aparecem no extrato do banco
    so_no_interno = merged[
        merged['_merge'] == 'right_only'
    ].copy()

    # ---------------------------------------------------------
    # PASSO 4 — Limpar as tabelas resultantes
    # ---------------------------------------------------------
    # Remove a coluna _merge (não precisamos mais dela)
    # e organiza as colunas de forma legível

    conciliados = conciliados.drop(columns=['_merge'])
    so_no_banco = so_no_banco.drop(columns=['_merge'])
    so_no_interno = so_no_interno.drop(columns=['_merge'])

    # Ordena tudo por data
    conciliados   = conciliados.sort_values('data').reset_index(drop=True)
    so_no_banco   = so_no_banco.sort_values('data').reset_index(drop=True)
    so_no_interno = so_no_interno.sort_values('data').reset_index(drop=True)

    # ---------------------------------------------------------
    # PASSO 5 — Resumo da conciliação
    # ---------------------------------------------------------
    total = len(extrato_banco)
    pct_conciliado = (len(conciliados) / total * 100) if total > 0 else 0

    print("\n=== Resultado da conciliação ===")
    print(f"✅ Conciliados:      {len(conciliados)} transações")
    print(f"⚠️  Só no banco:     {len(so_no_banco)} transações")
    print(f"❌ Só no interno:    {len(so_no_interno)} transações")
    print(f"\nTaxa de conciliação: {pct_conciliado:.1f}%")

    if len(so_no_banco) > 0:
        print(f"\nValor não lançado internamente: R$ {so_no_banco['valor'].sum():,.2f}")
    if len(so_no_interno) > 0:
        print(f"Valor não confirmado no banco:  R$ {so_no_interno['valor'].sum():,.2f}")

    # ---------------------------------------------------------
    # PASSO 6 — Retornar os 3 grupos num dicionário
    # ---------------------------------------------------------
    return {
        'conciliados':   conciliados,
        'so_no_banco':   so_no_banco,
        'so_no_interno': so_no_interno
    }


# ---------------------------------------------------------
# TESTE — simula extrato do banco vs lançamentos internos
# ---------------------------------------------------------
if __name__ == '__main__':

    # Simula o extrato que veio do banco
    extrato_banco = pd.DataFrame([
        {'data': '2026-03-01', 'descricao': 'SALARIO',                 'valor':  5000.00},
        {'data': '2026-03-02', 'descricao': 'SUPERMERCADO',            'valor':  -350.75},
        {'data': '2026-03-05', 'descricao': 'CONTA DE LUZ',            'valor':  -189.90},
        {'data': '2026-03-10', 'descricao': 'TRANSFERENCIA RECEBIDA',  'valor':  1200.00},
        {'data': '2026-03-15', 'descricao': 'FARMACIA',                'valor':   -87.50},
        # essa transação está só no banco (não foi lançada internamente)
        {'data': '2026-03-18', 'descricao': 'TAXA BANCARIA',           'valor':   -25.00},
    ])

    # Simula os lançamentos internos (feitos no seu sistema)
    lancamentos_internos = pd.DataFrame([
        {'data': '2026-03-01', 'descricao': 'SALARIO',                 'valor':  5000.00},
        {'data': '2026-03-02', 'descricao': 'SUPERMERCADO',            'valor':  -350.75},
        {'data': '2026-03-05', 'descricao': 'CONTA DE LUZ',            'valor':  -189.90},
        {'data': '2026-03-10', 'descricao': 'TRANSFERENCIA RECEBIDA',  'valor':  1200.00},
        {'data': '2026-03-15', 'descricao': 'FARMACIA',                'valor':   -87.50},
        # esse lançamento está só no interno (não aparece no banco)
        {'data': '2026-03-20', 'descricao': 'FORNECEDOR XYZ',          'valor':  -500.00},
    ])

    # Roda a conciliação
    resultado = conciliar(extrato_banco, lancamentos_internos)

    # Mostra os 3 grupos
    print("\n--- ✅ Conciliados ---")
    print(resultado['conciliados'].to_string(index=False))

    print("\n--- ⚠️  Só no banco ---")
    print(resultado['so_no_banco'].to_string(index=False))

    print("\n--- ❌ Só no interno ---")
    print(resultado['so_no_interno'].to_string(index=False))