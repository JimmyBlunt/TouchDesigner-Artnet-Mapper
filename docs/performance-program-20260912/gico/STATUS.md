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
