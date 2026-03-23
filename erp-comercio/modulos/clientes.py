import flet as ft
from database import executar, buscar_todos


def snack(page, msg, cor="#1e4a2e"):
    page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=cor)
    page.snack_bar.open = True
    page.update()


def tela(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO):

    cliente_selecionado = {"id": None}

    campo_nome     = ft.TextField(label="Nome completo", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_cpf      = ft.TextField(label="CPF / CNPJ", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_telefone = ft.TextField(label="Telefone", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_email    = ft.TextField(label="Email", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_endereco = ft.TextField(label="Endereço", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_cidade   = ft.TextField(label="Cidade", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL)
    campo_busca    = ft.TextField(label="🔍 Buscar cliente...", expand=True, color=COR_TEXTO, border_color=COR_BORDA, focused_border_color=COR_AZUL, on_change=lambda e: carregar_lista())

    lista = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)

    def carregar_lista():
        lista.controls.clear()
        busca    = campo_busca.value.strip().lower() if campo_busca.value else ""
        clientes = buscar_todos("SELECT * FROM clientes WHERE ativo = 1 ORDER BY nome")
        if busca:
            clientes = [c for c in clientes if busca in c['nome'].lower() or busca in (c['cpf_cnpj'] or '').lower()]
        if not clientes:
            lista.controls.append(ft.Text("Nenhum cliente cadastrado.", size=13, color=COR_SUBTEXTO))
        else:
            for c in clientes:
                lista.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(c['nome'], size=13, weight=ft.FontWeight.W_500, color=COR_TEXTO),
                                ft.Text(f"{c['telefone'] or ''} • {c['cidade'] or ''}", size=12, color=COR_SUBTEXTO),
                            ], spacing=2, expand=True),
                            ft.Row([
                                ft.IconButton(ft.Icons.EDIT, icon_color=COR_AZUL, icon_size=18, on_click=lambda e, cli=c: editar_cliente(cli)),
                                ft.IconButton(ft.Icons.DELETE, icon_color="#f44747", icon_size=18, on_click=lambda e, cid=c['id']: excluir_cliente(cid)),
                            ], spacing=0)
                        ]),
                        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=8,
                        padding=ft.padding.symmetric(horizontal=16, vertical=10)
                    )
                )
        page.update()

    def limpar_form():
        cliente_selecionado["id"] = None
        campo_nome.value = campo_cpf.value = campo_telefone.value = ""
        campo_email.value = campo_endereco.value = campo_cidade.value = ""
        txt_titulo.value = "Novo cliente"
        page.update()

    def salvar_cliente(e):
        if not campo_nome.value.strip():
            snack(page, "Digite o nome do cliente!", "#f44747")
            return
        if cliente_selecionado["id"]:
            executar('UPDATE clientes SET nome=?, cpf_cnpj=?, telefone=?, email=?, endereco=?, cidade=? WHERE id=?',
                (campo_nome.value, campo_cpf.value, campo_telefone.value, campo_email.value, campo_endereco.value, campo_cidade.value, cliente_selecionado["id"]))
            snack(page, "✅ Cliente atualizado!")
        else:
            executar('INSERT INTO clientes (nome, cpf_cnpj, telefone, email, endereco, cidade) VALUES (?, ?, ?, ?, ?, ?)',
                (campo_nome.value, campo_cpf.value, campo_telefone.value, campo_email.value, campo_endereco.value, campo_cidade.value))
            snack(page, "✅ Cliente cadastrado!")
        limpar_form()
        carregar_lista()

    def editar_cliente(c):
        cliente_selecionado["id"] = c['id']
        campo_nome.value     = c['nome'] or ""
        campo_cpf.value      = c['cpf_cnpj'] or ""
        campo_telefone.value = c['telefone'] or ""
        campo_email.value    = c['email'] or ""
        campo_endereco.value = c['endereco'] or ""
        campo_cidade.value   = c['cidade'] or ""
        txt_titulo.value     = "Editar cliente"
        page.update()

    def excluir_cliente(cid):
        def confirmar(e):
            executar("UPDATE clientes SET ativo = 0 WHERE id = ?", (cid,))
            dlg.open = False
            page.update()
            carregar_lista()
            snack(page, "Cliente removido.", "#333")

        def cancelar(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar exclusão"),
            content=ft.Text("Deseja remover este cliente?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar),
                ft.TextButton("Excluir", on_click=confirmar, style=ft.ButtonStyle(color="#f44747")),
            ]
        )
        page.dialog = dlg
        page.dialog.open = True
        page.update()

    txt_titulo = ft.Text("Novo cliente", size=15, weight=ft.FontWeight.BOLD, color=COR_TEXTO)

    formulario = ft.Container(
        content=ft.Column([
            txt_titulo,
            ft.Divider(color=COR_BORDA),
            ft.Row([campo_nome, campo_cpf], spacing=12),
            ft.Row([campo_telefone, campo_email], spacing=12),
            ft.Row([campo_endereco, campo_cidade], spacing=12),
            ft.Row([
                ft.ElevatedButton("💾 Salvar", on_click=salvar_cliente, bgcolor=COR_AZUL, color="white", expand=True),
                ft.OutlinedButton("🗑 Limpar", on_click=lambda e: limpar_form(), expand=True),
            ], spacing=12),
        ], spacing=12),
        bgcolor=COR_CARD, border=ft.border.all(1, COR_BORDA), border_radius=12, padding=20,
    )

    carregar_lista()

    return ft.Column([
        ft.Text("Clientes", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
        ft.Text("Cadastro e gerenciamento de clientes", size=13, color=COR_SUBTEXTO),
        ft.Divider(color=COR_BORDA),
        formulario,
        ft.Container(height=10),
        campo_busca,
        ft.Container(height=8),
        lista,
    ], spacing=8, expand=True)
