"""HISinOne-Explorer als Terminal-Oberflaeche (Textual).

Aufbau (jede Schicht erbt von der darunter):
    link_app.LinkTreeApp        Link-Baum, Filterfeld, Infospalte
    loading_app.LoadingApp      Login, Seiten laden, Baum-Tabellen erkennen
    navigation_app.NavigationApp  Aktionen (zurueck, neu laden, kopieren, ...)
    app.ExploreApp              Tasten, Shortcuts, Befehlspalette, Config

Tabellen: tables_screen (alle Tabellen einer Seite), single_table_screen
(eine im Vollbild, mit filter_screen als Basisklasse). Einstellungen:
settings (ganze Config), page_config (je Seite/Tabelle), shortcuts.
"""
