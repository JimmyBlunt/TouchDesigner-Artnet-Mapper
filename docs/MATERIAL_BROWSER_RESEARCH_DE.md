# Vergleich: Bedienansätze für Live-Materialien

| Ansatz | Vorbild | Stärke | Grenze | Entscheidung |
|---|---|---|---|---|
| Zentraler Live-Dashboard | Resolume | schnelle, sichere Live-Bedienung | weniger Spezialparameter | **Basis der Umsetzung** |
| Material-spezifischer Inspector | MadMapper | sehr detaillierte Shaderwerte | für Live-Bedienung zu komplex | später ergänzbar |
| Transform-Pipeline | TouchDesigner | Fokus, Zoom und 3D-Map sauber trennbar | braucht klare Reihenfolge | **technische Grundlage** |
| Look-/Cue-Presets | Resolume/MadMapper | wiederholbare Looks | zusätzlicher Verwaltungsaufwand | nächste Ausbaustufe |

Die gewählte Lösung verbindet einen zentralen Live-Dashboard-Ansatz mit einer
Transform-Ebene vor der 3D-UV-Map. Sie nutzt bestehende zentrale Parameter
(`Speed`, `Color`, `Color2`) und ergänzt nur Fokus und Zoom.

Quellen: [TouchDesigner Crop TOP](https://docs.derivative.ca/Crop_TOP),
[Resolume Dashboard](https://www.resolume.com/support/dashboard),
[Resolume Parameter Animation](https://resolume.com/support/en/parameter-animation),
[MadMapper Media Inspector](https://docs.madmapper.com/madmapper/6/3.-media/media-bin),
[MadMapper GLSL-Parameter](https://docs.madmapper.com/madmapper/6/3.-media/writing-custom-glsl-materials).
