# Status: GICO-Kameratest

Stand: 12.09.2026. Teilaufgabe 1, Agent `gico_camera_test`.

- Pure Bildnummer-Codierung, 24-Universen-Paketerzeugung und konservative
  Auswertung implementiert.
- Aufnahmeprotokoll 15/25/30 FPS mit Kalibriersequenz vorbereitet.
- Kommando zum Offline-Vorbereiten und expliziten Start implementiert; Start
  prüft TD-Ausgabe aus und verwendet den vorhandenen separaten Senderworker.
- Video-Kalibrierung mit Panel-Rechtecken und nummeriertem Kontrollbild,
  Frame-Zeitstempelauswertung, CRC-/Helligkeitsprüfung und CSV-Nachweis vorhanden.
- Deutsche Bedienungs- und Aufnahmeanleitung: `ANLEITUNG_DE.md`.
- Keine Hardwareausgabe, kein TD-Zugriff, keine Controllerkonfiguration und keine
  Firmwareänderung durch diesen Agenten gestartet.

Validierung abgeschlossen: **16 Tests bestanden in 23,786 Sekunden**.

- Alle 4.096 Bildnummern korrekt hin und zurück codiert; sämtliche 86.016
  möglichen einzelnen Bitfehler einschließlich Referenzbit erkannt.
- Paketadressen, reservierte schwarze Bereiche, ArtDmx-Header und Helligkeits-
  grenzen geprüft.
- Fehlende optische IDs, falsche einzelne Codes, Zählerüberlauf, unerwartete
  Rücksprünge, lange gehaltene Bilder und ungültige Zeitstempel geprüft.
- Vollständiges synthetisches MJPG-Video mit drei Panels und 120 Kamera-FPS
  geschrieben und wieder eingelesen. Automatische Marker-Kalibrierung und
  anschließende Auswertung erkennen die simulierten 15/25/30 FPS innerhalb
  0,25 FPS, ohne fehlende IDs oder unterschiedliche Panelnummern. Dabei werden
  echte Decoder-Präsentationszeitstempel verwendet, keine Frameindex-FPS-Rechnung.
- Sendergrenze isoliert getestet: fehlgeschlagene TD-off-Prüfung konstruiert
  keinen Worker; ein Einreichungsfehler schließt den Worker und protokolliert
  den Fehler. Diese Tests verwenden ausschließlich Mocks.
- Offline-Plan tatsächlich erzeugt: `offline-plan/plan.json`. Kein Socket und
  kein TD-Aufruf bei diesem `prepare`-Kommando.

Testkommando:

```powershell
& 'C:/Users/jbhtz/AppData/Roaming/uv/tools/marimapper/Scripts/python.exe' -m unittest tests.test_gico_camera_benchmark tests.test_gico_camera_video tests.test_gico_camera_sender
```

Bereitschaft: Software und Aufnahmeablauf sind für einen beaufsichtigten echten
Durchlauf vorbereitet. Live-Erprobung und reale Videokalibrierung bleiben offen.
Offen für die Hardwaremessung: ungeschnittenes Originalvideo eines echten
Durchlaufs mit bekannter Aufnahme-/Zeitlupenzeitbasis. Vorhandene Offline-Tests
können keine realen GICO-Ausgabe-FPS bestätigen.

Headerkorrektur nach Integrationsreview: Der Kamerasender verwendet wie der
bestehende native GICO-Pfad dauerhaft ArtDmx-Sequenz 0. Optische Bildnummern
bleiben im Gray-/CRC-Payload. Der Test prüft zwei aufeinanderfolgende Batches
mit jeweils 24 Sequenz-0-Paketen und den entsprechenden Logeintrag.


## Erster optischer Aufnahmelauf ausgeführt

`measurements/gico-camera-001`: Benutzer filmt das untere Panel mit angegebenen 60 Kamera-FPS. Lauf vollständig beendet, alle 5.030 Batches / 120.720 ArtDmx-Pakete ohne gemeldete Sendefehler oder Worker-Drops gesendet; abschließend 48 Schwarzpakete und Worker beendet. Rohphasen, Einreichungszeitpunkte und Bedienkontext gespeichert. Originalvideo und Identifikation des gefilmten Panels stehen noch aus. 60 Kamera-FPS erlauben bei 30 LED-FPS nur etwa zwei Abtastungen pro Zustand; dies ist zunächst eine orientierende Messung, kein Nachweis stabiler optischer 30 FPS.

WhatsApp-Vorprüfung: 576×1024, knapp 60 FPS, 244,013 s. Kalibrierpunkte erkennbar, aber kurze Decoderstichproben zu 96–100 % uneindeutig; keine belastbare LED-FPS-Zahl. Nach Abgleich zweier Schwarzpausen fehlen in dieser Datei ungefähr 33 s des letzten Messabschnitts. Originaldatei angekündigt; vor erneutem Test zunächst diese prüfen. Belege: `measurements/gico-camera-001-whatsapp-review/BEWERTUNG_DE.md`.
