# Prüfung von Version 1.0.0

Im Repository-Verzeichnis lässt sich die vollständige Python-Suite isoliert mit
uv ausführen. Die zusätzlichen Bibliotheken gehören zur Testumgebung; sie ändern
nicht die Python-Installation von TouchDesigner:

```powershell
uv run --with numpy --with scipy --with pillow --with pytest --with opencv-python-headless python -m unittest discover -s tests
```

Die Kamera-Prüfung erzeugt und verarbeitet eine lokale Videodatei. Sie ersetzt
keine Prüfung einer angeschlossenen Kamera. Der Windows-Symlink-Test wird
übersprungen, wenn der ausführende Benutzer keine Symlinks erstellen darf.

Die lokale Weboberfläche muss für die Browserprüfung bereits durch TouchDesigner
unter `http://127.0.0.1:9991/` gestartet sein. `tools/release_browser_qa.cjs` verwendet
Playwright und einen installierten Chrome-Browser; `NODE_PATH` muss auf die
vorhandene Playwright-Installation zeigen. Der Test öffnet Informationen und
Dialoge und ändert Zoom/Raster. Er startet weder Transport noch LED-Ausgabe.

Die Berichte in `qa/` unterscheiden automatisierte Modelltests, native
TouchDesigner-Prüfungen und Browserprüfungen. Screenshots dokumentieren den
tatsächlich gerenderten Zustand. Physische LED-Farben, Langzeit-Netzlast und
mechanische MK2-Eingaben werden durch diese Softwareprüfung nicht bestätigt.

Die Wiederherstellung der sechs entfernten historischen DATs wurde vor ihrer
Entfernung in einem temporären COMP ausgeführt und inhaltlich verglichen.
`CLEANUP_RECOVERY_DE.md` beschreibt den Rückweg.
