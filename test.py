from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Input, RichLog, Static

    
class MrocznyLoch(App):
    """Szkielet gry jako aplikacja TUI."""

    CSS = """
    #narrator { width: 2fr; border: solid #555555; }
    #panel    { width: 1fr; border: solid red; }
    """

    def compose(self) -> ComposeResult:
        """Buduje drzewo widgetow. yield = 'oto kolejny element UI'."""
        yield Header()
        with Horizontal():
            yield RichLog(id="narrator", wrap=True, markup=True)
            yield Static(self._stan(), id="panel")
        yield Input(placeholder="co robisz?")
        yield Footer()

    def _stan(self) -> str:
        return "[bold]HP:[/] 73/100\n\n[bold]Ekwipunek:[/]\n  noz\n  klucz"

    def on_mount(self) -> None:
        """Wywolane, gdy app wystartuje — tu leci genesis."""
        log = self.query_one("#narrator", RichLog)
        log.write("[dim]Ciemnosc. Budzisz sie na zimnej posadzce.[/]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """FRAMEWORK wola TO, gdy gracz nacisnie enter."""
        log = self.query_one("#narrator", RichLog)
        log.write(f"[cyan]> {event.value}[/]")

        # tutaj: ask_narrator(...), handle_response(...)
        log.write("[dim]Narrator odpowiada...[/]")

        event.input.clear()


if __name__ == "__main__":
    MrocznyLoch().run()