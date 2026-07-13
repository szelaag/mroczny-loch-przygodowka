from dataclasses import asdict

from generation import generuj_statystyki
from models import GameState, Item, ItemType, Attack, Enemy
from items import ITEM_CATALOG, create_item
from combat import ENEMY_CATALOG, create_enemy, prowadz_walke, wybierz_akcje, wybierz_bron


COFNIJ = object()
ANULUJ = object()

def zapytaj_liczbe(prompt: str) -> int | object:
    """Pyta o liczbę całkowitą. Zwraca int, COFNIJ albo ANULUJ."""
    while True:
        user = input(prompt).strip()
        if user == "$$":
            return ANULUJ
        if user == "$$$":
            return COFNIJ
        if user.isdigit():
            return int(user)
        print(f" $ '{user}' to nie liczba, sprobuj ponownie")


def zapytaj_float(prompt: str, domyslna: float = 0.0) -> float | object:
    """Pyta o liczbę zmiennoprzecinkową (0.0-1.0). Enter = domyślna."""
    while True:
        user = input(prompt).strip()
        if user == "$$":
            return ANULUJ
        if user == "$$$":
            return COFNIJ
        if user == "":
            return domyslna
        try:
            wartosc = float(user)
        except ValueError:
            print(f" $ '{user}' to nie liczba")
            continue
        if 0.0 <= wartosc <= 1.0:
            return wartosc
        print(" $ podaj wartosc miedzy 0.0 a 1.0")

def show_catalog(catalog: dict) -> None:
    for keys in catalog:
        print(asdict(catalog[keys]))

def cmd_show_catalog(parts: list[str]) -> None:
    if len(parts) > 2:
        if parts[2] == "enemy":
            show_catalog(ENEMY_CATALOG)
        elif parts[2] == "item":
            show_catalog(ITEM_CATALOG)
        else:
            print(f"$ Nie ma katalogu: {parts[3]}")
    else:
        user = input("$ Ktory katalog pokazac (item | enemy): ")
        if user == "enemy":
            show_catalog(ENEMY_CATALOG)
        elif user == "item":
            show_catalog(ITEM_CATALOG)
        else:
            print(f"$ Nie ma katalogu: {user}")

def cmd_set_hp(state: GameState, parts: list[str]) -> None:
    if len(parts) == 1:
        user = zapytaj_liczbe("$ Liczba na ktora ustawic: ")
        if user is COFNIJ:
            print("$ Anulowano")
            return
        elif user is ANULUJ:
            print("$ Anulowano")
            return
        state.hp = user
    elif parts[1].isdigit():
        state.hp = int(parts[1])
    else:
        print("$ Niepoprawny format | $sethp <liczba>")

def show_eq(eq: list[Item], detailed: bool = False) -> None:
    if detailed:
        print("\n=== EQ gracza ===")
        for i, item in enumerate(eq):
            print()
            print(f"{i+1}. Nazwa: {item.name}")
            print(f"- Type: {item.type.name}")
            print(f"- Wartosc: {item.value}")
            if item.attacks:
                print("- Ataki: ")
                for i, attack in enumerate(item.attacks):
                    print(f" > {i+1} Nazwa: {attack.name} | DMG: {attack.damage_min} - {attack.damage_max}", end="")
                    if attack.miss_chance > 0.0:
                        print(f" | Miss: {attack.miss_chance}", end="")
                    print()
    else:
        print("\n--- Ekwipunek ---")
        if not eq:
            print(" Pusto")
        else:
            for i, item in enumerate(eq):
                print(f" {i+1}. {item.name} | Wartosc: {item.value}") 


def cmd_show_cmds() -> None:
    print("\n=== lista komend ===\n")
    print("$walka <nazwa_przeciwnika> | symuluje walke z wybranym przeciwnikiem")
    print("$show <hp | eq | state> | wyswietla hp/eq/stan")
    print("$spawn <nazwa:ilosc,nazwa2:ilosc2> | dodaje do eq przedmioty z katalogu lub fallback | domyslna ilosc 1")
    print("$testset | dodaje zestaw roznych itemow do eq")
    print("$create | kreator nowego przedmiotu do item_catalog")


def cmd_show(state: GameState, parts: list[str]) -> None:
    if len(parts) == 1:
        while True:
            user = input("\nCo wyswietlic? (hp | eq | state)\n >> ")
            if user == "eq": parts.append("eq"); break
            elif user == "hp": parts.append("hp"); break
            elif user == "state": parts.append("state"); break
            elif user == "catalog": parts.append("catalog"); break
            else:
                print("Wybierz z podanych")
    if parts[1] == "hp":
        print(f"\n=== HP gracza: {state.hp} ===")
        
    elif parts[1] == "eq":
        show_eq(state.inventory, True)
        
    elif parts[1] == "state":
        print(f"\n=== HP gracza: {state.hp} ===")
        show_eq(state.inventory, True)
    elif parts[1] == "catalog":
        cmd_show_catalog(parts)


