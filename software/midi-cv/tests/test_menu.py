from __future__ import annotations

from sam17.ui.menu import Menu


def test_initial_render_shows_root_first_child(lcd):
    Menu(lcd)
    assert "Tune" in lcd.last_message


def test_down_then_enter_descends(lcd):
    menu = Menu(lcd)
    menu.down()  # highlight "Mode"
    leaf = menu.enter()
    assert leaf is None
    assert "standard" in lcd.last_message


def test_back_returns_to_parent(lcd):
    menu = Menu(lcd)
    menu.enter()  # into "Tune"
    menu.back()
    assert "Tune" in lcd.last_message


def test_enter_returns_leaf(lcd):
    menu = Menu(lcd)
    menu.enter()  # into "Tune"
    leaf = menu.enter()  # selects VCO1
    assert leaf is not None
    assert leaf.label == "VCO1"
