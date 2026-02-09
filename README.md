# Søvndagbok (CBT-i støtteverktøy)

Søvndagbok er et digitalt verktøy designet for å hjelpe brukere med å registrere søvn, visualisere søvnmønstre og beregne søvneffektivitet (SE). Applikasjonen fungerer som et støtteverktøy i forbindelse med kognitiv atferdsterapi for insomni (CBT-i).

## Funksjoner

- **Plan-fane:** Sett opp din personlige søvnplan, definer søvnvindu og få beregnet anbefalt leggetid.
- **Loggføring:** Daglig registrering av tider (leggetid, slukket lys, innsovning, oppvåkning, sto opp), nattlige oppvåkninger og eventuell søvn på dagtid.
- **Visualisering:** Grafisk fremstilling av søvneffektivitet (SE) over tid og Gantt-diagram som viser døgnrytmen.
- **Analyse & Råd:** Automatisk beregning av gjennomsnittlig SE for siste 7 dager, samt konkrete råd om justering av søvnvinduet basert på CBT-i prinsipper. Inkluderer også vurdering av dagtidsøvn.
- **Rådata-visning:** Full oversikt over alle registrerte data i tabellform (siste 7 dager eller alle data).

## Teknologi

Applikasjonen er bygget med moderne og robuste teknologier:
- **Python 3.x**
- **Streamlit** (for brukergrensesnitt)
- **Plotly** (for interaktive grafer)

Data lagres lokalt på maskinen som JSON-filer, noe som sikrer enkel tilgang og portabilitet.

## Installasjon og kjøring

1. **Klon prosjektet:**
   Last ned kildekoden fra GitHub til din lokale maskin.
   ```bash
   git clone https://github.com/TinyOslo/SleepDiary.git
   cd SleepDiary
   ```

2. **Opprett virtuelt miljø (valgfritt men anbefalt):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # På Windows: venv\Scripts\activate
   ```

3. **Installer avhengigheter:**
   Installer nødvendige pakker. Hvis `requirements.txt` finnes:
   ```bash
   pip install -r requirements.txt
   ```
   Ellers, installer manuelt:
   ```bash
   pip install streamlit pandas plotly
   ```

4. **Start applikasjonen:**
   Kjør følgende kommando i terminalen:
   ```bash
   streamlit run Sovndagbok.py
   ```

## Bruk

Appen er designet for daglig bruk gjennom hele behandlingsperioden:

1. **Oppstart:** Opprett en ny dagbokfil eller åpne en eksisterende ved oppstart.
2. **Planlegging:** Gå til "Plan"-fanen for å sette ditt mål for oppvåkning og ønsket søvnvindu.
3. **Daglig logg:** Gå til "Loggføring" hver morgen for å registrere forrige natts søvn.
4. **Evaluering:** Bruk "Visualisering" og "Analyse" ukentlig for å se fremgang og vurdere justeringer av søvnvinduet.

> **Merk:** Dette er et teknisk støtteverktøy for egenregistrering og erstatter ikke profesjonell medisinsk vurdering eller behandling.

## CBT-i referanse

Logikken og beregningene i denne applikasjonen er inspirert av prinsipper fra standard CBT-i behandling.
- **Søvneffektivitet (SE)** beregnes som: `(Total Søvntid (TST) / Tid i Seng (TIB)) * 100 %`.
- Rådene følger retningslinjer lik de som finnes i «Kognitiv atferdsterapi ved insomni – Veileder for behandlere (2025)».

## Personvern og lagring

Alle data lagres utelukkende lokalt på din egen datamaskin i JSON-format. Ingen data sendes til eksterne servere eller skytjenester, noe som gir full kontroll over ditt eget personvern.

## Lisens

Denne applikasjonen er lisensiert under MIT-lisensen.
© 2026 Asbjørn Hval Bergestuen

Se `LICENSE`-filen for fullstendig lisenstekst.
