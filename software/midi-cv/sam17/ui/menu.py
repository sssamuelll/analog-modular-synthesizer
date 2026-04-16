"""Hierarchical menu rendered on the 16x2 LCD.

The original thesis menu has three top-level entries (`Tune`, `Mode`,
`Help`); each opens a submenu navigated with the four hardware buttons.
This module owns the UI state and exposes callbacks the button driver can
wire to.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sam17.hardware.lcd import Lcd


@dataclass
class MenuNode:
    label: str
    children: list[MenuNode] = field(default_factory=list)


def default_menu() -> MenuNode:
    mode_names = ("standard", "tune", "glide", "arp", "step seq")
    help_entries = ("Documentation", "Guide", "Update", "About")
    return MenuNode(
        label="root",
        children=[
            MenuNode("Tune", [MenuNode("VCO1"), MenuNode("VCO2"), MenuNode("VCO3")]),
            MenuNode("Mode", [MenuNode(name) for name in mode_names]),
            MenuNode("Help", [MenuNode(name) for name in help_entries]),
        ],
    )


class Menu:
    def __init__(self, lcd: Lcd, root: MenuNode | None = None) -> None:
        self._lcd = lcd
        self._stack: list[tuple[MenuNode, int]] = [(root or default_menu(), 0)]
        self.refresh()

    @property
    def current(self) -> MenuNode:
        node, index = self._stack[-1]
        return node.children[index] if node.children else node

    def up(self) -> None:
        node, index = self._stack[-1]
        if node.children:
            self._stack[-1] = (node, (index - 1) % len(node.children))
        self.refresh()

    def down(self) -> None:
        node, index = self._stack[-1]
        if node.children:
            self._stack[-1] = (node, (index + 1) % len(node.children))
        self.refresh()

    def enter(self) -> MenuNode | None:
        """Descend into the highlighted child, or return it if it's a leaf."""
        node, index = self._stack[-1]
        if not node.children:
            return node
        child = node.children[index]
        if child.children:
            self._stack.append((child, 0))
            self.refresh()
            return None
        return child

    def back(self) -> None:
        if len(self._stack) > 1:
            self._stack.pop()
            self.refresh()

    def refresh(self) -> None:
        node, index = self._stack[-1]
        title = node.label
        selection = node.children[index].label if node.children else "(leaf)"
        self._lcd.print(f"{title}\n> {selection}")
