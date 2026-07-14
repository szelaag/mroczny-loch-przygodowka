from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box

from items import ITEM_CATALOG
from models import Item, Usage
from config import USD_PLN

console = Console()

def pusty_panel(tytul: str, komunikat: str) -> Panel:
    """Panel dla pustej zawartosci — spojny z tabelami."""
    return Panel(
        f"[dim italic]{komunikat}[/]",
        title=tytul,
        border_style="grey37",
        box=box.ROUNDED,
        padding=(1, 2),
    )


def nowa_tabela(tytul: str, min_width: int = 120, linie: bool = False, naglowek: bool = True) -> Table:
    return Table(
        title=tytul,
        title_style="bold",
        border_style="grey37",
        show_header=naglowek,
        header_style="bold",
        show_lines=linie,
        min_width=min_width,
        box=box.ROUNDED,
    )


def pokaz_eq(inventory: list[Item]) -> None:
    """Wyswietla ekwipunek jako tabele."""

    if not inventory:
        console.print(pusty_panel("Ekwipunek", "Nie masz przy sobie nic"))
        return

    tabela = nowa_tabela("Ekwipunek", linie=True)
    tabela.add_column("#", style="dim", width=3, justify="right")
    tabela.add_column("Przedmiot", style="bold cyan")
    tabela.add_column("Typ", style="dim")
    tabela.add_column("Wartosc", justify="right", style="yellow")
    tabela.add_column("Akcje")

    for i, item in enumerate(inventory):
        nazwa = item.name
        typ = item.type.value
        wartosc = str(item.value)
        akcje = "-"
        if item.attacks:
            akcje = ", ".join([atak.name for atak in item.attacks])
        tabela.add_row(str(i+1), nazwa, typ, wartosc, akcje)

    console.print(Align.center(tabela))


def pokaz_koszt(usage: Usage) -> None:
    """Wyswietla Usage jako tabele"""
    tabela = nowa_tabela("Koszt rozmowy", naglowek=False, min_width=60, linie=True)

    tabela.add_column(style="dim", justify="left")  
    tabela.add_column(style="yellow", justify="right") 

    tabela.add_row("USD", f"{usage.total_cost:.4f}")
    tabela.add_row("PLN", f"{usage.total_cost * USD_PLN:.4f}", end_section=True)  
    tabela.add_row("Input", f"{usage.total_input_tokens:,}")
    tabela.add_row("Output", f"{usage.total_output_tokens:,}")
    tabela.add_row("Suma", f"{usage.total_input_tokens + usage.total_output_tokens:,}")

    console.print()
    console.print(Align.center(tabela))

def pokaz_narracje(tekst: str) -> None:
    """Wyswietla odpowiedz narratora w panelu"""
    panel = Panel(
        f"{tekst}",
        title="[#5f875f]Narrator[/]",
        title_align="left",
        border_style="grey37",
        box=box.ROUNDED,
        padding=(1, 2),
        expand=True
    )
    console.print(panel)

def main() -> None:
    inventory = [ITEM_CATALOG["miecz"], ITEM_CATALOG["klucz"], ITEM_CATALOG["sztylet"]]
    # pokaz_eq(inventory)
    # console.print()
    # console.rule(style="red", title="Dla pustego :")
    # console.print()
    # pokaz_eq([])
    # usage = Usage()
    # usage.total_cost = 3.231
    # pokaz_koszt(usage)
    narrator = "Przykucasz i przyglądasz się szczelinę pod drzwiami. Cień kołysze się miarowo — coś lub ktoś chodzi tam w kółko. Słyszysz teraz cichy, głuchy pomruk, rytmiczny jak oddech śpiącego zwierzęcia.\n\nCokolwiek jest za tymi drzwiami, nie wie jeszcze o tobie.\n\nZostawiasz je w spokoju i idziesz do uchylonych drzwi, czy próbujesz zajrzeć do środka?"
    pokaz_narracje(narrator)

    user = console.input("[bold cyan]   ❯[/] ")
    pokaz_eq(inventory)

    user = console.input("[bold cyan]   ❯[/] ")



if __name__ == "__main__":
    main()