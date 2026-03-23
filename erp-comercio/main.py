import flet as ft
from database import criar_tabelas, produtos_estoque_baixo, resumo_financeiro


def main(page: ft.Page):
    page.title         = "ERP Comércio"
    page.window.width  = 1100
    page.window.height = 700
    page.theme_mode    = ft.ThemeMode.DARK
    page.bgcolor       = "#0f0f1a"
    page.padding       = 0

    criar_tabelas()

    COR_SIDEBAR  = "#16213e"
    COR_CARD     = "#1a1a2e"
    COR_BORDA    = "#2a2a4a"
    COR_AZUL     = "#4a7cf7"
    COR_VERDE    = "#4ec9b0"
    COR_AMARELO  = "#dcdcaa"
    COR_VERMELHO = "#f44747"
    COR_TEXTO    = "#e0e0e0"
    COR_SUBTEXTO = "#8899aa"

    area_conteudo = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    # ---------------------------------------------------------
    # DASHBOARD
    # ---------------------------------------------------------
    def tela_dashboard():
        area_conteudo.controls.clear()

        resumo = resumo_financeiro()
        baixo  = produtos_estoque_baixo()

        def card_stat(titulo, valor, cor, icone):
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icone, color=cor, size=28),
                        ft.Text(titulo, size=13, color=COR_SUBTEXTO)
                    ], spacing=8),
                    ft.Text(valor, size=28, weight=ft.FontWeight.BOLD, color=cor)
                ], spacing=8),
                bgcolor=COR_CARD,
                border=ft.border.all(1, COR_BORDA),
                border_radius=12,
                padding=20,
                expand=True
            )

        area_conteudo.controls.append(
            ft.Column([
                ft.Text("Dashboard", size=22, weight=ft.FontWeight.BOLD, color=COR_TEXTO),
                ft.Text("Visão geral do seu negócio", size=13, color=COR_SUBTEXTO),
                ft.Divider(color=COR_BORDA),
                ft.Row([
                    card_stat("Receitas do mês",  f"R$ {resumo['receitas']:,.2f}", COR_VERDE,    ft.Icons.TRENDING_UP),
                    card_stat("Despesas do mês",  f"R$ {resumo['despesas']:,.2f}", COR_VERMELHO, ft.Icons.TRENDING_DOWN),
                    card_stat("Saldo do mês",     f"R$ {resumo['saldo']:,.2f}",    COR_AZUL,     ft.Icons.ACCOUNT_BALANCE_WALLET),
                ], spacing=16),
                ft.Container(height=20),
                ft.Text("⚠️ Estoque baixo", size=15, weight=ft.FontWeight.BOLD, color=COR_AMARELO) if baixo else ft.Text("✅ Estoque em dia", size=15, color=COR_VERDE),
                ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Text(p['nome'], size=13, color=COR_TEXTO, expand=True),
                            ft.Text(f"Atual: {p['estoque_atual']}", size=12, color=COR_VERMELHO),
                            ft.Text(f"  Mín: {p['estoque_minimo']}", size=12, color=COR_SUBTEXTO),
                        ]),
                        bgcolor=COR_CARD,
                        border=ft.border.all(1, COR_BORDA),
                        border_radius=8,
                        padding=ft.padding.symmetric(horizontal=16, vertical=10)
                    )
                    for p in baixo[:5]
                ], spacing=6) if baixo else ft.Container(),
            ], spacing=12, expand=True)
        )
        page.update()

    # ---------------------------------------------------------
    # TELAS DOS MÓDULOS
    # ---------------------------------------------------------
    def tela_clientes():
        from modulos.clientes import tela as t
        area_conteudo.controls.clear()
        area_conteudo.controls.append(t(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO))
        page.update()

    def tela_estoque():
        from modulos.estoque import tela as t
        area_conteudo.controls.clear()
        area_conteudo.controls.append(t(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO))
        page.update()

    def tela_vendas():
        from modulos.vendas import tela as t
        area_conteudo.controls.clear()
        area_conteudo.controls.append(t(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO))
        page.update()

    def tela_financeiro():
        from modulos.financeiro import tela as t
        area_conteudo.controls.clear()
        area_conteudo.controls.append(t(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO))
        page.update()

    def tela_relatorios():
        from modulos.relatorios import tela as t
        area_conteudo.controls.clear()
        area_conteudo.controls.append(t(page, COR_CARD, COR_BORDA, COR_AZUL, COR_TEXTO, COR_SUBTEXTO))
        page.update()

    # ---------------------------------------------------------
    # SIDEBAR
    # ---------------------------------------------------------
    def item_menu(icone, texto, acao):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icone, color="#7eb8f7", size=20),
                ft.Text(texto, size=13, color=COR_TEXTO)
            ], spacing=12),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
            border_radius=8,
            on_click=lambda e: acao(),
            bgcolor="transparent",
            ink=True
        )

    sidebar = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("🏪 ERP", size=22, weight=ft.FontWeight.BOLD, color=COR_AZUL),
                    ft.Text("Comércio", size=12, color=COR_SUBTEXTO),
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(vertical=24),
            ),
            ft.Divider(color=COR_BORDA),
            item_menu(ft.Icons.SPACE_DASHBOARD,       "Dashboard",  tela_dashboard),
            item_menu(ft.Icons.PEOPLE,                "Clientes",   tela_clientes),
            item_menu(ft.Icons.INVENTORY_2,           "Estoque",    tela_estoque),
            item_menu(ft.Icons.POINT_OF_SALE,         "Vendas",     tela_vendas),
            item_menu(ft.Icons.ACCOUNT_BALANCE,       "Financeiro", tela_financeiro),
            item_menu(ft.Icons.BAR_CHART,             "Relatórios", tela_relatorios),
            ft.Divider(color=COR_BORDA),
            ft.Container(
                content=ft.Text("v1.0.0", size=11, color=COR_SUBTEXTO),
                padding=ft.padding.only(left=16, bottom=16)
            )
        ], spacing=4),
        width=200,
        bgcolor=COR_SIDEBAR,
        border=ft.border.only(right=ft.BorderSide(1, COR_BORDA))
    )

    page.add(
        ft.Row([
            sidebar,
            ft.Container(
                content=area_conteudo,
                expand=True,
                padding=24,
                bgcolor="#0f0f1a"
            )
        ], expand=True, spacing=0)
    )

    tela_dashboard()


if __name__ == '__main__':
    ft.app(target=main)
