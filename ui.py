from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import box
from rich.console import Group
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns
import time


from models import Item, Usage, GameState, Enemy, Attack, ItemType
from config import USD_PLN

# TYTUL = r"""
#  __  __ ____   ___   ____ ___ _   ___   __  _     ___   ____ _   _
# |  \/  |  _ \ / _ \ / ___|_ _| \ | \ \ / / | |   / _ \ / ___| | | |
# | |\/| | |_) | | | | |   | ||  \| |\ V /  | |  | | | | |   | |_| |
# | |  | |  _ <| |_| | |___| || |\  | | |   | |__| |_| | |___|  _  |
# |_|  |_|_| \_\\___/ \____|___|_| \_| |_|  |_____\___/ \____|_| |_|
# """
TYTUL = r"""
$$\      $$\ $$$$$$$\   $$$$$$\   $$$$$$\  $$$$$$$$\ $$\   $$\ $$\     $$\       $$\       $$$$$$\   $$$$$$\  $$\   $$\ 
$$$\    $$$ |$$  __$$\ $$  __$$\ $$  __$$\ \____$$  |$$$\  $$ |\$$\   $$  |      $$ |     $$  __$$\ $$  __$$\ $$ |  $$ |
$$$$\  $$$$ |$$ |  $$ |$$ /  $$ |$$ /  \__|    $$  / $$$$\ $$ | \$$\ $$  /       $$ |     $$ /  $$ |$$ /  \__|$$ |  $$ |
$$\$$\$$ $$ |$$$$$$$  |$$ |  $$ |$$ |         $$  /  $$ $$\$$ |  \$$$$  /        $$ |     $$ |  $$ |$$ |      $$$$$$$$ |
$$ \$$$  $$ |$$  __$$< $$ |  $$ |$$ |        $$  /   $$ \$$$$ |   \$$  /         $$ |     $$ |  $$ |$$ |      $$  __$$ |
$$ |\$  /$$ |$$ |  $$ |$$ |  $$ |$$ |  $$\  $$  /    $$ |\$$$ |    $$ |          $$ |     $$ |  $$ |$$ |  $$\ $$ |  $$ |
$$ | \_/ $$ |$$ |  $$ | $$$$$$  |\$$$$$$  |$$$$$$$$\ $$ | \$$ |    $$ |          $$$$$$$$\ $$$$$$  |\$$$$$$  |$$ |  $$ |
\__|     \__|\__|  \__| \______/  \______/ \________|\__|  \__|    \__|          \________|\______/  \______/ \__|  \__|                                   
"""
SZEROKOSC = 70


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


def wybierz_numer(ile: int) -> int:
    """Pyta o numer 1..ile. Zwraca wybor (1-indeksowany)."""
    while True:
        user = input_centrowany()
        if not user.isdigit():
            pokaz_komunikat("Podaj liczbe")
            continue
        wybor = int(user)
        if 1 <= wybor <= ile:
            return wybor
        pokaz_komunikat("Numer poza zakresem")


def input_centrowany(szerokosc: int = 65, formatowanie: str = "bold cyan") -> str:
    """Prompt wysrodkowany pod center tabela."""
    wciecie = " " * max(0, (console.width - szerokosc) // 2)
    return console.input(f"\n{wciecie}[{formatowanie}]❯[/] ")


def pokaz_wynik(wynik: str) -> None:
    """Wynik tury wysrodkowany (po zakonczeniu walki)."""
    console.print(Align.center(Text.from_markup(wynik)))


def pokaz_gole_rece() -> None:
    """Komunikat o braku broni."""
    console.print(
        Align.center(
            pusty_panel(
                "[cyan]Bron[/]",
                "Nie masz broni, walczysz [bold cyan]golymi rekoma[/].",
                True,
            )
        )
    )


def pokaz_komunikat(tekst: str) -> None:
    """Krotki komunikat na srodku (bledy walidacji, info)."""
    console.print(Align.center(f"[dim]{tekst}[/]"))


def nowa_tabela(
    tytul: str,
    min_width: int = 120,
    linie: bool = False,
    naglowek: bool = True,
    title_style: str = "bold",
    border_style: str = "grey37",
) -> Table:
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
        tabela.add_row(str(i + 1), nazwa, typ, wartosc, akcje)

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
        expand=True,
    )
    console.print()
    console.print(panel)


def kolor_hp(hp: int, hp_max: int) -> str:
    """Kolor wg progu HP"""
    udzial = hp / hp_max if hp_max else 0
    if udzial > 0.5:
        return "green"
    if udzial > 0.25:
        return "yellow"
    return "red"


