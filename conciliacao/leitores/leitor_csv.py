import pandas as pd  # biblioteca para trabalhar com tabelas de dados


def ler_extrato_csv(caminho):
    """
    Lê um arquivo CSV de extrato bancário e retorna uma tabela padronizada.

    Parâmetro:
        caminho: caminho do arquivo CSV (ex: 'dados/extrato.csv')

    Retorna:
        Um DataFrame com colunas: data, descricao, valor
    """

    # ---------------------------------------------------------
    # PASSO 1 — Ler o arquivo CSV
    # ---------------------------------------------------------
    # sep=';' porque bancos brasileiros usam ponto e vírgula como separador
    # encoding='utf-8' para aceitar acentos (ã, ç, é...)
    # skiprows=0 — muda para 1, 2... se o banco tiver linhas de cabeçalho no topo
    try:
        df = pd.read_csv(caminho, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        # alguns bancos usam encoding diferente, tentamos latin-1
        df = pd.read_csv(caminho, sep=';', encoding='latin-1')

    # ---------------------------------------------------------
    # PASSO 2 — Ver o que veio (útil para debug)
    # ---------------------------------------------------------
    print("Colunas encontradas no arquivo:")
    print(df.columns.tolist())
    print("\nPrimeiras 3 linhas:")
    print(df.head(3))

    # ---------------------------------------------------------
    # PASSO 3 — Padronizar os nomes das colunas
    # ---------------------------------------------------------
    # Cada banco usa nomes diferentes: "Data", "DT_LANC", "date"...
    # Renomeamos tudo para: data, descricao, valor
    # ATENÇÃO: ajuste os nomes abaixo conforme o seu banco!

    df = df.rename(columns={
        df.columns[0]: 'data',       # primeira coluna  → data
        df.columns[1]: 'descricao',  # segunda coluna   → descrição
        df.columns[2]: 'valor'       # terceira coluna  → valor
    })

    # ---------------------------------------------------------
    # PASSO 4 — Tratar a coluna de DATA
    # ---------------------------------------------------------
    # Converte texto para data de verdade
    # dayfirst=True porque no Brasil a data vem DD/MM/AAAA
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')

    # Remove linhas onde a data não foi reconhecida
    linhas_invalidas = df['data'].isna().sum()
    if linhas_invalidas > 0:
        print(f"\nAtenção: {linhas_invalidas} linha(s) com data inválida foram removidas.")
    df = df.dropna(subset=['data'])

    # ---------------------------------------------------------
    # PASSO 5 — Tratar a coluna de VALOR
    # ---------------------------------------------------------
    # Bancos brasileiros usam vírgula como decimal: 1.500,75
    # Python precisa do ponto: 1500.75
    # Então removemos os pontos de milhar e trocamos a vírgula por ponto

    df['valor'] = (
        df['valor']
        .astype(str)              # garante que é texto
        .str.strip()              # remove espaços em branco
        .str.replace('.', '', regex=False)   # remove ponto de milhar
        .str.replace(',', '.', regex=False)  # troca vírgula decimal por ponto
        .str.replace('R$', '', regex=False)  # remove símbolo do real se houver
        .str.strip()              # limpa espaços que sobraram
    )

    # Converte para número de verdade (float)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

    # Remove linhas onde o valor não foi reconhecido
    linhas_sem_valor = df['valor'].isna().sum()
    if linhas_sem_valor > 0:
        print(f"Atenção: {linhas_sem_valor} linha(s) com valor inválido foram removidas.")
    df = df.dropna(subset=['valor'])

    # ---------------------------------------------------------
    # PASSO 6 — Tratar a coluna de DESCRIÇÃO
    # ---------------------------------------------------------
    df['descricao'] = (
        df['descricao']
        .astype(str)
        .str.strip()       # remove espaços extras
        .str.upper()       # deixa tudo maiúsculo para comparações mais fáceis
    )

    # ---------------------------------------------------------
    # PASSO 7 — Manter só as colunas que precisamos
    # ---------------------------------------------------------
    df = df[['data', 'descricao', 'valor']]

    # ---------------------------------------------------------
    # PASSO 8 — Ordenar por data
    # ---------------------------------------------------------
    df = df.sort_values('data').reset_index(drop=True)

    # ---------------------------------------------------------
    # RESULTADO FINAL
    # ---------------------------------------------------------
    print(f"\nExtrato carregado com sucesso: {len(df)} transações encontradas.")
    print(f"Período: {df['data'].min().date()} até {df['data'].max().date()}")
    print(f"Total créditos: R$ {df[df['valor'] > 0]['valor'].sum():,.2f}")
    print(f"Total débitos:  R$ {df[df['valor'] < 0]['valor'].sum():,.2f}")

    return df


# ---------------------------------------------------------
# TESTE — roda isso direto pra ver se está funcionando
# ---------------------------------------------------------
if __name__ == '__main__':
    # Cria um CSV de exemplo para testar sem precisar do banco
    exemplo = """data;descricao;valor
01/03/2026;SALARIO;5.000,00
02/03/2026;SUPERMERCADO;-350,75
05/03/2026;CONTA DE LUZ;-189,90
10/03/2026;TRANSFERENCIA RECEBIDA;1.200,00
15/03/2026;FARMACIA;-87,50
20/03/2026;ALUGUEL;-1.500,00"""

    # Salva o exemplo na pasta dados
    with open('dados/extrato_teste.csv', 'w', encoding='utf-8') as f:
        f.write(exemplo)

    print("=== Testando leitor_csv.py ===\n")
    tabela = ler_extrato_csv('dados/extrato_teste.csv')

    print("\n=== Tabela final ===")
    print(tabela.to_string(index=False))