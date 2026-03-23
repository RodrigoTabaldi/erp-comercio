import flet as ft
from database import executar, buscar_todos, atualizar_estoque
from datetime import datetime


def snack(page, msg, cor="#1e4a2e"):
    page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=cor)
    page.snack_bar.open = True
    page.update()


def tela(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO):

    carrinho = []

    campo_busca_produto = ft.TextField(
        label="🔍 Buscar produto pelo nome ou código",
        expand=True, color=COR_TEXTO, border_color=COR_BORDA,
        focused_border_color=COR_AZUL,
        on_change=lambda e: buscar_produto()
    )
    campo_qtd = ft.TextField(
        label="Qtd", value="1", width=80,
        color=COR_TEXTO, border_color=COR_BORDA,
        focused_border_color=COR_AZUL,
        keyboard_type=ft.KeyboardType.NUMBER
    )
    campo_desconto = ft.TextField(
        label="Desconto (R$)", value="0", width=120,
        color=COR_TEXTO, border_color=COR_BORDA,
        focused_border_color=COR_AZUL,
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=lambda e: atualizar_total()
    )
    var_pagamento = ft.Dropdown(
        label="Forma de pagamento", width=200, color=COR_TEXTO,
        options=[
            ft.dropdown.Option("dinheiro",       "Dinheiro"),
            ft.dropdown.Option("cartao_credito",  "Cartão de crédito"),
            ft.dropdown.Option("cartao_debito",   "Cartão de débito"),
            ft.dropdown.Option("pix",             "PIX"),
            ft.dropdown.Option("fiado",           "Fiado"),
        ],
        value="dinheiro"
    )
    var_cliente = ft.Dropdown(label="Cliente (opcional)", expand=True, color=COR_TEXTO)

    lista_produtos_busca = ft.Column(spacing=4)
    lista_carrinho       = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)
    lista_vendas         = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

    txt_total    = ft.Text("R$ 0,00", size=24, weight=ft.FontWeight.BOLD, color="#4ec9b0")
    txt_subtotal = ft.Text("Subtotal: R$ 0,00", size=13, color=COR_SUBTEXTO)

    def carregar_clientes():
        clientes = buscar_todos("SELECT id, nome FROM clientes WHERE ativo=1 ORDER BY nome")
        var_cliente.options = [ft.dropdown.Option("", "Nenhum")] + [
            ft.dropdown.Option(str(c['id']), c['nome']) for c in clientes
        ]
        var_cliente.value = ""

    def buscar_produto():
        lista_produtos_busca.controls.clear()
        busca = campo_busca_produto.value.strip().lower()
        if not busca:
            page.update()
            return
        produtos    = buscar_todos("SELECT * FROM produtos WHERE ativo=1 ORDER BY nome")
        encontrados = [p for p in produtos if busca in p['nome'].lower() or busca in (p['codigo'] or '').lower()]
        for p in encontrados[:5]:
            cor_est = "#f44747" if p['estoque_atual'] <= 0 else COR_SUBTEXTO
            lista_produtos_busca.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(p['nome'], size=13, color=COR_TEXTO),
                            ft.Text(f"Estoque: {p['estoque_atual']} • R$ {p['preco_venda']:.2f}", size=12, color=cor_est),
                        ], spacing=2, expand=True),
                        ft.TextButton("+ Adicionar", on_click=lambda e, prod=p: adicionar_ao_carrinho(prod))
                    ]),
                    bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA),
                    border_radius=8, padding=ft.padding.symmetric(horizontal=12, vertical=8)
                )
            )
        page.update()

    def adicionar_ao_carrinho(produto):
        try:
            qtd = float(campo_qtd.value or 1)
        except ValueError:
            qtd = 1
        if qtd <= 0:
            return
        if produto['estoque_atual'] < qtd:
            snack(page, f"⚠️ Estoque insuficiente! Disponível: {produto['estoque_atual']}", "#f44747")
            return
        for item in carrinho:
            if item['produto_id'] == produto['id']:
                item['quantidade'] += qtd
                item['subtotal']    = item['quantidade'] * item['preco_unit']
                atualizar_carrinho()
                return
        carrinho.append({
            'produto_id': produto['id'],
            'nome':       produto['nome'],
            'quantidade': qtd,
            'preco_unit': produto['preco_venda'],
            'subtotal':   qtd * produto['preco_venda']
        })
        campo_busca_produto.value = ""
        lista_produtos_busca.controls.clear()
        atualizar_carrinho()

    def remover_do_carrinho(idx):
        carrinho.pop(idx)
        atualizar_carrinho()

    def atualizar_carrinho():
        lista_carrinho.controls.clear()
        if not carrinho:
            lista_carrinho.controls.append(
                ft.Text("Carrinho vazio — busque um produto acima.", size=13, color=COR_SUBTEXTO)
            )
        else:
            for i, item in enumerate(carrinho):
                lista_carrinho.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(item['nome'], size=13, weight=ft.FontWeight.W_500, color=COR_TEXTO),
                                ft.Text(f"{item['quantidade']} x R$ {item['preco_unit']:.2f}", size=12, color=COR_SUBTEXTO),
                            ], spacing=2, expand=True),
                            ft.Text(f"R$ {item['subtotal']:.2f}", size=13, weight=ft.FontWeight.BOLD, color="#4ec9b0"),
                            ft.IconButton(ft.Icons.DELETE, icon_color="#f44747", icon_size=16,
                                on_click=lambda e, idx=i: remover_do_carrinho(idx))
                        ]),
                        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA),
                        border_radius=8, padding=ft.padding.symmetric(horizontal=12, vertical=8)
                    )
                )
        atualizar_total()
        page.update()

    def atualizar_total():
        subtotal = sum(item['subtotal'] for item in carrinho)
        try:
            desconto = float(campo_desconto.value or 0)
        except ValueError:
            desconto = 0
        total = max(subtotal - desconto, 0)
        txt_subtotal.value = f"Subtotal: R$ {subtotal:.2f}"
        txt_total.value    = f"R$ {total:.2f}"
        page.update()

    def finalizar_venda(e):
        if not carrinho:
            snack(page, "Adicione produtos ao carrinho!", "#f44747")
            return
        try:
            desconto = float(campo_desconto.value or 0)
        except ValueError:
            desconto = 0
        subtotal   = sum(item['subtotal'] for item in carrinho)
        total      = max(subtotal - desconto, 0)
        cliente_id = var_cliente.value or None
        if cliente_id == "":
            cliente_id = None

        venda_id = executar('''
            INSERT INTO vendas (cliente_id, total, desconto, forma_pagamento, status)
            VALUES (?, ?, ?, ?, 'concluida')
        ''', (cliente_id, total, desconto, var_pagamento.value))

        for item in carrinho:
            executar('''
                INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unit, subtotal)
                VALUES (?, ?, ?, ?, ?)
            ''', (venda_id, item['produto_id'], item['quantidade'], item['preco_unit'], item['subtotal']))
            atualizar_estoque(item['produto_id'], item['quantidade'], 'saida', f'Venda #{venda_id}')

        executar('''
            INSERT INTO financeiro (tipo, descricao, valor, vencimento, pago, data_pagamento, categoria, venda_id)
            VALUES ('receita', ?, ?, ?, 1, ?, 'Vendas', ?)
        ''', (f"Venda #{venda_id}", total,
              datetime.now().strftime("%Y-%m-%d"),
              datetime.now().strftime("%Y-%m-%d"), venda_id))

        carrinho.clear()
        campo_desconto.value = "0"
        atualizar_carrinho()
        carregar_historico()
        snack(page, f"✅ Venda #{venda_id} finalizada! Total: R$ {total:.2f}")

    def carregar_historico():
        lista_vendas.controls.clear()
        vendas = buscar_todos('''
            SELECT v.*, c.nome as cliente_nome
            FROM vendas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            ORDER BY v.criado_em DESC LIMIT 20
        ''')
        if not vendas:
            lista_vendas.controls.append(
                ft.Text("Nenhuma venda realizada ainda.", size=13, color=COR_SUBTEXTO)
            )
        else:
            for v in vendas:
                lista_vendas.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"Venda #{v['id']} — {v['cliente_nome'] or 'Sem cliente'}", size=13, weight=ft.FontWeight.W_500, color=COR_TEXTO),
                                ft.Text(f"{v['forma_pagamento']} • {v['criado_em'][:16]}", size=12, color=COR_SUBTEXTO),
                            ], spacing=2, expand=True),
                            ft.Text(f"R$ {v['total']:,.2f}", size=14, weight=ft.FontWeight.BOLD, color="#4ec9b0"),
                        ]),
                        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA),
                        border_radius=8, padding=ft.padding.symmetric(horizontal=16, vertical=10)
                    )
                )
        page.update()

    carregar_clientes()
    carregar_historico()
    atualizar_carrinho()

    painel_venda = ft.Container(
        content=ft.Column([
            ft.Text("Nova venda", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
            ft.Divider(color=COR_BORDA),
            ft.Row([campo_busca_produto, campo_qtd], spacing=12),
            lista_produtos_busca,
            ft.Container(height=4),
            ft.Text("Carrinho", size=13, weight=ft.FontWeight.BOLD, color=COR_SUBTEXTO),
            lista_carrinho,
            ft.Divider(color=COR_BORDA),
            ft.Row([var_cliente, var_pagamento, campo_desconto], spacing=12),
            ft.Row([
                ft.Column([txt_subtotal, txt_total], spacing=4, expand=True),
                ft.ElevatedButton("✅ Finalizar venda", on_click=finalizar_venda,
                    bgcolor="#1e4a2e", color="#4ec9b0", height=50)
            ])
        ], spacing=10),
        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=12, padding=20,
    )

    return ft.Column([
        ft.Text("Vendas", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.Text("Registre vendas e consulte o histórico", size=13, color=COR_SUBTEXTO),
        ft.Divider(color=COR_BORDA),
        painel_venda,
        ft.Container(height=10),
        ft.Text("Últimas 20 vendas", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        lista_vendas,
    ], spacing=8, expand=True)
