# Zürich: wind, vertraging en het coronajaar

Een Nederlandstalig Streamlit-dashboard met zes pagina's. De rode draad is de vraag of meer wind anders samenhangt met vertraging bij regionale, narrowbody- en widebody-types. Daarnaast vergelijkt het dashboard 2019 en 2020 en voorspelt het de gemiddelde positieve aankomstvertraging voor de volgende dag.

## Starten

Python **3.12**. Vanaf een schone clone:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Alle drie benodigde databronnen staan in `data/`; geen Kaggle-account, token of extra downloadstap nodig. `@st.cache_data` voorkomt opnieuw inlezen en trainen bij elke klik. Kaartachtergrond vereist internet; zonder tiles blijven de gekoppelde routetabel en andere analyses beschikbaar. Voor lokaal Windows-gebruik kan ook `start_dashboard.bat` worden gestart (installeert vereisten in een lokale virtuele omgeving).

## Pagina's en verhaal

1. **Overzicht:** aantallen en de breuk tussen 2019/2020, met drie onderzoeksvragen.
2. **Vertraging & voorspelling:** uurpatronen, dagvoorspelling, baseline, ongeziene testdagen, empirische foutband, grootste missers en 2020 als stresstest.
3. **Wind & vliegtuigtype:** alleen landingen, jaren apart, daggewogen percentages en 95%-bootstrapintervallen. Oranje = regionaal, groenblauw = widebody, grijs = narrowbody-context. Gevoeligheidscontrole op extreme tijden en kwartaalcontrole.
4. **Het coronajaar:** maandelijkse bewegingen/vertraging, vaste top-10-routegroep met alleen de twee sterkste krimpers gekleurd, en dezelfde route vergelijken.
5. **Routes op de kaart:** vaste top 15 van 2019 uit de Europese tijdzones; kleur = procentuele krimp, puntoppervlak = oorspronkelijke drukte; twee labels, geen 295 willekeurige punten.
6. **Data & verantwoording:** ingrepen met aantallen, ontbrekende waarden, joincontroles, uitschieters, bronnen, beperkingen en presentatie-opzet.

## Inspecteer vóór je plot

`analysis.py` leest brondata, inspecteert en valideert joins. Het dashboard gebruikt dezelfde functies. `data/inspection.json` is een opgeslagen momentopname, geen handmatig verzonnen audit.

- Datum exact `dd/mm/yyyy`; '-' betekent ontbrekend, geen nul.
- Alleen volledige duplicaten verwijderen.
- Werkelijke datum ontbreekt: voor duidelijke avond→vroege-ochtendgevallen +24 uur. Geen blinde modulo-correctie die een 16-uurvertraging in een vroege aankomst verandert.
- `|vertraging| >360 min` als ambigu: behoud voor verkeerstellingen; geen vertragings-/modeldoel. Ook plausibele echte zeer lange vertraging kan hierdoor ontbreken. Het dashboard toont de gevoelige rijen en impact; vraag de bronhouder om werkelijke datums als vervolg.
- Onder die grens worden extreme geldige waarden behouden. Beschrijvende gevoeligheidsanalyse zonder `|vertraging|>180` is apart zichtbaar.
- Getekend tijdverschil kan negatief zijn (vroeg). Positieve vertraging `max(verschil,0)` is het modeldoel; vertraagd = **≥15 min**.
- Origineel OpenFlights is komma-gescheiden met decimale punt. Het alternatieve clean-lesbestand zou `sep=';', decimal=','` vereisen. Geen raden van delimiter.
- `many_to_one` op ICAO en weerdatum; geen verloren bronrijen. Niet-gekoppelde codes krijgen geen verzonnen locatie.
- BCS1/BCS3 (A220) zijn narrowbody; de indeling is handmatig, inspecteerbaar en geen geschat gewicht.
- `flightdata.zip` is geïnspecteerd en uitgesloten: Amsterdam–Barcelona past niet bij de Zürich-hoofdvraag. Het project bevat daarom geen misleidende vierde merge.

## Voorspelmethode

Doel: per dag de gemiddelde **positieve aankomstvertraging**, mits ten minste 10 geldige landingen. Voorspelmoment: einde van de vorige lokale dag. Invoer: vorige dagvertraging, afgelopen 7 dagen, **weer gisteren**, het geplande rooster van morgen, maand en weekdag. Geen gemeten weer morgen of vertragingscodes.

**Gradient boosting regressie**, vaste parameters in `analysis.py`:
- Training jan–aug 2019 (243 dagen).
- September 2019 alleen voor empirische 90e-percentiel-foutband en beschrijvend permutatiebelang.
- Oktober–december 2019 ongeziene test (92 dagen).
- 2020 als aparte stresstest (340 dagen); hetzelfde model, dezelfde foutband, geen retraining.
- Ontbrekende invoer: uitsluitend trainingsmediaan; ontbrekend doel nooit ingevuld.
- Baselines: gisteren en vaste trainingsmediaan. MAE/RMSE op daggemiddelden, geen claim over individuele vluchten.
- Elke testdag mag gisteren waargenomen vertraging gebruiken: een rollende **één-dag-vooruit** voorspelling, geen 92-daagse voorspelling vanuit één startpunt.
- Historisch rooster bevat alleen geregistreerde bewegingen. De vooraf geplande drukte van uitgevallen vluchten kan ontbreken. Voor een echte operationele toepassing is een vooraf opgeslagen volledig rooster en point-in-time weerbron nodig.

De band is een empirische foutmarge. De test toont werkelijk gemeten dekking; 90% is geen bewezen garantie, zeker niet bij de coronabreuk. De testresultaten mogen het model niet achteraf sturen.

## Windhypothese

Typeklasse is een benadering van grootte, niet werkelijke massa of windlimiet. Vergelijk het dagelijks vertraagde aandeel bij minder/meer wind; bootstrap hele dagen, geen individuele vluchten. Samenhang kan voortkomen uit routes, maatschappijen, seizoen of drukte. De hypothese dat zwaardere vliegtuigen 'wel kunnen landen' kan met deze gegevens niet rechtstreeks worden getoetst: ontbrekende annuleringen/uitwijkingen veroorzaken mogelijke selectiebias. Geen causale claims.

## GitHub → Streamlit

Repository: een nieuwe `zurich-dashboard` bij `thijscool2-arch` (pas een publicatieclaim doen nadat dit werkelijk is gepubliceerd).

1. Zet de **inhoud** van deze projectmap op de hoofdbranch, inclusief `data/` en `.streamlit/`.
2. Streamlit Community Cloud → Create app → kies repository en branch → main file **app.py**.
3. Advanced settings → Python **3.12** → Deploy.
4. Open alle zes pagina's en controleer ook de kaart. Deel de daadwerkelijk toegekende `*.streamlit.app`-link, niet een geraden URL.

Dit pakket is compleet; de publicatie-eis is pas behaald zodra de app daadwerkelijk online staat. Een GitHub- of Streamlit-login kan een handmatige stap voor de eigenaar vereisen.

## Verificatie

```bash
python -m unittest discover -s tests
python scripts/check_app.py
python scripts/refresh_audit.py
```

AppTest laadt alle zes pagina's en controleert fouten, filters en extreme windgrenzen. Audit wordt uit de bronnen geregenereerd. Bronnen/licenties/documentatie staan in `SOURCES.md`; opzet voor een presentatie van negen minuten in `PRESENTATIE.md`.