def cmd_spawn(state: GameState, parts: list[str]) -> None:
    if len(parts) == 1:
        print("\n=== katalog ===")
        for i, nazwa in enumerate(ITEM_CATALOG):
            print(f"{i+1}. {nazwa}")
        print("\n Sposob uzycia: item,item:ilosc")
        user = input("\n Co chcesz dodac ($$ aby anulowac): ")
        if user == "$$":
            print("anulowano")
            return
    else:
        user = parts[1]

    do_dodania: list[tuple[str, int]] = []
    for wpis in user.split(","):
        czesci = wpis.split(":")
        nazwa = czesci[0].strip()
        ilosc = 1
        if len(czesci) > 1:
            try:
                ilosc = int(czesci[1])
            except ValueError:
                print(f" Zla ilosc dla '{nazwa}', ustawiam 1")
        do_dodania.append((nazwa, ilosc))

    print("\nChcesz dodac:")
    for nazwa, ilosc in do_dodania:
        print(f" Nazwa: {nazwa}, ilosc: {ilosc}")

    user = input("Potwierdzasz ($$ aby anulowac lub enter): ")
    if user == "$$":
        print("anulowano")
        return

    for nazwa, ilosc in do_dodania:
        for _ in range(ilosc):
            state.inventory.append(create_item(nazwa))
        print(f" Dodano: {nazwa} x{ilosc}")


def cmd_walka(state: GameState, parts: list[str]) -> None:
    state.hp = 100
    if len(parts) == 1:                    
        print("\n=== przeciwnicy ===")
        for enemy in ENEMY_CATALOG:
            print(f"{enemy}")
        przeciwnik = input("\nPodaj nazwe przeciwnika (lub $$ aby anulowac): ").lower().strip()
        if przeciwnik == "$$":
            return
    else:                                  
        przeciwnik = parts[1]
    prowadz_walke(state, create_enemy(przeciwnik))

def cmd_testset(state: GameState) -> None:
    print("\n=== dodawanie zestawu testowego ===\n")
    cmd_spawn(state, ["$spawn", "miecz:1,sztylet:1,pochodnia:1,klucz:1"])


def krok_nazwa() -> str | object:
    """Pyta o nazwę przedmiotu."""
    while True:
        user = input("\n Nazwa przedmiotu ($$ anuluj): ").strip()
        if user == "$$":
            return ANULUJ
        if user == "$$$":
            return COFNIJ          # z pierwszego kroku cofnięcie = obsłuży maszyna
        if user:
            return user.lower()
        print(" $ nazwa nie moze byc pusta")


def krok_typ(typy: dict[str, ItemType]) -> ItemType | object:
    """Pyta o typ przedmiotu z dostępnych."""
    while True:
        print("\n Dostepne typy:")
        for nazwa in typy:
            print(f"  - {nazwa}")
        user = input(" Typ ($$ anuluj | $$$ cofnij): ").lower().strip()
        if user == "$$":
            return ANULUJ
        if user == "$$$":
            return COFNIJ
        if user in typy:
            return typy[user]
        print(f" $ '{user}' to niepoprawny typ")


def krok_wartosc() -> int | object:
    """Pyta o wartość przedmiotu."""
    return zapytaj_liczbe("\n Wartosc przedmiotu ($$ anuluj | $$$ cofnij): ")

def zapytaj_jeden_atak() -> Attack | object:
    """Pyta o pola jednego ataku. Zwraca Attack, COFNIJ (przerwij ten atak) albo ANULUJ."""
    nazwa = input("\n  Nazwa ataku (enter=koniec | $$$ cofnij | $$ anuluj): ").strip()
    if nazwa == "$$":
        return ANULUJ
    if nazwa == "$$$":
        return COFNIJ
    if nazwa == "":
        return None               # pusty = koniec dodawania ataków

    dmg_min = zapytaj_liczbe("   dmg min: ")
    if dmg_min is ANULUJ: return ANULUJ
    if dmg_min is COFNIJ: return COFNIJ

    dmg_max = zapytaj_liczbe("   dmg max: ")
    if dmg_max is ANULUJ: return ANULUJ
    if dmg_max is COFNIJ: return COFNIJ

    miss = zapytaj_float("   szansa pudla (0.0-1.0, enter=0): ")
    if miss is ANULUJ: return ANULUJ
    if miss is COFNIJ: return COFNIJ

    return Attack(nazwa.lower(), dmg_min, dmg_max, miss)


