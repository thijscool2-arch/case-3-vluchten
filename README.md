# Zürich: vertraging, weer en corona

Streamlit-dashboard met drie pagina’s. Alle filters staan in de zijbalk.

- **Vertraging & voorspelling:** uurlijkse patronen in 2019, uitleg van het model, daarna de toets op ongeziene dagen. De referentie **Laatste dagwaarde** voorspelt morgen met de laatst gemeten dagelijkse vertraging.
- **Weer & vliegtuigtype:** correlaties tussen dagelijkse vertraging, wind, regen, temperatuur, luchtdruk en roosterdrukte in 2019; daarna de windhypothese per grootteklasse en een kwartaalcontrole.
- **Het coronajaar:** de vaste top 15 Europese verbindingen uit 2019 op twee kaarten met dezelfde schaal; tijdlijnen van beide jaren met een referentielijn op 11 maart 2020; vergelijking van dezelfde route.

## Starten

Gebruik **Python 3.12**. `app.py`, `analysis.py`, `requirements.txt`, `airports-extended.dat`, `schedule_airport.csv.gz`, `weather2019.csv.gz` en `weather2020.csv.gz` staan naast elkaar. Pak de `.gz`-bestanden niet uit.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit Community Cloud: repository `thijscool2-arch/case-3-vluchten`, branch `main`, main file `app.py`, Python 3.12. Een bestaande deployment kan de wijzigingen van GitHub automatisch ophalen.

## Model en interpretatie

Gradient boosting met vooraf vastgelegde instellingen. Het model voorspelt de gemiddelde positieve aankomstvertraging van een dag: vroege aankomsten tellen als nul. Train januari–augustus 2019; kalibratie september; toets oktober–december. De invoer gebruikt eerdere vertraging, eerder gemeten wind, regen, temperatuur en luchtdruk, plus het geplande verkeer, toestelverdeling en kalender van de voorspelde dag. Gemeten weer of vertraging van morgen wordt niet als invoer gebruikt. Ontbrekende kenmerken worden uitsluitend met de trainingswaarden ingevuld. De empirische foutband garandeert geen vaste dekking.

De correlatiematrix is beschrijvend en gebruikt complete dagwaarnemingen van 2019 met minstens 10 bruikbare landingen. Dagweer en vertraging van dezelfde dag zijn geschikt voor deze verkenning, maar daarmee is geen oorzaak bewezen en geen directe voorspeller voor morgen vastgesteld. Het aantal uitgesloten dagen staat naast de matrix. Windanalyses wegen dagen even zwaar en tonen bootstraponzekerheid. Een kwartaalverschil verschijnt alleen bij minstens 10 dagen in elk van beide windgroepen.

De rode tijdlijn markeert de [WHO-aanduiding als pandemie op 11 maart 2020](https://www.who.int/news-room/speeches/item/who-director-general-s-opening-remarks-at-the-media-briefing-on-covid-19---11-march-2020), niet het begin van alle besmettingen of reisbeperkingen. Verschillen tussen 2019 en 2020 bewijzen geen afzonderlijk corona-effect.

## Datakwaliteit en bronnen

Het HvA-rooster wordt gecontroleerd vóór analyse. Alleen duidelijke middernachtovergangen worden gecorrigeerd; ambigue verschillen blijven meetellen voor verkeersvolume maar worden uitgesloten van vertragingsanalyses. Luchthaven- en weerkoppelingen behouden het aantal vluchten. De interne koppeling gebruikt de broncodes; zichtbare luchthavenlabels gebruiken drieletter-IATA-codes. Ontbrekende locaties worden niet geschat. Grootteklasse is geen gemeten landingsgewicht. Geannuleerde of uitgeweken vluchten kunnen ontbreken.

Bronnen: HvA-rooster; Meteostat Zürich-Kloten 06670; OpenFlights. Zie `SOURCES.md` en de downloadbare toelichting in het dashboard voor herkomst, licenties en gebruikte documentatie. De optionele Amsterdam–Barcelona-profielen horen niet bij Zürich en worden niet samengevoegd. Code is met hulp van Codex gemaakt; de groep moet verwerking, model, toets en visualisaties zelf kunnen uitleggen.
