import os
import sys
import pandas as pd

# Importa os módulos que criamos
from leitores.leitor_csv import ler_extrato_csv
from leitores.leitor_ofx import ler_extrato_ofx
from conciliador import conciliar
from relatorio import gerar_relatorio


# ---------------------------------------------------------
# CONFIGURAÇÕES — edite aqui conforme seu uso
# ---------------------------------------------------------

# Formato do extrato do banco: 'csv' ou 'ofx'
FORMATO_BANCO = 'csv'

# Caminhos dos arquivos
ARQUIVO_BANCO    = 'dados/extrato_banco.csv'   # extrato baixado do banco
ARQUIVO_INTERNO  = 'dados/lancamentos.csv'     # seus lançamentos internos


# ---------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------

def exibir_cabecalho():
    """Exibe o cabeçalho do sistema no terminal."""
    print("=" * 50)
    print("   SISTEMA DE CONCILIAÇÃO BANCÁRIA")
    print("=" * 50)
    print()


def verificar_arquivos():
    """
    Verifica se os arquivos necessários existem.
    Se não existir, avisa o usuário e encerra.
    """
    arquivos = [ARQUIVO_BANCO, ARQUIVO_INTERNO]

    for arquivo in arquivos:
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo não encontrado: {arquivo}")
            print(f"   Coloque o arquivo na pasta correta e tente novamente.")
            return False

    print(f"✅ Arquivo do banco encontrado:    {ARQUIVO_BANCO}")
    print(f"✅ Arquivo de lançamentos encontrado: {ARQUIVO_INTERNO}")
    print()
    return True


def ler_banco():
    """
    Lê o extrato do banco no formato configurado (CSV ou OFX).
    Retorna um DataFrame padronizado.
    """
    print(f"📂 Lendo extrato do banco ({FORMATO_BANCO.upper()})...")

    if FORMATO_BANCO == 'csv':
        df = ler_extrato_csv(ARQUIVO_BANCO)
    elif FORMATO_BANCO == 'ofx':
        df = ler_extrato_ofx(ARQUIVO_BANCO)
    else:
        print(f"❌ Formato '{FORMATO_BANCO}' não suportado. Use 'csv' ou 'ofx'.")
        sys.exit(1)

    return df


def ler_interno():
    """
    Lê os lançamentos internos (sempre CSV).
    Retorna um DataFrame padronizado.
    """
    print(f"\n📂 Lendo lançamentos internos...")
    df = ler_extrato_csv(ARQUIVO_INTERNO)
    return df


def criar_arquivos_teste():
    """
    Cria arquivos de exemplo na pasta dados/
    para você testar o sistema sem precisar de arquivos reais.
    """
    os.makedirs('dados', exist_ok=True)

    # Extrato do banco (tem uma taxa bancária a mais)
    extrato_banco = """data;descricao;valor
01/03/2026;SALARIO;5000,00
02/03/2026;SUPERMERCADO;-350,75
05/03/2026;CONTA DE LUZ;-189,90
10/03/2026;TRANSFERENCIA RECEBIDA;1200,00
15/03/2026;FARMACIA;-87,50
18/03/2026;TAXA BANCARIA;-25,00"""

    # Lançamentos internos (tem um fornecedor a mais)
    lancamentos_internos = """data;descricao;valor
01/03/2026;SALARIO;5000,00
02/03/2026;SUPERMERCADO;-350,75
05/03/2026;CONTA DE LUZ;-189,90
10/03/2026;TRANSFERENCIA RECEBIDA;1200,00
15/03/2026;FARMACIA;-87,50
20/03/2026;FORNECEDOR XYZ;-500,00"""

    with open('dados/extrato_banco.csv', 'w', encoding='utf-8') as f:
        f.write(extrato_banco)

    with open('dados/lancamentos.csv', 'w', encoding='utf-8') as f:
        f.write(lancamentos_internos)

    print("✅ Arquivos de teste criados em dados/")
    print("   → dados/extrato_banco.csv")
    print("   → dados/lancamentos.csv")
    print()


# ---------------------------------------------------------
# FLUXO PRINCIPAL
# ---------------------------------------------------------

def main():
    exibir_cabecalho()

    # PASSO 1 — Verifica se os arquivos existem
    # Se não existir, pergunta se quer criar arquivos de teste
    if not verificar_arquivos():
        print()
        resposta = input("Deseja criar arquivos de teste para experimentar? (s/n): ").strip().lower()
        if resposta == 's':
            criar_arquivos_teste()
        else:
            print("\nColoque os arquivos nas pastas indicadas e rode o programa novamente.")
            sys.exit(0)

    # PASSO 2 — Lê o extrato do banco
    try:
        df_banco = ler_banco()
    except Exception as e:
        print(f"\n❌ Erro ao ler extrato do banco: {e}")
        print("   Verifique se o arquivo está no formato correto.")
        sys.exit(1)

    # PASSO 3 — Lê os lançamentos internos
    try:
        df_interno = ler_interno()
    except Exception as e:
        print(f"\n❌ Erro ao ler lançamentos internos: {e}")
        print("   Verifique se o arquivo está no formato correto.")
        sys.exit(1)

    # PASSO 4 — Executa a conciliação
    print("\n⚙️  Executando conciliação...")
    try:
        resultado = conciliar(df_banco, df_interno)
    except Exception as e:
        print(f"\n❌ Erro na conciliação: {e}")
        sys.exit(1)

    # PASSO 5 — Gera o relatório Excel
    print("\n📊 Gerando relatório Excel...")
    try:
        caminho = gerar_relatorio(resultado)
    except Exception as e:
        print(f"\n❌ Erro ao gerar relatório: {e}")
        sys.exit(1)

    # PASSO 6 — Abre o relatório automaticamente
    print()
    resposta = input("Deseja abrir o relatório agora? (s/n): ").strip().lower()
    if resposta == 's':
        os.startfile(caminho)  # abre o Excel automaticamente no Windows

    print()
    print("=" * 50)
    print("   CONCILIAÇÃO FINALIZADA COM SUCESSO!")
    print("=" * 50)


# ---------------------------------------------------------
# PONTO DE ENTRADA
# ---------------------------------------------------------
# Esse bloco garante que o main() só roda quando você
# executar esse arquivo diretamente (python main.py)
# e não quando outro arquivo importar ele.

if __name__ == '__main__':
    main()