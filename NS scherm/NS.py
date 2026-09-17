```python
import tkinter as tk
import time
import subprocess
from pathlib import Path

from PIL import Image, ImageTk, ImageOps
from screeninfo import get_monitors


# ============================================================
# INSTELLINGEN
# ============================================================

# Monitor:
# 0 = hoofdmonitor
# 1 = tweede monitor
# 2 = derde monitor, enz.
MONITOR_INDEX = 1

# Tijd dat het NS-scherm zichtbaar is
NS_TIME = 10

# Tijd dat iedere afbeelding zichtbaar is
IMAGE_TIME = 5

# Aantal afbeeldingen per blok
# Voorbeeld:
# [3, 6] = eerst 3 afbeeldingen, daarna NS,
#          daarna 6 afbeeldingen, daarna NS, enz.
BLOCKS = [3, 6]

# Map met afbeeldingen
IMAGE_FOLDER = Path(
    r"C:\Users\Niels\Pictures\NSTest\afbeeldingen"
)

# NS externe scherm
NS_URL = (
    "https://www.ns.nl/reisinformatie/externe-schermen/treinen/"
    "vertrektijden?stationId=DT&columns=2&rows=7&header=Delft"
    "&footer=&clock=true&headerLogo=true&footerLogo=false"
)


# ============================================================
# MONITOR INSTELLEN
# ============================================================

monitors = get_monitors()

if len(monitors) <= MONITOR_INDEX:
    print("FOUT: de gekozen monitor bestaat niet.")
    print(f"Er zijn {len(monitors)} monitor(en) gevonden.")
    input("Druk op Enter om af te sluiten...")
    exit()

monitor = monitors[MONITOR_INDEX]

SCREEN_X = monitor.x
SCREEN_Y = monitor.y
SCREEN_WIDTH = monitor.width
SCREEN_HEIGHT = monitor.height

print("----------------------------------------")
print("Geselecteerde monitor:")
print(f"Monitor index : {MONITOR_INDEX}")
print(f"Resolutie    : {SCREEN_WIDTH} x {SCREEN_HEIGHT}")
print(f"Positie      : X={SCREEN_X}, Y={SCREEN_Y}")
print("----------------------------------------")


# ============================================================
# AFBEELDINGEN INLEZEN
# ============================================================

def get_images():
    """Zoek alle afbeeldingen in de ingestelde map."""

    if not IMAGE_FOLDER.exists():
        print(f"FOUT: map bestaat niet:")
        print(IMAGE_FOLDER)
        return []

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".webp"
    }

    images = []

    for file in IMAGE_FOLDER.iterdir():
        if file.is_file() and file.suffix.lower() in allowed_extensions:
            images.append(file)

    # Alfabetisch sorteren
    images.sort(key=lambda x: x.name.lower())

    return images


# ============================================================
# CHROME STARTEN
# ============================================================

def find_chrome():
    """Zoek Chrome op de computer."""

    possible_paths = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return None


def start_chrome():
    """Start Chrome in kiosk mode."""

    chrome = find_chrome()

    if chrome is None:
        print("FOUT: Chrome kon niet worden gevonden.")
        return None

    print("Chrome starten...")

    process = subprocess.Popen([
        str(chrome),
        "--kiosk",
        "--disable-infobars",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        NS_URL
    ])

    # Even wachten totdat Chrome geopend is
    time.sleep(5)

    return process


# ============================================================
# AFBEELDING OVERLAY
# ============================================================

class ImageOverlay:

    def __init__(self):

        self.root = tk.Tk()

        # Geen titelbalk / randen
        self.root.overrideredirect(True)

        # Altijd boven Chrome
        self.root.attributes("-topmost", True)

        self.root.configure(bg="black")

        # Precies de positie en resolutie van monitor 2
        self.root.geometry(
            f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}"
            f"+{SCREEN_X}+{SCREEN_Y}"
        )

        self.label = tk.Label(
            self.root,
            bg="black"
        )

        self.label.pack(
            fill="both",
            expand=True
        )

        # Overlay aanvankelijk verborgen
        self.root.withdraw()

        # ESC = programma afsluiten
        self.root.bind(
            "<Escape>",
            lambda event: self.root.destroy()
        )

    def show_image(self, image_path):

        try:

            print(f"Afbeelding tonen: {image_path.name}")

            img = Image.open(image_path)

            # EXIF-rotatie corrigeren
            img = ImageOps.exif_transpose(img)

            # Afbeelding schermvullend maken
            # Hierbij kan een klein gedeelte van de afbeelding
            # aan de zijkanten/bovenkant worden afgesneden.
            img = ImageOps.fit(
                img,
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5)
            )

            photo = ImageTk.PhotoImage(img)

            self.label.configure(
                image=photo
            )

            # Belangrijk: referentie bewaren zodat Python
            # de afbeelding niet uit het geheugen verwijdert.
            self.label.image = photo

            # Overlay tonen
            self.root.deiconify()

            # Tkinter direct laten tekenen
            self.root.update()

        except Exception as e:

            print("FOUT bij openen afbeelding:")
            print(image_path)
            print(e)

    def hide(self):

        self.root.withdraw()
        self.root.update()


# ============================================================
# HOOFDPROGRAMMA
# ============================================================

def main():

    print("")
    print("========================================")
    print("      NS DIGITAAL SCHERM")
    print("========================================")

    print("")
    print("Afbeeldingen zoeken...")

    images = get_images()

    print(f"{len(images)} afbeeldingen gevonden.")

    for image in images:
        print(f"  - {image.name}")

    if len(images) == 0:
        print("")
        print("WAARSCHUWING: er zijn geen afbeeldingen gevonden.")

    print("")
    print("Chrome starten...")

    chrome_process = start_chrome()

    if chrome_process is None:
        input("Druk op Enter om af te sluiten...")
        return

    # Overlay maken
    overlay = ImageOverlay()

    try:

        while True:

            # Opnieuw afbeeldingen inlezen.
            # Hierdoor kun je tijdens het draaien eventueel
            # afbeeldingen toevoegen/verwijderen.
            images = get_images()

            print("")
            print("----------------------------------------")
            print(f"{len(images)} afbeeldingen gevonden.")
            print("----------------------------------------")

            if len(images) == 0:

                overlay.hide()

                print(f"NS-scherm ({NS_TIME} seconden)")

                time.sleep(NS_TIME)

                continue

            # ================================================
            # NS-SCHERM
            # ================================================

            overlay.hide()

            print("")
            print(f"NS-scherm ({NS_TIME} seconden)")

            time.sleep(NS_TIME)

            # ================================================
            # AFBEELDINGEN
            # ================================================

            image_index = 0
            block_index = 0

            while image_index < len(images):

                # Bepaal hoeveel afbeeldingen dit blok bevat
                aantal_in_blok = BLOCKS[
                    block_index % len(BLOCKS)
                ]

                print("")
                print(
                    f"Blok {block_index + 1}: "
                    f"{aantal_in_blok} afbeeldingen"
                )

                # Overlay tonen VOOR het hele blok
                # Hierdoor verschijnt het NS-scherm niet
                # tussen de afzonderlijke afbeeldingen.
                overlay.root.deiconify()
                overlay.root.update()

                # Zoveel afbeeldingen tonen als dit blok voorschrijft
                for _ in range(aantal_in_blok):

                    if image_index >= len(images):
                        break

                    image = images[image_index]

                    overlay.show_image(image)

                    time.sleep(IMAGE_TIME)

                    image_index += 1

                block_index += 1

                # ============================================
                # TERUG NAAR NS
                # ============================================

                if image_index < len(images):

                    overlay.hide()

                    print("")
                    print(
                        f"Terug naar NS-scherm "
                        f"({NS_TIME} seconden)"
                    )

                    time.sleep(NS_TIME)

            # Na alle afbeeldingen begint de cyclus opnieuw.


    except KeyboardInterrupt:

        print("")
        print("Programma gestopt.")

    except tk.TclError:

        print("")
        print("Overlay gesloten.")

    finally:

        try:
            overlay.root.destroy()
        except:
            pass

        print("Programma afgesloten.")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
```
