#!/usr/bin/env python3
# Draws a Christmas tree with twinkling lights on a 50-pixel NeoPixel grid,
# then scrolls it sideways.
#
# Run with: sudo python3 tree_scroll.py [-c] [-s]

import time
import random
import argparse
from rpi_ws281x import PixelStrip, Color

# LED strip configuration (same as strandtest):
LED_COUNT = 50        # Pixels 0-49.
LED_PIN = 18          # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10          # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 128  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False    # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

# Physical layout of the grid: LAYOUT[row][col] is the LED number at that spot,
# or None where there is no LED. Row 0 is the top. The strip snakes back and
# forth, which is why every other row runs backwards.
LAYOUT = [
    [41,   42,   43, 44, 45, 46, 47, 48,   49],
    [40,   39,   38, 37, 36, 35, 34, 33,   32],
    [23,   24,   25, 26, 27, 28, 29, 30,   31],
    [22,   21,   20, 19, 18, 17, 16, 15,   14],
    [5,     6,    7,  8,  9, 10, 11, 12,   13],
    [None, None,  4,  3,  2,  1,  0, None, None],
]
WIDTH = len(LAYOUT[0])
HEIGHT = len(LAYOUT)

# Background color, used for every '.' in a picture. Dark blue night sky.
BACKGROUND = Color(0, 0, 20)
SNOW = Color(60, 60, 60)

# One character per pixel. '.' is the background and '*' is a twinkling light.
PALETTE = {
    '.': BACKGROUND,
    'R': Color(255, 0, 0),
    'G': Color(0, 150, 0),
    'B': Color(0, 0, 255),
    'Y': Color(255, 180, 0),
    'T': Color(100, 40, 0),     # Brown trunk
    'W': Color(255, 255, 255),
}

# Colors a '*' light picks from at random on every frame.
LIGHT_COLORS = [
    Color(255, 0, 0),
    Color(0, 0, 255),
    Color(255, 180, 0),
    Color(255, 0, 180),
    Color(255, 255, 255),
]

# The picture, drawn the same way it looks in the spreadsheet.
TREE = [
    "....Y....",
    "...G*G...",
    "..GG*GG..",
    ".G*GGG*G.",
    "GGG*GG*GG",
    "....T....",
]


class Snowfall:
    """A few snowflakes drifting down the background, behind the picture."""

    def __init__(self, flakes=4):
        self.flakes = [[random.randrange(HEIGHT), random.randrange(WIDTH)]
                       for _ in range(flakes)]

    def step(self):
        for flake in self.flakes:
            flake[0] += 1
            if flake[0] >= HEIGHT:
                flake[0] = 0
                flake[1] = random.randrange(WIDTH)

    def covers(self, row, col):
        return [row, col] in self.flakes


def draw(strip, image, offset=0, snow=None):
    """Show the WIDTH-wide window of image starting at column offset.

    The image wraps around, so any offset works and the picture can be wider
    than the grid.
    """
    image_width = len(image[0])
    for row in range(HEIGHT):
        for col in range(WIDTH):
            led = LAYOUT[row][col]
            if led is None:
                continue
            ch = image[row][(col + offset) % image_width]
            if ch == '*':
                color = random.choice(LIGHT_COLORS)
            elif ch == '.' and snow and snow.covers(row, col):
                color = SNOW
            else:
                color = PALETTE[ch]
            strip.setPixelColor(led, color)
    strip.show()


def hold(strip, image, seconds=3, wait_ms=400, snow=None):
    """Show image standing still, letting the lights twinkle and snow fall."""
    for _ in range(int(seconds * 1000 / wait_ms)):
        draw(strip, image, snow=snow)
        if snow:
            snow.step()
        time.sleep(wait_ms / 1000.0)


def scroll(strip, image, wait_ms=150, gap=3, loops=1, snow=None):
    """Scroll image right-to-left across the grid.

    gap adds blank columns after the image so it fully leaves the grid
    before it comes back around.
    """
    padded = [line + '.' * gap for line in image]
    for _ in range(loops):
        for offset in range(len(padded[0])):
            draw(strip, padded, offset, snow)
            if snow:
                snow.step()
            time.sleep(wait_ms / 1000.0)


def clear(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, 0)
    strip.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    parser.add_argument('-s', '--snow', action='store_true', help='add falling snow to the background')
    args = parser.parse_args()

    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    snow = Snowfall() if args.snow else None

    print('Press Ctrl-C to quit.')
    try:
        while True:
            hold(strip, TREE, snow=snow)       # Show the tree standing still...
            scroll(strip, TREE, snow=snow)     # ...then scroll it off and back on.
    except KeyboardInterrupt:
        if args.clear:
            clear(strip)
