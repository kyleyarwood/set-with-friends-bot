import re, sys
from playwright.sync_api import Playwright, sync_playwright, expect
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional
import cProfile
import pstats
import time

class Shape(Enum):
    DIAMOND = "#diamond"
    SQUIGGLE = "#squiggle"
    OVAL = "#oval"

class Colour(Enum):
    RED = "#ff0101"
    GREEN = "#008002"
    PURPLE = "#800080"

class Number(Enum):
    ONE = 1
    TWO = 2
    THREE = 3

class Fill(Enum):
    EMPTY = auto()
    LINES = auto()
    FILLED = auto()

@dataclass
class Tile:
    SHAPE: Shape
    COLOUR: Colour
    NUMBER: int
    FILL: Fill
    element: Optional[Any]

    def to_tuple(self):
        return (self.SHAPE.value, self.COLOUR, self.NUMBER, self.FILL)

    def click(self):
        start = time.time()
        print(start, "CLICKING")
        self.element.click()
        end = time.time()
        print(end, "CLICKED", end - start)

def convert_to_tile(tile_element):
    global is_multiplayer
    if is_multiplayer:
        num = 29
    else:
        num = 45
    individual_elements = tile_element.query_selector_all(f".jss{num}")
    number = Number(len(individual_elements))
    details = individual_elements[0].query_selector_all("use")
    shape = Shape(details[0].get_attribute("href"))
    colour = Colour(details[1].get_attribute("stroke"))
    if details[0].get_attribute("fill") == "transparent":
        fill = Fill.EMPTY
    elif details[0].get_attribute("mask"):
        fill = Fill.LINES
    else:
        fill = Fill.FILLED
    return Tile(SHAPE=shape, NUMBER=number, COLOUR=colour, FILL=fill, element=tile_element)


def third_in_set(tile1, tile2):
    res = Tile(SHAPE=Shape.DIAMOND, COLOUR=Colour.RED, NUMBER=1, FILL=Fill.EMPTY, element=None)
    for attribute in ("SHAPE", "COLOUR", "NUMBER", "FILL"):
        attr1 = getattr(tile1, attribute)
        attr2 = getattr(tile2, attribute)
        if attr1 == attr2:
            setattr(res, attribute, attr1)
        else:
            for x in type(attr1):
                if x != attr1 and x != attr2:
                    setattr(res, attribute, x)
                    break
    return res

def click_on_set(tiles):
    tile_map = {tile.to_tuple(): tile for tile in tiles}
    for i,tile1 in enumerate(tiles):
        for j,tile2 in enumerate(tiles[i+1:]):
            tile3 = third_in_set(tile1, tile2)
            if tile3.to_tuple() not in tile_map:
                continue
            tile3 = tile_map.get(tile3.to_tuple())
            for tile in (tile1, tile2, tile3):
                tile.click()
            break
        else:
            continue
        break

def run(playwright: Playwright) -> None:
    global is_multiplayer
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    if len(sys.argv) > 1:
        page.goto(sys.argv[1])
        page.get_by_role("button", name="Enter").click()  
    else:
        page.goto("https://setwithfriends.com/")
        page.get_by_role("button", name="Enter").click()
        page.get_by_label("Create a new private game.").click()
        page.get_by_label("Make sure everyone is in the").click()
    while True:
        num = 47
        if is_multiplayer:
            num = 31
        time.sleep(0.3) # actually makes it faster waiting for the page to render believe it or not
        tile_elements = page.query_selector_all(f".jss{num}")
        tiles = [convert_to_tile(tile_element) for tile_element in tile_elements]
        click_on_set(tiles)
    context.close()
    browser.close()

with cProfile.Profile() as pr:
    is_multiplayer = len(sys.argv) > 1
    with sync_playwright() as playwright:
        run(playwright)

