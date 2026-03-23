import flet as ft
from database import executar, buscar_todos, atualizar_estoque


def snack(page, msg, cor="#1e4a2e"):
    page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=cor)
    page.snack_bar.open = True
    page.update()


def tela(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO):

    produto_selecionado = {"id": None}

    campo_codigo    = ft.TextField(label="Código", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_nome      = ft.TextField(label="Nome do produto", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_categoria = ft.TextField(label="Categoria", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_unidade   = ft.TextField(label="Unidade (UN, KG, L...)", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_custo     = ft.TextField(label="Preço de custo (R$)", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, keyboard_type=ft.KeyboardType.NUMBER)
    campo_venda     = ft.TextField(label="Preço de venda (R$)", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, keyboard_type=ft.KeyboardType.NUMBER)
    campo_estoque   = ft.TextField(label="Estoque atual", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, keyboard_type=ft.KeyboardType.NUMBER)
    campo_minimo    = ft.TextField(label="Estoque mínimo", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, keyboard_type=ft.KeyboardType.NUMBER)
    campo_busca     = ft.TextField(label="🔍 Buscar produto...", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, on_change=lambda e: carregar_lista())
    campo_qtd_mov   = ft.TextField(label="Quantidade", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, keyboard_type=ft.KeyboardType.NUMBER)
    campo_motivo    = ft.TextField(label="Motivo", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)

    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

    def carregar_lista():
        lista.controls.clear()
        busca    = campo_busca.value.strip().lower() if campo_busca.value else ""
        produtos = buscar_todos("SELECT * FROM produtos WHERE ativo = 1 ORDER BY nome")
        if busca:
            produtos = [p for p in produtos if busca in p['nome'].lower() or busca in (p['codigo'] or '').lower()]
        if not produtos:
            lista.controls.append(ft.Text("Nenhum produto cadastrado.", size=13, color=COR_SUBTEXTO))
        else:
            for p in produtos:
                cor_estoque = "#f44747" if p['estoque_atual'] <= p['estoque_minimo'] else "#4ec9b0"
                alerta      = " ⚠️" if p['estoque_atual'] <= p['estoque_minimo'] else ""
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{p['nome']}{alerta}", size=13, weight=ft.FontWeight.W_500, color=COR_TEXTO),
                                ft.Text(f"Cód: {p['codigo'] or '-'} • {p['categoria'] or '-'} • {p['unidade']}", size=12, color=COR_SUBTEXTO),
                            ], spacing=2, expand=True),
                            ft.Column([
                                ft.Text(f"Estoque: {p['estoque_atual']}", size=12, color=cor_estoque, weight=ft.FontWeight.BOLD),
                                ft.Text(f"Venda: R$ {p['preco_venda']:.2f}", size=12, color=COR_SUBTEXTO),
                            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
                            ft.Row([
                                ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color="#4ec9b0", icon_size=18, tooltip="Entrada", on_click=lambda e, prod=p: movimentar(prod, 'entrada')),
                                ft.IconButton(ft.Icons.REMOVE_CIRCLE, icon_color="#dcdcaa", icon_size=18, tooltip="Saída", on_click=lambda e, prod=p: movimentar(prod, 'saida')),
                                ft.IconButton(ft.Icons.EDIT, icon_color=COR_AZUL, icon_size=18, on_click=lambda e, prod=p: editar_produto(prod)),
                                ft.IconButton(ft.Icons.DELETE, icon_color="#f44747", icon_size=18, on_click=lambda e, pid=p['id']: excluir_produto(pid)),
                            ], spacing=0)
                        ]),
                        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=8,
                        padding=ft.padding.symmetric(horizontal=16, vertical=10)
                    )
                )
        page.update()

    def limpar_form():
        produto_selecionado["id"] = None
        campo_codigo.value = campo_nome.value = campo_categoria.value = ""
        campo_custo.value  = campo_venda.value = ""
        campo_unidade.value  = "UN"
        campo_estoque.value  = "0"
        campo_minimo.value   = "0"
        txt_titulo.value     = "Novo produto"
        page.update()

    def salvar_produto(e):
        if not campo_nome.value.strip():
            snack(page, "Digite o nome do produto!", "#f44747")
            return
        try:
            custo   = float(campo_custo.value or 0)
            venda   = float(campo_venda.value or 0)
            estoque = float(campo_estoque.value or 0)
            minimo  = float(campo_minimo.value or 0)
        except ValueError:
            snack(page, "Valores numéricos inválidos!", "#f44747")
            return

        if produto_selecionado["id"]:
            executar('''UPDATE produtos SET codigo=?, nome=?, categoria=?, unidade=?,
                preco_custo=?, preco_venda=?, estoque_atual=?, estoque_minimo=? WHERE id=?''',
                (campo_codigo.value, campo_nome.value, campo_categoria.value, campo_unidade.value,
                 custo, venda, estoque, minimo, produto_selecionado["id"]))
            snack(page, "✅ Produto atualizado!")
        else:
            executar('''INSERT INTO produtos (codigo, nome, categoria, unidade, preco_custo, preco_venda, estoque_atual, estoque_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (campo_codigo.value, campo_nome.value, campo_categoria.value, campo_unidade.value,
                 custo, venda, estoque, minimo))
            snack(page, "✅ Produto cadastrado!")

        limpar_form()
        carregar_lista()

    def editar_produto(p):
        produto_selecionado["id"] = p['id']
        campo_codigo.value    = p['codigo'] or ""
        campo_nome.value      = p['nome'] or ""
        campo_categoria.value = p['categoria'] or ""
        campo_unidade.value   = p['unidade'] or "UN"
        campo_custo.value     = str(p['preco_custo'])
        campo_venda.value     = str(p['preco_venda'])
        campo_estoque.value   = str(p['estoque_atual'])
        campo_minimo.value    = str(p['estoque_minimo'])
        txt_titulo.value      = "Editar produto"
        page.update()

    def excluir_produto(pid):
        def confirmar(e):
            executar("UPDATE produtos SET ativo = 0 WHERE id = ?", (pid,))
            dlg.open = False
            page.update()
            carregar_lista()
            snack(page, "Produto removido.", "#333")

        def cancelar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text("Deseja remover este produto?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.TextButton("Excluir", on_click=confirmar, style=ft.ButtonStyle(color="#f44747")),
            ]
        )
        page.dialog = dlg
        page.dialog.open = True
        page.update()

    def movimentar(produto, tipo):
        campo_qtd_mov.value = ""
        campo_motivo.value  = ""

        def confirmar(e):
            try:
                qtd = float(campo_qtd_mov.value or 0)
            except ValueError:
                return
            if qtd <= 0:
                return
            atualizar_estoque(produto['id'], qtd, tipo, campo_motivo.value)
            dlg.open = False
            page.update()
            carregar_lista()
            snack(page, f"✅ {'Entrada' if tipo == 'entrada' else 'Saída'} registrada!")

        def cancelar(e):
            dlg.open = False
            page.update()

        cor_tipo  = "#4ec9b0" if tipo == 'entrada' else "#dcdcaa"
        nome_tipo = "Entrada de estoque" if tipo == 'entrada' else "Saída de estoque"

        dlg = ft.AlertDialog(
            title=ft.Text(nome_tipo, color=cor_tipo),
            content=ft.Column([
                ft.Text(f"Produto: {produto['nome']}", size=13, color=COR_TEXTO),
                ft.Text(f"Estoque atual: {produto['estoque_atual']}", size=12, color=COR_SUBTEXTO),
                ft.Container(height=8),
                campo_qtd_mov,
                campo_motivo,
            ], spacing=8, tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.ElevatedButton("Confirmar", on_click=confirmar, bgcolor=cor_tipo, color="white"),
            ]
        )
        page.dialog = dlg
        page.dialog.open = True
        page.update()

    txt_titulo = ft.Text("Novo produto", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO)

    formulario = ft.Container(
        content=ft.Column([
            txt_titulo,
            ft.Divider(color=COR_BORDA),
            ft.Row([campo_codigo, campo_nome, campo_categoria, campo_unidade], spacing=12),
            ft.Row([campo_custo, campo_venda, campo_estoque, campo_minimo], spacing=12),
            ft.Row([
                ft.ElevatedButton("💾 Salvar", on_click=salvar_produto, bgcolor=COR_AZUL, color="white", expand=True),
                ft.OutlinedButton("🗑 Limpar", on_click=lambda e: limpar_form(), expand=True),
            ], spacing=12),
        ], spacing=12),
        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=12, padding=20,
    )

    limpar_form()
    carregar_lista()

    return ft.Column([
        ft.Text("Estoque", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.Text("Cadastro e controle de produtos", size=13, color=COR_SUBTEXTO),
        ft.Divider(color=COR_BORDA),
        formulario,
        ft.Container(height=10),
        campo_busca,
        ft.Container(height=8),
        lista,
    ], spacing=8, expand=True)
