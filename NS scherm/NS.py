import tkinter as tk
from PIL import Image, ImageTk, ImageOps
from pathlib import Path
import subprocess
import time
import os
import sys


# ============================================================
# INSTELLINGEN
# ============================================================

# Resolutie van het scherm
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440


# ------------------------------------------------------------
# TIJDEN
# ------------------------------------------------------------

# Hoe lang het NS-scherm zichtbaar blijft
NS_TIME = 10

# Hoe lang iedere afbeelding zichtbaar blijft
IMAGE_TIME = 5


# ------------------------------------------------------------
# AFBEELDINGEN
# ------------------------------------------------------------

# Hoeveel afbeeldingen maximaal achter elkaar?
#
# Bijvoorbeeld:
# 3 = na iedere 3 afbeeldingen terug naar NS
# 5 = na iedere 5 afbeeldingen terug naar NS
# 10 = na iedere 10 afbeeldingen terug naar NS
#
# ============================================================
# AANTAL AFBEELDINGEN PER BLOK
# ============================================================

BLOCKS = [3, 6]

# ------------------------------------------------------------
# MAP MET AFBEELDINGEN
# ------------------------------------------------------------

IMAGE_FOLDER = Path(r"C:\Users\Niels\Pictures\NSTest\afbeeldingen")


# ------------------------------------------------------------
# NS URL
# ------------------------------------------------------------

NS_URL = (
    "https://www.ns.nl/reisinformatie/externe-schermen/treinen/"
    "vertrektijden?stationId=DT&columns=2&rows=7&header=Delft"
    "&footer=&clock=true&headerLogo=true&footerLogo=false"
)


# ------------------------------------------------------------
# MOGELIJKE CHROME LOCATIES
# ------------------------------------------------------------

CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


# ============================================================
# CHROME VINDEN
# ============================================================

def find_chrome():

    for path in CHROME_PATHS:

        if os.path.exists(path):
            return path

    print("ERROR: Google Chrome kon niet worden gevonden.")

    sys.exit(1)


# ============================================================
# CHROME STARTEN
# ============================================================

def start_chrome():

    chrome = find_chrome()

    print("Chrome starten...")

    subprocess.Popen([
        chrome,
        "--kiosk",
        "--disable-infobars",
        "--disable-session-crashed-bubble",
        "--disable-features=Translate",
        "--noerrdialogs",
        NS_URL
    ])

    print(
        "Wachten totdat de NS-pagina geladen is..."
    )

    time.sleep(8)


# ============================================================
# AFBEELDINGEN VINDEN
# ============================================================

def get_images():

    IMAGE_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    images = []

    for file in IMAGE_FOLDER.iterdir():

        if file.is_file():

            if file.suffix.lower() in allowed_extensions:
                images.append(file)

    # Alfabetisch sorteren
    images.sort(
        key=lambda x: x.name.lower()
    )

    # Dubbelen verwijderen
    unique_images = []

    seen = set()

    for image in images:

        full_path = str(
            image.resolve()
        ).lower()

        if full_path not in seen:

            seen.add(full_path)

            unique_images.append(image)

    return unique_images


# ============================================================
# FULLSCREEN OVERLAY
# ============================================================

