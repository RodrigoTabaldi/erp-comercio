import pdfplumber  # biblioteca que extrai texto e tabelas de PDFs
import pandas as pd
import re           # biblioteca para trabalhar com padrões de texto (regex)


# ---------------------------------------------------------
# COMO O PDFPLUMBER FUNCIONA
# ---------------------------------------------------------
# O pdfplumber abre o PDF e te dá acesso a:
#   - page.extract_text()  → todo o texto da página como string
#   - page.extract_table() → tenta detectar tabelas automaticamente
#   - page.extract_tables()→ todas as tabelas da página
#
# O desafio: você precisa identificar o padrão do banco
# e escrever regras para separar data, descrição e valor.
# ---------------------------------------------------------


def inspecionar_pdf(caminho):
    """
    PRIMEIRO PASSO SEMPRE: inspecionar o PDF antes de extrair.
    Mostra o texto bruto de cada página para você entender
    como o banco organiza as informações.

    Use essa função quando receber um PDF novo de um banco diferente.
    """
    print(f"=== Inspecionando: {caminho} ===\n")

    with pdfplumber.open(caminho) as pdf:
        print(f"Total de páginas: {len(pdf.pages)}\n")

        for i, page in enumerate(pdf.pages):
            print(f"--- Página {i + 1} ---")

            # Tenta extrair como tabela primeiro
            tabelas = page.extract_tables()
            if tabelas:
                print(f"  Tabelas encontradas: {len(tabelas)}")
                for j, tabela in enumerate(tabelas):
                    print(f"  Tabela {j + 1}:")
                    for linha in tabela[:5]:  # mostra só as 5 primeiras linhas
                        print(f"    {linha}")
            else:
                # Se não tem tabela, mostra o texto bruto
                texto = page.extract_text()
                if texto:
                    print(texto[:500])  # mostra os primeiros 500 caracteres

            print()


def ler_pdf_nubank(caminho):
    """
    Lê extrato PDF do Nubank (fatura do cartão de crédito).

    O Nubank organiza as transações assim no PDF:
        15 mar   Netflix                    R$ 45,90
        16 mar   Uber                      R$ 23,50
        17 mar   Supermercado              R$ 187,30

    Parâmetro:
        caminho: caminho do arquivo PDF

    Retorna:
        DataFrame com colunas: data, descricao, valor
    """
    print(f"📄 Lendo PDF Nubank: {caminho}")
    linhas_encontradas = []

    # Padrão do Nubank: DD MMM   DESCRIÇÃO   R$ VALOR
    # Exemplos que esse padrão captura:
    #   "15 mar   Netflix   R$ 45,90"
    #   "02 jan   UBER *VIAGEM   R$ 23,50"
    padrao = re.compile(
        r'(\d{2}\s+\w{3})'     # data: "15 mar"
        r'\s+'                  # espaços
        r'(.+?)'               # descrição (qualquer coisa)
        r'\s+'                  # espaços
        r'R\$\s*([\d,.]+)'     # valor: "R$ 45,90"
    )

    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue

            for linha in texto.split('\n'):
                match = padrao.search(linha)
                if match:
                    data_str, descricao, valor_str = match.groups()
                    linhas_encontradas.append({
                        'data_raw': data_str.strip(),
                        'descricao': descricao.strip(),
                        'valor_raw': valor_str.strip()
                    })

    if not linhas_encontradas:
        print("⚠️  Nenhuma transação encontrada. O layout do PDF pode ter mudado.")
        print("   Rode inspecionar_pdf() para ver o texto bruto e ajustar o padrão.")
        return pd.DataFrame(columns=['data', 'descricao', 'valor'])

    df = pd.DataFrame(linhas_encontradas)

    # Converte data: "15 mar" → adiciona o ano atual
    ano_atual = pd.Timestamp.now().year
    df['data'] = pd.to_datetime(
        df['data_raw'] + f' {ano_atual}',
        format='%d %b %Y',
        errors='coerce'
    )

    # Converte valor: "1.234,56" → 1234.56
    df['valor'] = (
        df['valor_raw']
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
        # No cartão de crédito, todos os gastos são negativos
        .multiply(-1)
    )

    df = df[['data', 'descricao', 'valor']].dropna()
    df['descricao'] = df['descricao'].str.upper().str.strip()
    df = df.sort_values('data').reset_index(drop=True)

    print(f"✅ {len(df)} transações encontradas.")
    return df


