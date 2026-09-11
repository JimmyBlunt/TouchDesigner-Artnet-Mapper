# Bestätigtes LED-Flackern beim internen Controller-Test

Der Benutzer bestätigt ausdrücklich: Die LEDs blitzen mit bloßem Auge auf. Das neue Video zeigt den **internen Test im Webmenü von Controller 249**, nicht einen TouchDesigner-Test. Die frühere Erklärung des kleinen türkisfarbenen Reflexes im ersten Video erklärt dieses reale Flackern nicht.

Original: 1117 Frames, 464 × 832, ca. 59,962 Bilder/s, 18,628 s; Quelle und SHA-256 in `source.json`. Die Übersicht und `flash-details.jpg` bestehen aus unveränderten Video-Einzelbildern, lediglich für die Übersicht verkleinert und mit Zeit/Frame beschriftet. Einzelne Originalframes sind als PNG erhalten.

## Beobachtung und Eingrenzung

- Um 4,89–4,99 s zeigen mehrere Stellen zugleich unterschiedliche Farben. Um 16,04–16,18 s wechseln größere Teile in sehr kurzer Folge von blau zu rot, grün und wieder blau; die Helligkeit verändert sich deutlich. Nicht jeder Farbwechsel ist ohne Test-Sollkurve als Fehler klassifizierbar; die schnellen zusätzlichen Blitze und der direkte Augenzeugenbericht sind ernst zu nehmen.
- Eine bestimmte defekte LED oder eine feste Grenze in der Datenkette kann aus der bewegten Kameraaufnahme nicht bestimmt werden. Es ist insbesondere nicht belegt, dass jeweils genau die nächste LED betroffen ist.
- Der interne Test erzeugt seine Daten im Controller. Das Problem ist damit außerhalb des MariMapper-Scanablaufs reproduzierbar. Scan-Paketabstand und Scan-LED-Timing sind keine notwendige Voraussetzung für dieses Fehlerbild. Controller-Firmware, die elektrische Signalerzeugung, Verkabelung, LED-Elektronik und Stromversorgung bleiben Kandidaten.
- Beim aktuellen Auslesen waren TouchDesigner-Sender und Scan aus. Controller-Teststatus: `active:false`, `phase:stopped`, `outputId:3` (Ausgang 4). Die Controller-Konfiguration passt zu 810 LEDs an GPIO14/U133. Diese späteren Statuswerte dokumentieren nicht jeden Zustand während der Videoaufnahme.

## Plausible Ursachen, noch unbewiesen

1. Störungen auf Datenleitung oder Masseverbindung; Kontakt-/Lötstellen; ungeeigneter Signalpegel. Das kann falsche Farbwerte oder nachfolgende LEDs betreffen. [Adafruit Best Practices](https://learn.adafruit.com/adafruit-neopixel-uberguide/best-practices).
2. Controller-Timing oder Treiberfehler. Espressif beschreibt explizit falsche Farben bei verzögerter RMT-Interruptbedienung, etwa durch WLAN auf demselben CPU-Kern. Ob diese Firmware tatsächlich diesen Treiber verwendet, ist unbekannt; keine passende Firmwarequelle im aktuellen Repository gefunden. [Espressif LED Strip](https://components.espressif.com/components/espressif/led_strip/versions/3.0.1/readme).
3. Versorgungsprobleme, besonders wenn der Fehler mit Last/Helligkeit zunimmt. Aus dem Video wurde keine Spannung gemessen und keine sichere Rangfolge gegenüber Signaltiming abgeleitet.

Nächster einfacher Vergleich: denselben internen Test mit dem vorhandenen Anschluss auf Panel 3 / Ausgang 3 beobachten. Damit wird zunächst unterschieden, ob nur Panel 4 betroffen ist. Ein späterer Kabel-/Port-Kreuztausch erfordert identische Pinbelegung und spannungsloses Umstecken; dabei müssen Testlänge und jeweiliger Ausgang passend berücksichtigt werden. Vorläufig keine weiteren Scanansichten als fehlerfrei bewerten, nur weil eine hohe Erkennungsquote erreicht wird.

Bei dieser Untersuchung wurden ausschließlich lokale Videos/Code und Controller-GET-Endpunkte gelesen. Kein Test gestartet, keine Konfiguration geschrieben, keine Verkabelung verändert. Alle Scanaufnahmen bleiben erhalten.
