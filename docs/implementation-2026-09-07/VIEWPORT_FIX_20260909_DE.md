# 3D-Ansicht: Drehen und Zoom

Vorheriger Entwurf gesichert als `Backup/Implementation/PixelblazeMapper_20260909_BEFORE_VIEWPORT_FIX.1.toe`, reparierte Version als `PixelblazeMapper_20260909_VIEWPORT_FIXED.1.toe` im selben Ordner. Beide enthalten das neue Panel (203 LEDs) und den Bestand: 2 Objekte, 3947 LEDs. Keine aktive Übernahme.

Ursache: `uvbuttonsright=False` ließ trotz rselect-Callbacks keine rechte Mausbewegung in die UV-Auswertung eingehen. `mousewheel=False`; Zoom war nicht implementiert. Beide Eingaben jetzt aktiviert. Zoom verändert nur den Kameraabstand, nicht Geometrie oder LED-Größe. Grenzen 0.1–20; Reset setzt Zoom auf 1. Ergänzt: VIEW LEFT/RIGHT, ZOOM +/- als Kamera-Schaltflächen.

Bedienung: Rechts gedrückt halten und bewegen dreht die Ansicht. Mausrad zoomt. Linkes Ziehen verändert weiterhin das ausgewählte Objekt! FRAME / RESET VIEW passt die Kamera wieder ein. Die Freigabe für eine aktive Übernahme wird beim bestehenden UI-Neuaufbau aus Sicherheitsgründen auf NO zurückgesetzt.

Verifikation: echte Windows-Mausrad-Eingabe vergrößerte die Ansicht (Zoom 1 -> 1.3225); echter Klick VIEW RIGHT änderte Yaw 25 -> 40 Grad. 64 Unit-Tests bestanden. SHA256 von draft_document und map_active vor/nach identisch. Keine TD-Operatorfehler, Speichern erfolgreich, normale Ausgabe aus. Rechte gehaltene Mausbewegung nicht physisch automatisiert geprüft: das verfügbare Drag-API unterstützt keine Auswahl der Maustaste; Benutzer-Abnahme ausstehend.

Parameterreferenz: https://docs.derivative.ca/Panel_COMP_Panel_Page ; https://docs.derivative.ca/Panel_Value
