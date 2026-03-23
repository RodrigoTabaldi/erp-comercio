import flet as ft
from database import executar, buscar_todos, resumo_financeiro
from datetime import datetime


def snack(page, msg, cor="#1e4a2e"):
    page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=cor)
    page.snack_bar.open = True
    page.update()


def tela(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO):

    lancamento_selecionado = {"id": None}

    campo_descricao  = ft.TextField(label="Descrição", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_valor      = ft.TextField(label="Valor (R$)", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, keyboard_type=ft.KeyboardType.NUMBER)
    campo_vencimento = ft.TextField(label="Vencimento (DD/MM/AAAA)", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_categoria  = ft.TextField(label="Categoria", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_busca      = ft.TextField(label="🔍 Buscar...", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, on_change=lambda e: carregar_lista())

    var_tipo = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="receita", label="Receita", fill_color="#4ec9b0"),
            ft.Radio(value="despesa", label="Despesa", fill_color="#f44747"),
        ]),
        value="receita"
    )

    txt_receitas = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color="#4ec9b0")
    txt_despesas = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color="#f44747")
    txt_saldo    = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD, color=COR_AZUL)

    def atualizar_resumo():
        r = resumo_financeiro()
        txt_receitas.value = f"R$ {r['receitas']:,.2f}"
        txt_despesas.value = f"R$ {r['despesas']:,.2f}"
        txt_saldo.value    = f"R$ {r['saldo']:,.2f}"
        txt_saldo.color    = "#4ec9b0" if r['saldo'] >= 0 else "#f44747"

    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

    def carregar_lista():
        lista.controls.clear()
        busca = campo_busca.value.strip().lower() if campo_busca.value else ""
        lancamentos = buscar_todos('SELECT * FROM financeiro ORDER BY pago ASC, vencimento ASC')
        if busca:
            lancamentos = [l for l in lancamentos if busca in l['descricao'].lower()]
        if not lancamentos:
            lista.controls.append(ft.Text("Nenhum lançamento cadastrado.", size=13, color=COR_SUBTEXTO))
        else:
            for l in lancamentos:
                cor_tipo  = "#4ec9b0" if l['tipo'] == 'receita' else "#f44747"
                icone_pago = ft.Icons.CHECK_CIRCLE if l['pago'] else ft.Icons.RADIO_BUTTON_UNCHECKED
                cor_icone  = "#4ec9b0" if l['pago'] else COR_SUBTEXTO
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(icone_pago, color=cor_icone, size=20),
                            ft.Column([
                                ft.Text(l['descricao'], size=13, weight=ft.FontWeight.W_500, color=COR_TEXTO),
                                ft.Text(f"{l['categoria'] or '-'} • Venc: {l['vencimento']}", size=12, color=COR_SUBTEXTO),
                            ], spacing=2, expand=True),
                            ft.Column([
                                ft.Text(f"R$ {l['valor']:,.2f}", size=13, weight=ft.FontWeight.BOLD, color=cor_tipo),
                                ft.Text("Pago" if l['pago'] else "Pendente", size=11, color=cor_icone),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                            ft.Row([
                                ft.IconButton(
                                    ft.Icons.CHECK if not l['pago'] else ft.Icons.UNDO,
                                    icon_color="#4ec9b0", icon_size=18,
                                    on_click=lambda e, lid=l['id'], pago=l['pago']: toggle_pago(lid, pago)
                                ),
                                ft.IconButton(ft.Icons.EDIT, icon_color=COR_AZUL, icon_size=18, on_click=lambda e, lan=l: editar_lancamento(lan)),
                                ft.IconButton(ft.Icons.DELETE, icon_color="#f44747", icon_size=18, on_click=lambda e, lid=l['id']: excluir_lancamento(lid)),
                            ], spacing=0)
                        ]),
                        bgcolor="#333" if l['pago'] else COR_CARD,
                        border=ft.border.all(1, COR_BORDA), border_radius=8,
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        opacity=0.6 if l['pago'] else 1.0
                    )
                )
        atualizar_resumo()
        page.update()

    def limpar_form():
        lancamento_selecionado["id"] = None
        campo_descricao.value  = ""
        campo_valor.value      = ""
        campo_vencimento.value = datetime.now().strftime("%d/%m/%Y")
        campo_categoria.value  = ""
        var_tipo.value         = "receita"
        txt_titulo.value       = "Novo lançamento"
        page.update()

    def salvar_lancamento(e):
        if not campo_descricao.value.strip():
            snack(page, "Digite a descrição!", "#f44747")
            return
        try:
            valor = float(campo_valor.value.replace(',', '.') or 0)
        except ValueError:
            snack(page, "Valor inválido!", "#f44747")
            return
        try:
            parts = campo_vencimento.value.split('/')
            vencimento = f"{parts[2]}-{parts[1]}-{parts[0]}"
        except:
            vencimento = datetime.now().strftime("%Y-%m-%d")

        if lancamento_selecionado["id"]:
            executar('UPDATE financeiro SET tipo=?, descricao=?, valor=?, vencimento=?, categoria=? WHERE id=?',
                (var_tipo.value, campo_descricao.value, valor, vencimento, campo_categoria.value, lancamento_selecionado["id"]))
            snack(page, "✅ Lançamento atualizado!")
        else:
            executar('INSERT INTO financeiro (tipo, descricao, valor, vencimento, categoria) VALUES (?, ?, ?, ?, ?)',
                (var_tipo.value, campo_descricao.value, valor, vencimento, campo_categoria.value))
            snack(page, "✅ Lançamento cadastrado!")
        limpar_form()
        carregar_lista()

    def editar_lancamento(l):
        lancamento_selecionado["id"] = l['id']
        campo_descricao.value  = l['descricao'] or ""
        campo_valor.value      = str(l['valor'])
        campo_categoria.value  = l['categoria'] or ""
        var_tipo.value         = l['tipo']
        try:
            parts = l['vencimento'].split('-')
            campo_vencimento.value = f"{parts[2]}/{parts[1]}/{parts[0]}"
        except:
            campo_vencimento.value = ""
        txt_titulo.value = "Editar lançamento"
        page.update()

    def toggle_pago(lid, pago_atual):
        novo  = 0 if pago_atual else 1
        data  = datetime.now().strftime("%Y-%m-%d") if novo else None
        executar("UPDATE financeiro SET pago=?, data_pagamento=? WHERE id=?", (novo, data, lid))
        carregar_lista()

    def excluir_lancamento(lid):
        def confirmar(e):
            executar("DELETE FROM financeiro WHERE id = ?", (lid,))
            dlg.open = False
            page.update()
            carregar_lista()
            snack(page, "Lançamento removido.", "#333")

        def cancelar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text("Deseja remover este lançamento?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.TextButton("Excluir", on_click=confirmar, style=ft.ButtonStyle(color="#f44747")),
            ]
        )
        page.dialog = dlg
        page.dialog.open = True
        page.update()

    txt_titulo = ft.Text("Novo lançamento", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO)

    cards_resumo = ft.Row([
        ft.Container(content=ft.Column([ft.Text("Receitas do mês", size=12, color=COR_SUBTEXTO), txt_receitas], spacing=4),
            bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=10, padding=16, expand=True),
        ft.Container(content=ft.Column([ft.Text("Despesas do mês", size=12, color=COR_SUBTEXTO), txt_despesas], spacing=4),
            bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=10, padding=16, expand=True),
        ft.Container(content=ft.Column([ft.Text("Saldo do mês", size=12, color=COR_SUBTEXTO), txt_saldo], spacing=4),
            bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=10, padding=16, expand=True),
    ], spacing=12)

    formulario = ft.Container(
        content=ft.Column([
            txt_titulo, ft.Divider(color=COR_BORDA), var_tipo,
            ft.Row([campo_descricao, campo_valor], spacing=12),
            ft.Row([campo_vencimento, campo_categoria], spacing=12),
            ft.Row([
                ft.ElevatedButton("💾 Salvar", on_click=salvar_lancamento, bgcolor=COR_AZUL, color="white", expand=True),
                ft.OutlinedButton("🗑 Limpar", on_click=lambda e: limpar_form(), expand=True),
            ], spacing=12),
        ], spacing=12),
        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=12, padding=20,
    )

    limpar_form()
    carregar_lista()

    return ft.Column([
        ft.Text("Financeiro", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.Text("Contas a pagar e receber", size=13, color=COR_SUBTEXTO),
        ft.Divider(color=COR_BORDA),
        cards_resumo,
        ft.Container(height=10),
        formulario,
        ft.Container(height=10),
        campo_busca,
        ft.Container(height=8),
        lista,
    ], spacing=8, expand=True)
