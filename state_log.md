# Systemdokumentasjon: Sovndagbok (SleepDiary)

Denne filen fungerer som prosjektets tekniske hukommelse og dokumenterer arkitektur, dataflyt og tilstandshåndtering.

## 1. Systemoversikt

Applikasjonen er en **Streamlit**-basert webapplikasjon designet for å støtte Kognitiv Atferdsterapi for Insomni (CBT-i).

### Dataflyt
1.  **Brukerinput**: Brukeren registrerer søvndata (leggetid, oppvåkninger, stå-opp-tid) via `st.time_input`, `st.number_input` og egne input-skjemaer.
2.  **Tilstand (Session State)**: Midlertidige data lagres i `st.session_state` før lagring.
3.  **Filbehandling**: Data persisteres i lokale JSON-filer (f.eks. `min_sovndagbok.json`).
4.  **Databehandling (Pandas)**: JSON-data lastes inn og transformeres til en Pandas DataFrame i `process_log_data()`. Her beregnes metrikker som Søvneffektivitet (SE), Total Søvntid (TST) og Tid i Seng (TIB).
5.  **Visualisering (Plotly)**:
    -   **Gantt-diagram (`build_sleep_gantt_figure`)**: Viser døgnrytme fra 18:00 til 18:00. Håndterer midnatts-overganger ved å normalisere datoer.
    -   **SE-graf**: Linjediagram som viser utvikling i søvneffektivitet over tid.

## 2. Funksjonalitet og Logikk

### CBT-i Logikk
Kjernen i applikasjonen er beregningen av **Søvneffektivitet (SE)** og dynamisk justering av **Søvnvindu**.
-   **SE Formel**: `(Total Søvntid / Tid i Seng) * 100`
-   **Regler for justering (basert på snitt siste uke)**:
    -   SE > 85%: Øk søvnvindu med 15 min.
    -   SE < 80%: Reduser søvnvindu med 15 min (min 5 timer).
    -   SE 80-85%: Ingen endring.
-   **Søvnrestriksjon**: Appen holder styr på et "aktivt søvnvindu" som brukeren skal prøve å følge.

### Moduler
-   **DataManager**: Klasse som håndterer all fil-I/O (laste/lagre JSON).
-   **UI Components**: Separate funksjoner for hver visning (`render_logging_view`, `render_viz_view`, etc.).

## 3. Biblioteker og Avhengigheter

Status for `requirements.txt`:
*   `streamlit`: Brukes til UI.
*   `plotly`: Brukes til grafer.
*   `pandas`: Brukes til dataminipulering.

> [!NOTE]
> `requirements.txt` er nå oppdatert med låste versjonsnumre (f.eks. `streamlit==1.54.0`) basert på aktivt miljø. Dette sikrer reproduserbarhet.

**Merk:** `watchdog` er inkludert i `requirements.txt` (versjon 6.0.0).

## 4. Session State Håndtering

`st.session_state` brukes omfattende for å holde på applikasjonens tilstand mellom overganger (reruns).

*   `data`: Inneholder hele datastrukturen fra JSON-filen (lastet i minne).
*   `filepath`: Stien til den aktive JSON-filen.
*   `current_browser_dir`: Holder styr på hvilken mappe filutforskeren ser på.
*   `log_date`: Datoen som loggføres akkurat nå.
*   `current_wakeups`: Midlertidig liste med oppvåkninger under redigering, før lagring.
*   `history_editor_data`: Kopi av historikk-dataene under redigering i "Din søvnplan".

## 5. Tekniske Observasjoner og Forbedringspotensial

### Logiske Utfordringer
*   **Dato-håndtering ved midnatt**: Logikken for å splitte døgnet ved kl 18:00 (`get_dt` funksjonen) er robust, men hardkodet.
*   **Historikk-redigering**: Logikken i `render_window_history_editor` er kompleks med mye manuell validering. Kunne vært forenklet ved å bruke en mer strukturert datamodell eller skjemavalidering.

### Ryddepotensial (Minimalistisk)
Koden er generelt velstrukturert (takket være nylig refaktorering), men enkelte ting kan ryddes:

1.  **Ubrukte/Implisitte Importer**:
    -   Ingen direkte ubrukte biblioteker funnet i toppen av filen.
    
2.  **Redundant kode**:
    -   `render_report_content`: Inneholder en indre funksjon `generate_aligned_table` som bygger en markdown-tabell manuelt. Dette kunne kanskje vært løst enklere med `df.to_markdown()`, men dagens løsning gir full kontroll over bredde og format, så det er ikke direkte feil.
    -   Snapshot-logikken i `render_logging_view` (`st.session_state.original_values`) er litt "verbose", men nyttig for UX (warning ved ulagrede endringer).

### Konklusjon
Prosjektstrukturen er solid. Neste steg bør være å formalisere tester hvis prosjektet vokser.