def pasek_hp(
    hp: int, hp_max: int, szerokosc: int = 12, kolor: str | None = None
) -> str:
    """Pasek HP jako string ze znacznikami koloru."""
    if hp_max <= 0:
        return ""

    hp = max(0, min(hp, hp_max))
    udzial = hp / hp_max

    pelne = round(udzial * szerokosc)
    pasek = "█" * pelne + "░" * (szerokosc - pelne)

    if kolor is None:
        kolor = kolor_hp(hp, hp_max)

    return f"[{kolor}]{pasek}[/]"


def pokaz_stan_hp(state: GameState) -> None:
    kolor = kolor_hp(state.hp, state.hp_max)

    console.print(
        Align.center(
            Panel(
                pasek_hp(state.hp, state.hp_max, 50),
                title="[bold white]Stan zdrowia[/]",
                subtitle=f"[{kolor}]{state.hp}[/] [dim]/[/] [green]{state.hp_max}[/]",
                border_style="grey37",
                box=box.ROUNDED,
                padding=(1, 2),
                expand=False,
            )
        )
    )


def pokaz_smierc():
    console.print(
        Align.center(
            Panel(
                "[bold red]NIE ŻYJESZ[/]\n\n[dim]Możesz wyjść (/wyjdz) lub sprawdzić statystyki.[/]",
                border_style="red",
                box=box.DOUBLE,
                width=SZEROKOSC,
                padding=(1, 4),
            )
        )
    )


def pokaz_komendy() -> None:
    """Lista dostepnych komend gracza."""
    tabela = nowa_tabela("Komendy", naglowek=False, min_width=60, linie=True)
    tabela.add_column(style="bold cyan", justify="right")
    tabela.add_column(style="dim")

    tabela.add_row("/ekwipunek", "co masz przy sobie")
    tabela.add_row("/stan", "twoje zdrowie")
    tabela.add_row("/historia", "podsumowanie przygody")
    tabela.add_row("/koszt", "tokeny i pieniadze")
    tabela.add_row("/zapisz", "zapisz gre")
    tabela.add_row("/wyjdz", "koniec")

    console.print(Align.center(tabela))


def pokaz_stan_walki(state: GameState, enemy: Enemy) -> None:
    """HP gracza i wroga z paskami."""
    tabela = nowa_tabela(
        tytul="Walka", naglowek=False, title_style="bold red", min_width=0, linie=True
    )

    tabela.add_column()
    tabela.add_column(justify="right")
    tabela.add_column(justify="left", width=30)

    max_hp_w_walce = max(state.hp_max, enemy.hp_max)
    szerokosc_gracza = round(state.hp_max / max_hp_w_walce * 30)
    szerokosc_wroga = round(enemy.hp_max / max_hp_w_walce * 30)

    tabela.add_row(
        "[green]Ty[/]",
        f"[cyan]{state.hp}/{state.hp_max}[/]",
        pasek_hp(state.hp, state.hp_max, szerokosc_gracza),
    )
    tabela.add_row(
        f"[red]{enemy.name.capitalize()}[/]",
        f"[cyan]{enemy.hp}/{enemy.hp_max}[/]",
        pasek_hp(enemy.hp, enemy.hp_max, szerokosc_wroga, kolor="red"),
    )

    console.print(Align.center(tabela))


def tabela_stanu_walki(state: GameState, enemy: Enemy) -> Table:
    """HP gracza i wroga z paskami."""
    tabela = Table(box=None, show_header=False, padding=(0, 2))

    tabela.add_column()
    tabela.add_column(justify="right")
    tabela.add_column(justify="left", width=30)

    max_hp_w_walce = max(state.hp_max, enemy.hp_max)
    szerokosc_gracza = round(state.hp_max / max_hp_w_walce * 30)
    szerokosc_wroga = round(enemy.hp_max / max_hp_w_walce * 30)

    tabela.add_row(
        "[green]Ty[/]",
        f"[cyan]{state.hp}/{state.hp_max}[/]",
        pasek_hp(state.hp, state.hp_max, szerokosc_gracza),
    )
    tabela.add_row(
        f"[red]{enemy.name.capitalize()}[/]",
        f"[cyan]{enemy.hp}/{enemy.hp_max}[/]",
        pasek_hp(enemy.hp, enemy.hp_max, szerokosc_wroga, kolor="red"),
    )

    return tabela


def pokaz_bronie(bronie: list[Item]) -> None:
    tabela = nowa_tabela("Wybierz bron", title_style="red", naglowek=False)
    tabela.add_column(justify="right")
    for i, bron in enumerate(bronie):
        for j, atak in enumerate(bron.attacks):
            numer = str(i + 1) if j == 0 else ""
            nazwa = bron.name if j == 0 else ""
            miss = (
                f"[red]{atak.miss_chance:.0%}[/]"
                if atak.miss_chance > 0.0
                else "[dim]-[/]"
            )
            tabela.add_row(
                f"[dim]{numer}[/]",
                f"[bold cyan]{nazwa}[/]",
                f"[orange1]{atak.name}[/]"
                if atak.miss_chance > 0.0
                else f"[green]{atak.name}[/]",
                f"{atak.damage_min} [dim]-[/] {atak.damage_max}",
                miss,
                end_section=True if j + 1 == len(bron.attacks) else False,
            )
    console.print(Align.center(tabela))