def ler_pdf_itau(caminho):
    """
    Lê extrato PDF do Itaú (conta corrente).

    O Itaú organiza as transações em tabela assim:
        | Data     | Histórico          | Valor      |
        | 01/03    | SALDO ANTERIOR     | 1.000,00   |
        | 02/03    | PIX ENVIADO        | -350,00    |
        | 05/03    | TED RECEBIDA       | 2.500,00   |

    Parâmetro:
        caminho: caminho do arquivo PDF

    Retorna:
        DataFrame com colunas: data, descricao, valor
    """
    print(f"📄 Lendo PDF Itaú: {caminho}")
    linhas_encontradas = []

    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:

            # O Itaú usa tabelas — tentamos extrair diretamente
            tabelas = page.extract_tables()

            for tabela in tabelas:
                for linha in tabela:
                    if not linha or len(linha) < 3:
                        continue

                    data_str  = linha[0]
                    descricao = linha[1]
                    valor_str = linha[-1]  # último campo é o valor

                    # Verifica se a data parece com DD/MM
                    if not data_str or not re.match(r'\d{2}/\d{2}', str(data_str)):
                        continue

                    # Ignora linha de cabeçalho
                    if 'data' in str(data_str).lower():
                        continue

                    linhas_encontradas.append({
                        'data_raw': str(data_str).strip(),
                        'descricao': str(descricao).strip() if descricao else '',
                        'valor_raw': str(valor_str).strip() if valor_str else ''
                    })

    if not linhas_encontradas:
        print("⚠️  Nenhuma transação encontrada. Tentando extração por texto...")
        return _ler_itau_por_texto(caminho)

    df = pd.DataFrame(linhas_encontradas)

    # Converte data: "02/03" → adiciona o ano atual
    ano_atual = pd.Timestamp.now().year
    df['data'] = pd.to_datetime(
        df['data_raw'] + f'/{ano_atual}',
        format='%d/%m/%Y',
        errors='coerce'
    )

    # Converte valor
    df['valor'] = (
        df['valor_raw']
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .str.replace(' ', '', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
    )

    df = df[['data', 'descricao', 'valor']].dropna()
    df['descricao'] = df['descricao'].str.upper().str.strip()
    df = df.sort_values('data').reset_index(drop=True)

    print(f"✅ {len(df)} transações encontradas.")
    return df


def _ler_itau_por_texto(caminho):
    """
    Alternativa: lê o Itaú via texto quando a extração de tabela falha.
    Padrão: DD/MM DESCRIÇÃO VALOR
    """
    linhas_encontradas = []
    padrao = re.compile(
        r'(\d{2}/\d{2})'     # data: "02/03"
        r'\s+'
        r'(.+?)'             # descrição
        r'\s+'
        r'(-?[\d.]+,\d{2})' # valor: "1.500,00" ou "-350,00"
        r'\s*$'              # fim da linha
    )

    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue
            for linha in texto.split('\n'):
                match = padrao.search(linha)
                if match:
                    data_str, descricao, valor_str = match.groups()
                    linhas_encontradas.append({
                        'data_raw': data_str,
                        'descricao': descricao.strip(),
                        'valor_raw': valor_str
                    })

    if not linhas_encontradas:
        print("❌ Não foi possível extrair transações deste PDF.")
        return pd.DataFrame(columns=['data', 'descricao', 'valor'])

    df = pd.DataFrame(linhas_encontradas)
    ano_atual = pd.Timestamp.now().year
    df['data'] = pd.to_datetime(df['data_raw'] + f'/{ano_atual}', format='%d/%m/%Y', errors='coerce')
    df['valor'] = (
        df['valor_raw']
        .str.replace('.', '', regex=False)
        .str.replace(',', '.', regex=False)
        .pipe(pd.to_numeric, errors='coerce')
    )
    df = df[['data', 'descricao', 'valor']].dropna()
    df['descricao'] = df['descricao'].str.upper().str.strip()
    return df.sort_values('data').reset_index(drop=True)


def ler_pdf_generico(caminho):
    """
    Tenta extrair transações de qualquer PDF bancário.
    Menos preciso, mas funciona como ponto de partida
    para bancos que você ainda não tem um leitor específico.

    Busca qualquer linha que tenha: data + texto + valor em R$
    """
    print(f"📄 Lendo PDF genérico: {caminho}")
    linhas_encontradas = []

    # Padrão genérico: aceita DD/MM/AAAA ou DD/MM ou DD MMM
    padrao = re.compile(
        r'(\d{2}[/\s]\d{2}(?:[/\s]\d{2,4})?|\d{2}\s+\w{3})'
        r'\s+(.+?)\s+'
        r'(-?R?\$?\s*[\d.]+,\d{2})'
    )

    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            texto = page.extract_text()
            if not texto:
                continue
            for linha in texto.split('\n'):
                match = padrao.search(linha)
                if match:
                    data_str, descricao, valor_str = match.groups()
                    linhas_encontradas.append({
                        'data_raw': data_str.strip(),
                        'descricao': descricao.strip(),
                        'valor_raw': valor_str.strip()
                    })

    print(f"✅ {len(linhas_encontradas)} linhas encontradas (verifique se estão corretas).")
    return linhas_encontradas


# ---------------------------------------------------------
# COMO USAR — escolha o banco e aponte o arquivo
# ---------------------------------------------------------
if __name__ == '__main__':

    import sys

    # PASSO 1 — Inspecione sempre primeiro!
    # Descomente a linha abaixo na primeira vez que usar um PDF novo:
    # inspecionar_pdf('dados/extrato.pdf')

    # PASSO 2 — Escolha o leitor do seu banco
    banco = 'nubank'   # troque para 'itau' ou 'generico'
    arquivo = 'dados/extrato.pdf'

    if not __import__('os').path.exists(arquivo):
        print(f"Coloque seu arquivo PDF em: {arquivo}")
        print("Depois rode novamente.")
        sys.exit(0)

    if banco == 'nubank':
        df = ler_pdf_nubank(arquivo)
    elif banco == 'itau':
        df = ler_pdf_itau(arquivo)
    else:
        linhas = ler_pdf_generico(arquivo)
        print(linhas[:10])
        sys.exit(0)

    if len(df) > 0:
        print("\n=== Transações extraídas ===")
        print(df.to_string(index=False))
        print(f"\nTotal: R$ {df['valor'].sum():,.2f}")