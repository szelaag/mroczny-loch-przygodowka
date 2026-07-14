from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box
from rich.console import Group
from rich.text import Text
from rich.rule import Rule


from models import Item, Usage, GameState, Enemy, Attack, ItemType
from config import USD_PLN

console = Console()

def pusty_panel(tytul: str, komunikat: str, formatuj: bool = False) -> Panel:
    """Panel dla pustej zawartosci — spojny z tabelami."""
    return Panel(
        komunikat if formatuj else f"[dim italic]{komunikat}[/]",
        title=tytul,
        border_style="grey37",
        box=box.ROUNDED,
        padding=(1, 2),
    )

def pusty_print() -> None:
    """printuje pusta linie"""
    console.print()

def input_walki() -> str:
    """Prompt wysrodkowany pod panelem walki."""
    wciecie = " " * max(0, (console.width - 65) // 2)
    return console.input(f"\n{wciecie}[bold cyan]❯[/] ")


def pokaz_wynik(wynik: str) -> None:
    """Wynik tury wysrodkowany (po zakonczeniu walki)."""
    console.print(Align.center(Text.from_markup(wynik)))

def pokaz_gole_rece() -> None:
    """Komunikat o braku broni."""
    console.print(Align.center(pusty_panel("[cyan]Bron[/]", "Nie masz broni, walczysz [bold cyan]golymi rekoma[/].", True)))


def pokaz_komunikat(tekst: str) -> None:
    """Krotki komunikat na srodku (bledy walidacji, info)."""
    console.print(Align.center(f"[dim]{tekst}[/]"))


def nowa_tabela(tytul: str, min_width: int = 120, linie: bool = False, naglowek: bool = True, title_style: str = "bold", border_style: str = "grey37") -> Table:
    return Table(
        title=tytul,
        title_style=title_style,
        border_style=border_style,
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

    tabela = nowa_tabela("[cyan]Ekwipunek[/]", linie=True)
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

def pokaz_narracje(tekst: str, narrator: str = "[#5f875f]Narrator[/]") -> None:
    """Wyswietla odpowiedz narratora w panelu"""
    panel = Panel(
        f"{tekst}",
        title=narrator,
        title_align="left",
        border_style="grey37",
        box=box.ROUNDED,
        padding=(1, 2),
        expand=True
    )
    console.print(panel)


def pasek_hp(hp: int, hp_max: int, szerokosc: int = 12, kolor: str | None = None) -> str:
    """Pasek HP jako string ze znacznikami koloru."""
    if hp_max <= 0:
        return ""

    hp = max(0, min(hp, hp_max))
    udzial = hp / hp_max

    pelne = round(udzial * szerokosc)
    pasek = "█" * pelne + "░" * (szerokosc - pelne)

    if kolor is None:
        if udzial > 0.5:
            kolor = "green"
        elif udzial > 0.25:
            kolor = "yellow"
        else:
            kolor = "red"

    return f"[{kolor}]{pasek}[/]"

def pokaz_stan_walki(state: GameState, enemy: Enemy) -> None:
    """HP gracza i wroga z paskami."""
    tabela = nowa_tabela(tytul="Walka", naglowek=False, title_style="bold red", min_width=0, linie=True)

    tabela.add_column()
    tabela.add_column(justify="right")
    tabela.add_column(justify="left", width=30)

    max_hp_w_walce = max(state.hp_max, enemy.hp_max)   
    szerokosc_gracza = round(state.hp_max / max_hp_w_walce * 30)   
    szerokosc_wroga  = round(enemy.hp_max / max_hp_w_walce * 30)   

    tabela.add_row("[green]Ty[/]", f"[cyan]{state.hp}/{state.hp_max}[/]", pasek_hp(state.hp, state.hp_max, szerokosc_gracza))
    tabela.add_row(f"[red]{enemy.name.capitalize()}[/]", f"[cyan]{enemy.hp}/{enemy.hp_max}[/]", pasek_hp(enemy.hp, enemy.hp_max, szerokosc_wroga, kolor="red"))

    console.print(Align.center(tabela))

def tabela_stanu_walki(state: GameState, enemy: Enemy) -> Table:
    """HP gracza i wroga z paskami."""
    tabela = Table(box=None, show_header=False, padding=(0, 2))

    tabela.add_column()
    tabela.add_column(justify="right")
    tabela.add_column(justify="left", width=30)

    max_hp_w_walce = max(state.hp_max, enemy.hp_max)   
    szerokosc_gracza = round(state.hp_max / max_hp_w_walce * 30)   
    szerokosc_wroga  = round(enemy.hp_max / max_hp_w_walce * 30)   

    tabela.add_row("[green]Ty[/]", f"[cyan]{state.hp}/{state.hp_max}[/]", pasek_hp(state.hp, state.hp_max, szerokosc_gracza))
    tabela.add_row(f"[red]{enemy.name.capitalize()}[/]", f"[cyan]{enemy.hp}/{enemy.hp_max}[/]", pasek_hp(enemy.hp, enemy.hp_max, szerokosc_wroga, kolor="red"))

    return tabela

    
def pokaz_bronie(bronie: list[Item]) -> None:
    tabela = nowa_tabela("Wybierz bron", title_style="red", naglowek=False)
    tabela.add_column(justify="right")
    for i, bron in enumerate(bronie):
        for j, atak in enumerate(bron.attacks):
            numer = str(i+1) if j == 0 else ""
            nazwa = bron.name if j == 0 else ""
            miss = f"[red]{atak.miss_chance:.0%}[/]" if atak.miss_chance > 0.0 else "[dim]-[/]"
            tabela.add_row(
                f"[dim]{numer}[/]",
                f"[bold cyan]{nazwa}[/]",
                f"[orange1]{atak.name}[/]" if atak.miss_chance > 0.0 else f"[green]{atak.name}[/]",
                f"{atak.damage_min} [dim]-[/] {atak.damage_max}",
                miss, end_section= True if j+1 == len(bron.attacks) else False
            )
    console.print(Align.center(tabela))


def pokaz_akcje(ataki: list[Attack]) -> None:
    tabela = nowa_tabela("Wybierz atak", title_style="red", naglowek=False, min_width=0)
    tabela.add_column(width=4, justify="right", style="dim")     # numer
    for i, atak in enumerate(ataki):
        miss = f"[red]{atak.miss_chance:.0%}[/]" if atak.miss_chance > 0.0 else "[dim]-[/]"
        tabela.add_row(
            f"[dim]{i+1}[/]",
            f"[orange1]{atak.name}[/]" if atak.miss_chance > 0.0 else f"[green]{atak.name}[/]",
            f"{atak.damage_min} [dim]-[/] {atak.damage_max}",
            miss,
        )
    console.print(Align.center(tabela))


def tabela_akcji(ataki: list[Attack]) -> Table:
    tabela = Table(box=None, show_header=False, padding=(0, 2))
    tabela.add_column(width=4, justify="right", style="dim")     # numer
    for i, atak in enumerate(ataki):
        miss = f"[red]{atak.miss_chance:.0%}[/]" if atak.miss_chance > 0.0 else "[dim]-[/]"
        tabela.add_row(
            f"[dim]{i+1}[/]",
            f"[orange1]{atak.name}[/]" if atak.miss_chance > 0.0 else f"[green]{atak.name}[/]",
            f"{atak.damage_min} [dim]-[/] {atak.damage_max}",
            miss,
        )
    return tabela

def panel_tury(
    state: GameState,
    enemy: Enemy,
    akcje: list[Attack],
    wynik: str = "",
) -> None:
    """Panel jednej tury: wynik poprzedniej + stan + akcje do wyboru."""
    elementy = []

    if wynik:
        elementy.append(Text.from_markup(wynik))
        elementy.append(Rule(style="grey37"))

    elementy.append(tabela_stanu_walki(state, enemy))
    elementy.append(Rule(style="grey37"))
    elementy.append(tabela_akcji(akcje))

    panel = Panel(
        Group(*elementy),
        title="[bold red]Walka[/]",
        title_align="left",
        border_style="red",
        box=box.ROUNDED,
        padding=(1, 2),
        width=80,
    )
    console.print(Align.center(panel))

def main() -> None:
    # --- dane testowe ---
    miecz = Item(
        name="miecz",
        type=ItemType.BRON,
        value=50,
        attacks=[
            Attack("light", 4, 6),
            Attack("heavy", 10, 16, miss_chance=0.4),
            Attack("stab", 7, 10),
        ],
    )
    sztylet = Item(
        name="sztylet",
        type=ItemType.BRON,
        value=20,
        attacks=[
            Attack("light", 3, 5),
            Attack("stab", 6, 8),
        ],
    )
    klucz = Item(name="klucz", type=ItemType.KLUCZ, value=0)

    state = GameState(hp=71, hp_max=100, inventory=[miecz, sztylet, klucz])
    enemy = Enemy(name="goblin", hp=16, hp_max=35, damage_min=4, damage_max=8)

    akcje = miecz.attacks

    # --- 1. pierwsza tura (bez wyniku) ---
    console.rule("[dim]pierwsza tura — brak wyniku[/]", style="grey37")
    panel_tury(state, enemy, akcje)

    # --- 2. tura z trafieniem ---
    console.rule("[dim]trafienie + kontratak[/]", style="grey37")
    wynik = "Zadales [bold]14[/] dmg  ·  [red]Goblin zadal 7 dmg[/]"
    panel_tury(state, enemy, akcje, wynik)

    # --- 3. tura z pudlem ---
    console.rule("[dim]pudlo + kontratak[/]", style="grey37")
    wynik = "[dim]Chybiles[/]  ·  [red]Goblin zadal 5 dmg[/]"
    panel_tury(state, enemy, akcje, wynik)

    # --- 4. wrog pada ---
    console.rule("[dim]wrog pada[/]", style="grey37")
    enemy_martwy = Enemy(name="goblin", hp=0, hp_max=35, damage_min=4, damage_max=8)
    wynik = "Zadales [bold]16[/] dmg  ·  [green]Goblin pada[/]"
    panel_tury(state, enemy_martwy, akcje, wynik)

    # --- 5. gracz na skraju (czerwony pasek) ---
    console.rule("[dim]gracz umiera[/]", style="grey37")
    state_ranny = GameState(hp=8, hp_max=100, inventory=[miecz])
    wynik = "[dim]Chybiles[/]  ·  [red]Goblin zadal 8 dmg[/]"
    panel_tury(state_ranny, enemy, akcje, wynik)

    # --- 6. gole rece (jedna akcja) ---
    console.rule("[dim]gole rece — jedna akcja[/]", style="grey37")
    panel_tury(state, enemy, [Attack("cios", 1, 2)])


if __name__ == "__main__":
    main()