def pokaz_akcje(ataki: list[Attack]) -> None:
    tabela = nowa_tabela("Wybierz atak", title_style="red", naglowek=False, min_width=0)
    tabela.add_column(width=4, justify="right", style="dim")  # numer
    for i, atak in enumerate(ataki):
        miss = (
            f"[red]{atak.miss_chance:.0%}[/]" if atak.miss_chance > 0.0 else "[dim]-[/]"
        )
        tabela.add_row(
            f"[dim]{i + 1}[/]",
            f"[orange1]{atak.name}[/]"
            if atak.miss_chance > 0.0
            else f"[green]{atak.name}[/]",
            f"{atak.damage_min} [dim]-[/] {atak.damage_max}",
            miss,
        )
    console.print(Align.center(tabela))


def tabela_akcji(ataki: list[Attack]) -> Table:
    tabela = Table(box=None, show_header=False, padding=(0, 2))
    tabela.add_column(width=4, justify="right", style="dim")  # numer
    for i, atak in enumerate(ataki):
        miss = (
            f"[red]{atak.miss_chance:.0%}[/]" if atak.miss_chance > 0.0 else "[dim]-[/]"
        )
        tabela.add_row(
            f"[dim]{i + 1}[/]",
            f"[orange1]{atak.name}[/]"
            if atak.miss_chance > 0.0
            else f"[green]{atak.name}[/]",
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


def pokaz_liste_saveow(savy: list[dict]) -> None:
    tabela = nowa_tabela("Zapisane gry", min_width=80)
    tabela.add_column("#", style="dim", justify="right", width=4)
    tabela.add_column("Nazwa", style="bold cyan")
    tabela.add_column("HP", justify="right")
    tabela.add_column("")  # ← pasek, bez nagłówka
    tabela.add_column("Przedmioty", style="yellow", justify="right")
    tabela.add_column("Tury", style="dim", justify="right")

    for i, save in enumerate(savy):
        tabela.add_row(
            str(i + 1),
            save["nazwa"],
            f"{save['hp']}/{save['hp_max']}",
            pasek_hp(save["hp"], save["hp_max"], 15),
            str(save["przedmioty"]),
            str(save["tury"]),
        )

    console.print(Align.center(tabela))


def wyrownaj_art(art: str) -> str:
    """Usuwa wspolne wciecie z obu stron i wyrownuje dlugosci."""
    linie = [
        l.rstrip() for l in art.strip("\n").split("\n")
    ]  # ← rstrip usuwa martwe spacje

    niepuste = [l for l in linie if l.strip()]
    wciecie = min(len(l) - len(l.lstrip()) for l in niepuste)
    linie = [l[wciecie:] for l in linie]

    max_dl = max(len(l) for l in linie)
    return "\n".join(l.ljust(max_dl) for l in linie)


def pokaz_tytul() -> None:
    console.clear()
    console.print("\n" * 2)
    console.print(Align.center(Text(wyrownaj_art(TYTUL), style="bold red")))
    console.print("\n" * 2)
    console.print(
        Align.center(
            Panel(
                Align.center(
                    "[dim italic]Budzisz sie w ciemnosci.\nNie pamietasz, jak tu trafiles.[/]"
                ),
                border_style="red",
                box=box.DOUBLE,
                width=SZEROKOSC,
                padding=(1, 4),
            )
        )
    )
    console.print("\n" * 2)


def pokaz_sam_tytul() -> None:
    console.clear()
    console.print("\n" * 2)
    console.print(Align.center(Text(wyrownaj_art(TYTUL), style="bold red")))


def pokaz_menu(sa_savy: bool) -> None:
    """Opcje startowe jako przyciski obok siebie."""
    nowa = Panel(
        "[dim]1[/]\n\n[bold]NOWA GRA[/]",
        border_style="grey37",
        box=box.ROUNDED,
        width=20,
        padding=(1, 2),
    )

    if not sa_savy:
        console.print(Align.center(nowa))
        return

    wczytaj = Panel(
        "[dim]2[/]\n\n[bold]WCZYTAJ GRE[/]",
        border_style="grey37",
        box=box.ROUNDED,
        width=20,
        padding=(1, 2),
    )

    ustawienia = Panel(
        "[dim]3[/]\n\n[dim]USTAWIENIA[/]",
        border_style="grey37",
        box=box.ROUNDED,
        width=20,
        padding=(1, 2),
    )

    console.print(Align.center(Columns([nowa, wczytaj, ustawienia], padding=(0, 1))))


def main() -> None:
    state = GameState(hp=87, hp_max=100)
    pokaz_stan_hp(state)


if __name__ == "__main__":
    main()