def krok_ataki() -> list[Attack] | object:
    """Zbiera ataki w pętli. Zwraca list[Attack], COFNIJ (gdy pusto) albo ANULUJ."""
    ataki: list[Attack] = []
    print("\n === ataki broni ===")
    while True:
        atak = zapytaj_jeden_atak()

        if atak is ANULUJ:
            return ANULUJ
        if atak is COFNIJ:
            if ataki:
                usuniety = ataki.pop()       # usuń ostatni atak
                print(f" $ usunieto atak: {usuniety.name}")
            else:
                return COFNIJ                 # pusto → cofnij do poprzedniego kroku
            continue
        if atak is None:                      # pusty enter = koniec
            return ataki

        ataki.append(atak)
        print(f" $ dodano atak: {atak.name}")

def cmd_create(state: GameState, parts: list[str]) -> None:
    typy = {
        "bron": ItemType.BRON,
        "klucz": ItemType.KLUCZ,
        "narzedzie": ItemType.NARZEDZIE,
        "zuzywalny": ItemType.ZUZYWALNY,
        "nieznany": ItemType.NIEZNANY,
    }

    print("\n === kreator przedmiotu ===")

    # Akumulator zebranych danych
    dane: dict = {}

    # Definicja kroków: (klucz w dane, funkcja pytająca)
    # ataki dodawane warunkowo (tylko dla broni) — obsłużone w pętli
    kroki = ["nazwa", "typ", "wartosc", "ataki"]

    indeks = 0
    while indeks < len(kroki):
        krok = kroki[indeks]

        # Wywołaj odpowiedni krok
        if krok == "nazwa":
            wynik = krok_nazwa()
        elif krok == "typ":
            wynik = krok_typ(typy)
        elif krok == "wartosc":
            wynik = krok_wartosc()
        elif krok == "ataki":
            # ataki tylko dla broni — inaczej pomiń
            if dane.get("typ") != ItemType.BRON:
                dane["ataki"] = []
                indeks += 1
                continue
            wynik = krok_ataki()

        # Obsłuż sygnały nawigacji
        if wynik is ANULUJ:
            print(" $ anulowano tworzenie")
            return
        if wynik is COFNIJ:
            if indeks == 0:
                print(" $ to pierwszy krok, nie mozna cofnac")
                continue                 # zostań na nazwie
            indeks -= 1                  # cofnij do poprzedniego kroku
            continue

        # Zapisz wynik, idź naprzód
        dane[krok] = wynik
        indeks += 1

    # Podgląd
    print("\n === podglad przedmiotu ===")
    print(f" Nazwa: {dane['nazwa']} | Typ: {dane['typ'].name} | Wartosc: {dane['wartosc']}")
    if dane["ataki"]:
        print(" Ataki:")
        for atak in dane["ataki"]:
            print(f"  - {atak.name}: {atak.damage_min}-{atak.damage_max}, miss {atak.miss_chance}")

    # Potwierdzenie
    user = input("\n Potwierdzasz? (enter = zapisz | $$ = anuluj): ").strip().lower()
    if user == "$$":
        print(" $ anulowano")
        return

    # Zbuduj Item ze zebranych danych
    nowy = Item(
        name=dane["nazwa"],
        type=dane["typ"],
        value=dane["wartosc"],
        attacks=dane["ataki"],
    )

    # Dodaj do katalogu (żeby create_item go znał)
    ITEM_CATALOG[dane["nazwa"]] = nowy
    print(f" $ dodano '{dane['nazwa']}' do katalogu")

    # Opcjonalnie do EQ
    user = input(" Dodac do EQ? (tak | enter = nie): ").strip().lower()
    if user == "tak":
        state.inventory.append(create_item(dane["nazwa"]))
        print(f" $ dodano '{dane['nazwa']}' do ekwipunku")

# def cmd_generate(state: GameState, parts: list[str]) -> None:
#     if len(parts) > 1:
#         nowy_przedmiot = generuj_statystyki(parts[1], Usage())


def modify_state(state: GameState):

    print("\n=== tryb modyfikacji ===\n")

    while True:
        user = input("\n >> ").strip().lower()

        if not user:
            continue

        parts = user.split()
        if parts[0] in {"$wyjdz", "$exit", "$$"}:
            print("$ Opuszasz tryb modyfikacji")
            break

        elif parts[0] in {"$komendy", "$"}:
            cmd_show_cmds()
            continue

        elif parts[0] == "$walka":
            cmd_walka(state, parts)
            continue

        elif parts[0] == "$spawn":
            cmd_spawn(state, parts)
            continue
        elif parts[0] == "$testset":
            cmd_testset(state)
            continue

        elif parts[0] == "$create":
            cmd_create(state, parts)
            continue

        elif parts[0] == "$show":
            cmd_show(state, parts)
            continue

        elif parts[0] == "$sethp":
            cmd_set_hp(state, parts)
            continue

        #TEMP
        elif parts[0] == "$bron":
            bron = wybierz_bron(state)
            print(bron)
            akcja = wybierz_akcje(bron)
            print(akcja)

        elif parts[0] == "$gen":
            pass

        else:
            print(f"$ komenda: {user} nie istnieje\n")
            cmd_show_cmds()
            continue
