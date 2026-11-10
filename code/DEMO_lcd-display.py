
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 480, 320
FRAMEBUFFER = "/dev/fb0"

def draw_screen(counter):
    image = Image.new("RGB", (WIDTH, HEIGHT), (20, 25, 35))
    draw = ImageDraw.Draw(image)

    draw.text((20, 15), "RASPBERRY PI DISPLAY", fill="white")
    draw.rectangle((20, 60, 460, 180), fill=(35, 90, 130))
    draw.text((40, 85), "LCD framebuffer active", fill="white")
    draw.text((40, 125), f"Update: {counter}", fill=(255, 220, 80))
    draw.text((20, 230), time.strftime("%H:%M:%S"), fill="white")

    # Rotate 180 degrees for the assumed upside-down orientation.
    image = image.rotate(180)
    return image

def write_frame(image):
    rgb = np.asarray(image, dtype=np.uint16)

    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    pixels = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)

    with open(FRAMEBUFFER, "r+b", buffering=0) as fb:
        fb.seek(0)
        fb.write(pixels.astype("<u2").tobytes())

counter = 0

while True:
    image = draw_screen(counter)
    write_frame(image)
    counter += 1
    time.sleep(1)