class ImageOverlay:

    def __init__(self):

        self.root = tk.Tk()

        # Geen Windows-rand
        self.root.overrideredirect(True)

        # Altijd boven Chrome
        self.root.attributes(
            "-topmost",
            True
        )

        # Exact schermformaat
        self.root.geometry(
            f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}+0+0"
        )

        # Zwarte achtergrond
        self.root.configure(
            bg="black"
        )

        # Label voor afbeelding
        self.label = tk.Label(
            self.root,
            bg="black"
        )

        self.label.pack(
            fill="both",
            expand=True
        )

        # ESC = afsluiten
        self.root.bind(
            "<Escape>",
            self.exit_program
        )

        self.current_image = None

        # Start verborgen
        self.root.withdraw()

        self.root.update()

    # ========================================================
    # OVERLAY TONEN
    # ========================================================

    def show(self):

        self.root.deiconify()

        self.root.lift()

        self.root.attributes(
            "-topmost",
            True
        )

        self.root.focus_force()

        self.root.update()

    # ========================================================
    # OVERLAY VERBERGEN
    # ========================================================

    def hide(self):

        self.root.withdraw()

        self.root.update()

    # ========================================================
    # AFBEELDING TONEN
    # ========================================================

    def show_image(self, filename):

        try:

            print(
                f"Afbeelding tonen: {filename.name}"
            )

            image = Image.open(filename)

            # EXIF-rotatie corrigeren
            image = ImageOps.exif_transpose(
                image
            )

            # RGB
            if image.mode not in (
                "RGB",
                "RGBA"
            ):
                image = image.convert(
                    "RGB"
                )

            # ------------------------------------------------
            # AFBEELDING SCHERMVULLEND MAKEN
            # ------------------------------------------------

            image = ImageOps.fit(
                image,
                (
                    SCREEN_WIDTH,
                    SCREEN_HEIGHT
                ),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5)
            )

            # Tkinter afbeelding
            self.current_image = ImageTk.PhotoImage(
                image
            )

            # Alleen de inhoud vervangen.
            #
            # Het venster zelf blijft zichtbaar.
            self.label.configure(
                image=self.current_image
            )

            self.root.update()

        except Exception as e:

            print(
                f"Fout bij afbeelding "
                f"{filename}: {e}"
            )

    # ========================================================
    # PROGRAMMA AFSLUITEN
    # ========================================================

    def exit_program(self, event=None):

        print(
            "Programma afsluiten..."
        )

        self.root.destroy()

        sys.exit(0)


# ============================================================
# HOOFDPROGRAMMA
# ============================================================

def main():

    print()
    print("==============================")
    print("      NS INFORMATIESCHERM")
    print("==============================")
    print()

    print(
        f"NS-tijd: {NS_TIME} seconden"
    )

    print(
        f"Afbeelding-tijd: {IMAGE_TIME} seconden"
    )


    print()

    # --------------------------------------------------------
    # CHROME STARTEN
    # --------------------------------------------------------

    start_chrome()

    # --------------------------------------------------------
    # OVERLAY MAKEN
    # --------------------------------------------------------

    overlay = ImageOverlay()

    # --------------------------------------------------------
    # ONEINDIGE LOOP
    # --------------------------------------------------------

    while True:

        # ====================================================
        # AFBEELDINGEN OPNIEUW INLADEN
        # ====================================================

        images = get_images()

        print()
        print(
            f"{len(images)} afbeeldingen gevonden."
        )

        # Geen afbeeldingen
        if not images:

            print(
                "Geen afbeeldingen gevonden."
            )

            overlay.hide()

            time.sleep(NS_TIME)

            continue


        # ====================================================
        # EERST NS-SCHERM
        # ====================================================

        print()
        print(
            f"NS-scherm "
            f"({NS_TIME} seconden)"
        )

        overlay.hide()

        time.sleep(NS_TIME)


        # ====================================================
        # AFBEELDINGEN IN AANGEGEVEN BLOKKEN TONEN
        # ====================================================

        image_index = 0
        block_index = 0

        while image_index < len(images):

            # Bepaal hoeveel afbeeldingen dit blok bevat
            aantal_in_blok = BLOCKS[
                block_index % len(BLOCKS)
            ]

            print()
            print(
                f"Blok {block_index + 1}: "
                f"{aantal_in_blok} afbeeldingen"
            )

            # ------------------------------------------------
            # NS-SCHERM VERBERGEN
            # ------------------------------------------------

            overlay.show()

            # ------------------------------------------------
            # AFBEELDINGEN VAN DIT BLOK
            # ------------------------------------------------

            for i in range(aantal_in_blok):

                # Zijn alle afbeeldingen al geweest?
                if image_index >= len(images):
                    break

                image = images[image_index]

                overlay.show_image(image)

                time.sleep(IMAGE_TIME)

                image_index += 1

            # ------------------------------------------------
            # ZIJN ER NOG AFBEELDINGEN?
            # ------------------------------------------------

            if image_index < len(images):

                print(
                    "Blok klaar → NS-scherm"
                )

                overlay.hide()

                time.sleep(NS_TIME)

            block_index += 1


            # ====================================================
            # ALLE AFBEELDINGEN GEWEEST
            # ====================================================

            print()
            print(
                "Alle afbeeldingen zijn geweest."
            )

            print(
                "Cyclus opnieuw starten."
            )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\nProgramma gestopt."
        )