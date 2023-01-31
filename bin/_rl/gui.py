from typing import Tuple

from urwid import (RIGHT, BoxAdapter, Columns, CompositeCanvas, Filler, Frame,
                   LineBox, MainLoop, MonitoredFocusList, Padding, Pile,
                   SolidFill, Terminal, Text, Widget, WidgetContainerMixin,
                   WidgetWrap, Divider)
import urwid


class SplitContainer(WidgetContainerMixin, WidgetWrap):

    _first_body: Widget
    _second_body: Widget
    _ratio: float

    _focused_widget: Widget
    _contents: MonitoredFocusList

    def __init__(
        self, first_body: Widget, second_body: Widget, ratio: float = 2.0
    ):
        self._first_body = first_body
        self._second_body = second_body
        self._ratio = ratio
        body = Filler(Columns([
            self._first_body,
            self._second_body
        ]))
        self._focused_widget = (
            self._first_body
            if self._first_body.selectable()
            else self._second_body
            if self._second_body.selectable()
            else None
        )
        super(WidgetWrap, self).__init__(body)

    def _is_horizontal(self, size: Tuple[int]) -> bool:
        cols, rows = size
        return cols > rows * self._ratio

    def render(self, size: Tuple[int], focus: bool = False) -> CompositeCanvas:
        container_type = Columns if self._is_horizontal(size) else Pile
        self._w = Filler(container_type([
            self._first_body, self._second_body
        ]))
        return super(WidgetWrap, self).render(size, focus)

    def options(self) -> None:
        return None

    @property
    def focus(self) -> Widget:
        return self._focused_widget

    @property
    def focus_position(self) -> str:
        if self._focused_widget == self._first_body:
            return 'first'
        elif self._focused_widget == self._second_body:
            return 'second'
        else:
            return None

    @focus_position.setter
    def focus_position(self, value: str):
        if value == 'first':
            self._focused_widget = self._first_body
        elif value == 'second':
            self._focused_widget = self._second_body
        else:
            raise IndexError()

    @property
    def contents(self):
        ...


class Gui:

    urwid.set_encoding("utf8")

    _mainframe: Frame

    _id_ip_text: Text
    _time_text: Text

    _gateway_text: Text
    _running_text: Text
    _cronjob_text: Text
    _on_pi_text: Text
    _update_text: Text

    _terminal: Terminal

    def __init__(self):
        self._mainframe = self._build_mainframe()
        loop = MainLoop(self._mainframe)
        self._terminal.main_loop = loop
        loop.run()

    def _build_header(self) -> Columns:
        self._id_ip_text = Text("master@192.168.1.10")
        self._time_text = Text("13:37:42", align=RIGHT)
        return Columns([
            self._id_ip_text,
            self._time_text
        ])

    def _build_footer(self) -> Columns:
        self._gateway_text = Text("Gateway: 192.168.1.1")
        self._running_text = Text(" 🟢 ", align=RIGHT)
        self._cronjob_text = Text(" 🕒 ", align=RIGHT)
        self._on_pi_text = Text(" π ", align=RIGHT)
        self._update_text = Text(" 🗘 ", align=RIGHT)
        return Columns([
            ('pack', self._gateway_text),
            Padding(BoxAdapter(SolidFill(), 1)),
            ('pack', self._running_text),
            ('pack', self._cronjob_text),
            ('pack', self._on_pi_text),
            ('pack', self._update_text)
        ])

    def _build_mainframe(self) -> Frame:
        self._terminal = Terminal(None)
        return Frame(
            header=self._build_header(),
            body=Filler(Columns(
                [
                    LineBox(Pile([
                       Text("A"),
                       Text("B")
                    ])),
                    LineBox(self._terminal)
                ],
                box_columns=[1]
            )),
            footer=self._build_footer()
        )


def main():
    gui = Gui()


if __name__ == "__main__":
    main()
