from ofxparse import OfxParser  # biblioteca que lê arquivos OFX
import pandas as pd              # biblioteca para trabalhar com tabelas
import chardet                # detecta o encoding do arquivo automaticamente


def ler_extrato_ofx(caminho):
    """
    Lê um arquivo OFX de extrato bancário e retorna uma tabela padronizada.

    Parâmetro:
        caminho: caminho do arquivo OFX (ex: 'dados/extrato.ofx')

    Retorna:
        Um DataFrame com colunas: data, descricao, valor
    """

    # ---------------------------------------------------------
    # PASSO 1 — Detectar o encoding do arquivo
    # ---------------------------------------------------------
    # OFX de bancos brasileiros às vezes vem em latin-1, às vezes utf-8
    # O chardet detecta automaticamente para evitar erros de caractere
    with open(caminho, 'rb') as f:
        resultado = chardet.detect(f.read())
        encoding = resultado['encoding'] or 'utf-8'
        print(f"Encoding detectado: {encoding}")

    # ---------------------------------------------------------
    # PASSO 2 — Abrir e parsear o arquivo OFX
    # ---------------------------------------------------------
    # "parsear" = ler e interpretar a estrutura do arquivo
    with open(caminho, encoding=encoding, errors='ignore') as f:
        ofx = OfxParser.parse(f)

    # ---------------------------------------------------------
    # PASSO 3 — Extrair as transações
    # ---------------------------------------------------------
    # O OFX pode ter várias contas dentro dele
    # Pegamos a primeira conta encontrada
    conta = ofx.account
    extrato = conta.statement
    transacoes = extrato.transactions

    print(f"\nBanco: {conta.institution.organization if conta.institution else 'não informado'}")
    print(f"Conta: {conta.account_id}")
    print(f"Total de transações: {len(transacoes)}")

    # ---------------------------------------------------------
    # PASSO 4 — Montar a tabela com os dados
    # ---------------------------------------------------------
    # Percorremos cada transação e extraímos os campos que precisamos
    linhas = []

    for t in transacoes:
        linhas.append({
            'data':      t.date,         # data da transação
            'descricao': t.memo,         # descrição (PIX, TED, compra...)
            'valor':     float(t.amount) # valor já vem como número no OFX
        })

    # Transforma a lista de dicionários em uma tabela pandas
    df = pd.DataFrame(linhas)

    # ---------------------------------------------------------
    # PASSO 5 — Tratar a coluna de DATA
    # ---------------------------------------------------------
    # No OFX a data já vem como objeto datetime, mas garantimos o formato certo
    df['data'] = pd.to_datetime(df['data'], errors='coerce')

    # Remove fuso horário se vier no arquivo (alguns bancos incluem)
    if df['data'].dt.tz is not None:
        df['data'] = df['data'].dt.tz_localize(None)

    # Remove linhas com data inválida
    linhas_invalidas = df['data'].isna().sum()
    if linhas_invalidas > 0:
        print(f"\nAtenção: {linhas_invalidas} linha(s) com data inválida removidas.")
    df = df.dropna(subset=['data'])

    # ---------------------------------------------------------
    # PASSO 6 — Tratar a coluna de DESCRIÇÃO
    # ---------------------------------------------------------
    df['descricao'] = (
        df['descricao']
        .astype(str)
        .str.strip()   # remove espaços extras
        .str.upper()   # tudo maiúsculo para comparações fáceis
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
    print(f"\nExtrato OFX carregado com sucesso: {len(df)} transações.")
    print(f"Período: {df['data'].min().date()} até {df['data'].max().date()}")
    print(f"Total créditos: R$ {df[df['valor'] > 0]['valor'].sum():,.2f}")
    print(f"Total débitos:  R$ {df[df['valor'] < 0]['valor'].sum():,.2f}")

    return df


# ---------------------------------------------------------
# TESTE — cria um OFX de exemplo e testa a leitura
# ---------------------------------------------------------
if __name__ == '__main__':

    # OFX é um formato de texto estruturado — criamos um exemplo manual
    exemplo_ofx = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:UTF-8
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
  <SIGNONMSGSRSV1>
    <SONRS>
      <STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>
      <DTSERVER>20260320</DTSERVER>
      <LANGUAGE>POR</LANGUAGE>
    </SONRS>
  </SIGNONMSGSRSV1>
  <BANKMSGSRSV1>
    <STMTTRNRS>
      <STMTRS>
        <CURDEF>BRL</CURDEF>
        <BANKACCTFROM>
          <BANKID>001</BANKID>
          <ACCTID>12345-6</ACCTID>
          <ACCTTYPE>CHECKING</ACCTTYPE>
        </BANKACCTFROM>
        <BANKTRANLIST>
          <DTSTART>20260301</DTSTART>
          <DTEND>20260320</DTEND>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20260301</DTPOSTED>
            <TRNAMT>5000.00</TRNAMT>
            <FITID>001</FITID>
            <MEMO>SALARIO</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20260302</DTPOSTED>
            <TRNAMT>-350.75</TRNAMT>
            <FITID>002</FITID>
            <MEMO>SUPERMERCADO</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20260305</DTPOSTED>
            <TRNAMT>-189.90</TRNAMT>
            <FITID>003</FITID>
            <MEMO>CONTA DE LUZ</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>CREDIT</TRNTYPE>
            <DTPOSTED>20260310</DTPOSTED>
            <TRNAMT>1200.00</TRNAMT>
            <FITID>004</FITID>
            <MEMO>TRANSFERENCIA RECEBIDA</MEMO>
          </STMTTRN>
          <STMTTRN>
            <TRNTYPE>DEBIT</TRNTYPE>
            <DTPOSTED>20260315</DTPOSTED>
            <TRNAMT>-87.50</TRNAMT>
            <FITID>005</FITID>
            <MEMO>FARMACIA</MEMO>
          </STMTTRN>
        </BANKTRANLIST>
        <LEDGERBAL>
          <BALAMT>5572.85</BALAMT>
          <DTASOF>20260320</DTASOF>
        </LEDGERBAL>
      </STMTRS>
    </STMTTRNRS>
  </BANKMSGSRSV1>
</OFX>"""

    # Salva o exemplo na pasta dados
    with open('dados/extrato_teste.ofx', 'w', encoding='utf-8') as f:
        f.write(exemplo_ofx)

    print("=== Testando leitor_ofx.py ===\n")
    tabela = ler_extrato_ofx('dados/extrato_teste.ofx')

    print("\n=== Tabela final ===")
    print(tabela.to_string(index=False))