"""B3 - Enter im Suchfeld des Material Browsers.

Befund: /project1/material_browser/unified_search ist ein reiner fieldCOMP
ohne Callback-Parameter und ohne zugehoerigen panelexecuteDAT. Enter loeste
nichts aus, der Button SEARCH/APPLY war Pflicht - vier Klicks fuer den
haeufigsten Vorgang im Projekt (Feld, Button, Karte, APPLY SELECTED).

Neu: ein panelexecuteDAT 'unified_search_enter' nach demselben Muster wie
der bereits funktionierende 'unified_apply_click', nur auf den Panel-Wert
'select' des Feldes (feuert beim Bestaetigen mit Enter) statt auf 'lselect'
des Buttons. Der Button bleibt unveraendert; es kommt nur der Tastaturweg
hinzu.

OFFEN: dass 'select' beim Enter tatsaechlich pulst, liess sich aus der
Ferne nicht ausloesen und ist im interaktiven Review zu bestaetigen.
"""

PARENT = '/project1/material_browser'
NAME = 'unified_search_enter'

TEXT = '''# Enter in the search field applies the filters, same as the SEARCH/APPLY button.
# Before this (audit 2026-09-16, step B3) the field had no callback at all, so the
# button was mandatory and the most frequent action in the browser cost four clicks.
# The button keeps working; this only adds the keyboard path.

def onOffToOn(panelValue):
    op('/project1/material_browser/unified_runtime').module.apply_filters()
    return
'''


def apply():
    parent_op = op(PARENT)
    dat = parent_op.op(NAME) or parent_op.create(panelexecuteDAT, NAME)
    ref = parent_op.op('unified_apply_click')
    if ref:
        dat.nodeX, dat.nodeY = ref.nodeX, ref.nodeY - 140
    dat.par.panels = parent_op.op('unified_search')
    dat.par.panelvalue = 'select'
    dat.par.offtoon = True
    for off in ('whileon', 'ontooff', 'whileoff', 'valuechange'):
        setattr(dat.par, off, False)
    dat.par.active = True
    dat.text = TEXT
    return f'{dat.path} created'


def revert():
    dat = op(PARENT).op(NAME)
    if dat:
        dat.destroy()
        return f'{PARENT}/{NAME} removed'
    return 'nothing to revert'
