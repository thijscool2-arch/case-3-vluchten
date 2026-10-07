"""Streamlit-dashboard Zürich, gebouwd rond vragen en onderbouwde bevindingen."""
from pathlib import Path
import hashlib
import importlib
import analysis as analysis_module
# Streamlit reruns app.py but imported modules can remain from an older deployment.
importlib.reload(analysis_module)
ANALYSIS_VERSION = hashlib.sha256(Path(analysis_module.__file__).read_bytes()).hexdigest()
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from analysis import load_data, daily_frame, fit_forecast, wind_analysis, GROUPS

st.set_page_config(page_title='Zürich | Wind, vertraging & corona',page_icon='✈',layout='wide',initial_sidebar_state='expanded')
ORANGE='#E75C37'; TEAL='#087F83'; GREY='#BCC3C8'; DARK='#202C37'; PURPLE='#705CC5'; RED='#BC4053'; BLUE='#3968AA'
PALETTE={'Regionaal':ORANGE,'Narrowbody':GREY,'Widebody':TEAL,'2019':GREY,'2020':ORANGE,'Landing':TEAL,'Vertrek':ORANGE}
st.markdown('''<style>
.stApp {background:#F7F6F2;color:#202C37;}
.block-container {max-width:1250px;padding-top:1.7rem;padding-bottom:3rem;}
h1 {font-weight:750!important;letter-spacing:-1.5px!important;}
h2 {letter-spacing:-.6px!important;} [data-testid="stMetric"] {background:#fff;border-radius:12px;padding:18px;border:1px solid #E2E5E4;}
[data-testid="stMetricValue"] {font-size:2rem;} [data-testid="stSidebar"] {border-right:1px solid #ddd;}
.story {background:linear-gradient(120deg,#1F3544,#294D55);color:white;padding:22px 28px;border-radius:16px;margin:16px 0 26px;line-height:1.65;font-size:1.06rem;border-left:5px solid #F59B73;}
.story b {color:#FFA17F;} .eyebrow {color:#64717B;text-transform:uppercase;letter-spacing:2px;font-size:.76rem;margin-bottom:14px;}
[data-testid="stSidebar"] {background:#EEEFEB;}
[data-testid="stMain"] [data-testid="stRadio"] > div[role="radiogroup"] {display:flex;gap:10px;padding:8px;background:#E9ECE8;border-radius:14px;margin-bottom:28px;}
[data-testid="stMain"] [data-testid="stRadio"] label {flex:1;padding:12px 16px;border-radius:10px;background:#fff;min-width:180px;}
[data-testid="stMain"] [data-testid="stRadio"] label:has(input:checked) {background:#203C46;color:#fff;}
[data-testid="stMain"] [data-testid="stRadio"] label:has(input:checked) p {color:#fff;}
[data-testid="stMain"] [data-testid="stRadio"] label > div:first-child {display:none;}
[data-testid="stMetricLabel"] p {color:#62757D;}
h3 {font-size:1.35rem!important;} h4 {font-size:1.1rem!important;line-height:1.5!important;}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner='Brondata inspecteren en koppelen…',max_entries=1)
def data(code_version): return load_data()
@st.cache_data(show_spinner='Voorspelling trainen en toetsen op latere dagen…',max_entries=1)
def forecast(daily,code_version):
    return fit_forecast(daily)
@st.cache_data(max_entries=12)
def wind(year,threshold,trim,code_version,_df):
    return wind_analysis(_df,year,threshold,trim)

def story(text): st.markdown(f'<div class="story">{text}</div>',unsafe_allow_html=True)
def header(kicker,title,subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div>',unsafe_allow_html=True)
    st.title(title); st.markdown(subtitle)
def chart(fig,key=None,height=370):
    if fig.layout.title.text:
        st.markdown(f'#### {fig.layout.title.text}')
    fig.update_layout(title=None,height=height,font=dict(family='Arial',size=13,color=DARK),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=15,r=25,t=45,b=30),legend=dict(orientation='h',y=1.02,x=0,yanchor='bottom'),hoverlabel=dict(bgcolor='white'),title_font=dict(size=18))
    fig.update_xaxes(showgrid=False,zeroline=False)
    fig.update_yaxes(gridcolor='#E1E4E2',zerolinecolor='#C5CACB')
    st.plotly_chart(fig,use_container_width=True,key=key,config={'displaylogo':False})
def num(n): return f'{int(n):,}'.replace(',','.')
def percent(v): return f'{100*v:.1f}%'.replace('.',',')
def late_by_year(d):
    return d.loc[d.geldig].groupby('jaar').agg(n=('FLT','size'),late=('te_laat','mean'),positive=('positief','mean'))
def monthly_counts(d):
    x=d.groupby(['jaar','maand','beweging']).size().rename('vluchten').reset_index()
    full=pd.MultiIndex.from_product([[2019,2020],range(1,13),['Landing','Vertrek']],names=['jaar','maand','beweging'])
    # Missing cells stay NaN: no automatic zero days/months for absent source rows.
    return x.set_index(['jaar','maand','beweging']).reindex(full).reset_index()

D,W,A=data(ANALYSIS_VERSION)
AIRPORTS=D[['Org/Des','IATA','City']].drop_duplicates().set_index('Org/Des')
def airport_code(code):
    value=AIRPORTS.IATA.get(code)
    return str(value) if pd.notna(value) and len(str(value))==3 else 'code onbekend'
def airport_label(code):
    city=AIRPORTS.City.get(code)
    return f'{airport_code(code)} · {city if pd.notna(city) else "luchthavennaam onbekend"}'
st.markdown('<div class="eyebrow">ZRH / het verhaal achter de vlucht</div>',unsafe_allow_html=True)
PAGE=st.radio('Pagina', ['Vertraging & voorspelling','Weer & vliegtuigtype','Het coronajaar'],horizontal=True,label_visibility='collapsed',key='page')

with st.sidebar:
    st.markdown('### ZÜRICH / ZRH')
    st.caption('Van rooster naar inzicht · 2019–2020')
    if PAGE!='Het coronajaar':
        year=st.selectbox('Analysejaar',[2019,2020],key='analysis_year')
    st.divider()
    st.caption('Lees per grafiek de titel, kleurlegenda en korte toelichting.')
    st.caption('Vertraagd: ≥15 minuten. Landing en vertrek worden waar nodig apart geanalyseerd.')
    st.caption('Bronnen: HvA-rooster, Meteostat 06670 en OpenFlights. Alle bronbestanden zijn meegeleverd.')


if PAGE=='Vertraging & voorspelling':
    header('01 / begrijpen → toetsen','Vertraging herkennen én voorspellen','Eerst het patroon per uur; daarna een eerlijke toets: kunnen we morgen de gemiddelde aankomstvertraging voorspellen?')
    st.caption(f'Je bekijkt {year}. Het model blijft getraind op 2019; de toets volgt het gekozen jaar.')
    x=D.loc[D.jaar.eq(year)&D.geldig]
    metrics=late_by_year(x).loc[year]
    cards=st.columns(3)
    cards[0].metric('Vluchten met bruikbare tijden',num(metrics['n']))
    cards[1].metric('Minstens 15 minuten te laat',percent(metrics['late']))
    cards[2].metric('Gemiddelde aankomstvertraging',f'{x.loc[x.LSV.eq("L"),"positief"].mean():.1f} min')
    h=x.groupby(['uur','beweging']).agg(percentage=('te_laat','mean'),n=('FLT','size')).reset_index()
    reliable=h.loc[h.n.ge(100)]
    if not reliable.empty:
        peak=reliable.loc[reliable.percentage.idxmax()]
        story(f'In {year} heeft <b>{peak.beweging.lower()} rond {int(peak.uur):02d}:00</b> het hoogste aandeel vertraagde vluchten onder uurvakken met minstens 100 bewegingen: <b>{percent(peak.percentage)}</b>. Dat is een patroon in het rooster, geen bewezen effect van het tijdstip.')
    fig=go.Figure()
    for b,col in [('Landing',TEAL),('Vertrek',ORANGE)]:
        hh=h.loc[h.beweging.eq(b)].set_index('uur').reindex(range(24))
        fig.add_trace(go.Scatter(x=hh.index,y=100*hh.percentage,name=b,mode='lines+markers',line=dict(color=col,width=3),customdata=hh.n,hovertemplate='%{x}:00 · %{y:.1f}%<br>n=%{customdata}<extra>%{fullData.name}</extra>',connectgaps=False))
    fig.update_layout(title=f'{peak.beweging} rond {int(peak.uur):02d}:00 heeft het hoogste vertraagde aandeel · {year}',xaxis_title='Gepland lokaal uur',yaxis_title='Vluchten ≥15 minuten vertraagd (%)')
    chart(fig);st.caption('Alleen geldige tijden; aankomst en vertrek apart. Geen lijn over ontbrekende uren. Het dagritme is geen gecontroleerde causale vergelijking.')
    st.divider();st.subheader('Van weer en rooster naar de vertraging van morgen')
    intro=st.columns(3)
    with intro[0]:
        with st.container(border=True):
            st.markdown('#### 01 · De vraag')
            st.write('Hoeveel minuten komen landingen morgen gemiddeld te laat? Vroege landingen tellen als nul. We voorspellen een daggemiddelde, geen individuele vlucht.')
    with intro[1]:
        with st.container(border=True):
            st.markdown('#### 02 · De informatie')
            st.write('Eerdere vertraging, wind, regen, temperatuur en luchtdruk. Daarbij komen de geplande drukte en toestelverdeling van morgen, de weekdag en de maand.')
    with intro[2]:
        with st.container(border=True):
            st.markdown('#### 03 · De eerlijke toets')
            st.write('Leren: januari–augustus 2019. Foutband: september. Toets: latere dagen. We vergelijken met **Laatste dagwaarde**: morgen is gelijk aan vandaag.')
    st.caption('Model: gradient boosting, kleine beslisbomen die elkaars fouten verbeteren. Alleen eerder beschikbare weerwaarden; het gemeten weer van morgen is onbekend. Ontbrekende invoer wordt ingevuld vanuit de trainingsperiode. Geannuleerde vluchten kunnen ontbreken in het historische rooster.')
    st.subheader('De toets: levert het model een kleinere fout op?')
    F=forecast(daily_frame(D,W),ANALYSIS_VERSION)
    M=F['metrics'] if year==2019 else F['stress_metrics']
    T=F['test'] if year==2019 else F['stress']
    if year==2020:
        st.info('2020 is een extra stresstest: het model en de foutband blijven vastgezet op 2019. Het model leert niet opnieuw van het coronajaar.')
    gain=100*(M['baseline_MAE']-M['MAE'])/M['baseline_MAE']
    direction='lager' if gain>=0 else 'hoger'
    story(f'De gemiddelde fout is <b>{M["MAE"]:.1f} minuten</b> op {M["dagen"]} ongeziene testdagen. Dat is <b>{abs(gain):.1f}% {direction}</b> dan de referentie <b>Laatste dagwaarde</b>. Het model voorspelt een daggemiddelde; de fout voor een individuele vlucht kan veel groter zijn.')
    c=st.columns(3)
    c[0].metric('Gemiddelde voorspellingsfout',f'{M["MAE"]:.1f} min');c[1].metric('Referentie: Laatste dagwaarde',f'{M["baseline_MAE"]:.1f} min');c[2].metric('Testdagen binnen de foutband',percent(M['dekking']))
    st.caption('Een kleinere fout is beter. De foutband toont een verwachte marge; de dekking vertelt op hoeveel testdagen de echte vertraging binnen die marge viel.')
    t=T
    plot_t=t.reindex(pd.date_range(t.index.min(),t.index.max(),freq='D'))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.bovengrens,line=dict(width=0),showlegend=False,hoverinfo='skip',connectgaps=False))
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.ondergrens,line=dict(width=0),fill='tonexty',fillcolor='rgba(112,92,197,.13)',name='Empirische 90%-foutband',hoverinfo='skip',connectgaps=False))
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.baseline,name='Laatste dagwaarde',line=dict(color=GREY,width=1.5,dash='dot'),connectgaps=False))
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.doel,name='Werkelijk',line=dict(color=DARK,width=1.8),connectgaps=False))
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.voorspeld,name='Voorspeld',line=dict(color=PURPLE,width=2.5),connectgaps=False))
    fig.update_layout(title=f'De voorspellingsfout is {abs(gain):.0f}% {"kleiner" if gain>=0 else "groter"} dan de referentie',xaxis_title='Voorspelde dag',yaxis_title='Gemiddelde positieve aankomstvertraging (min)')
    chart(fig,height=420)
    st.caption(f'Train: jan–aug 2019 · foutband: september 2019 · toets: {"okt–dec 2019" if year==2019 else "heel 2020, zonder opnieuw trainen"}. De empirische 90%-band biedt geen gegarandeerde dekking bij veranderende omstandigheden.')
    l,r=st.columns([1,1])
    with l:
        imp=F['importance'].sort_values('MAE_toename')
        cols=[ORANGE if v==imp.MAE_toename.max() and v>0 else GREY for v in imp.MAE_toename]
        fig=go.Figure(go.Bar(x=imp.MAE_toename,y=imp.kenmerk,orientation='h',marker_color=cols,error_x=dict(type='data',array=imp.spreiding,color=DARK)))
        fig.update_layout(title='Eerdere vertraging en weer: wat helpt het model?',xaxis_title='Extra MAE na verwisselen (min)',yaxis_title='')
        chart(fig);st.caption('Permutatiebelang op september, geen causaal effect. Balkjes tonen spreiding over 15 verwisselingen. Correlatie tussen kenmerken kan belang verdelen.')
    with r:
        st.markdown('#### Op drukke vertragingsdagen kan het model missen')
        worst=t.loc[t.fout.abs().idxmax()]
        day=t.fout.abs().idxmax().strftime('%d-%m-%Y')
        st.write(f'De grootste misser in deze periode is {day}: voorspeld **{worst.voorspeld:.1f} minuten**, werkelijk **{worst.doel:.1f} minuten** gemiddelde aankomstvertraging.')
        st.caption('De beschikbare gegevens vertellen niet welke storing, staking of weersituatie deze misser veroorzaakte.')
    st.download_button('Download alle testvoorspellingen',t.to_csv().encode(),'testvoorspellingen.csv','text/csv')

elif PAGE=='Weer & vliegtuigtype':
    header('02 / eerst het weer, dan de hypothese','Welke omstandigheden hangen samen met vertraging?','Hypothese: op dagen met meer wind neemt vertraging bij kleinere vliegtuigtypes sterker toe dan bij widebody-types.')
    st.caption(f'Weer en vliegtuigtypes in {year}. Elke vergelijking gebruikt alleen het gekozen jaar.')
    threshold=st.sidebar.slider('Daggemiddelde wind: grens (km/h)',10,25,15)
    trim=st.sidebar.checkbox('Gevoeligheid: zonder |vertraging| >180 min',False)
    st.subheader('Welke omstandigheden gaan samen met meer vertraging?')
    st.write('Lees van links naar rechts: links hangt samen met minder vertraging, rechts met meer. De twee sterkste verbanden krijgen kleur; de overige balken geven context.')
    weather_daily=daily_frame(D,W).loc[f'{year}-01-01':f'{year}-12-31']
    columns={'doel':'Vertraging','wspd':'Wind','prcp':'Regen','tavg':'Temperatuur','pres':'Luchtdruk','geplande_bewegingen':'Drukte'}
    complete=weather_daily.loc[weather_daily.landing_n.ge(10),list(columns)].dropna().rename(columns=columns)
    target=complete.corr()['Vertraging'].drop('Vertraging').dropna()
    if len(complete)>=10 and not target.empty:
        strongest=target.abs().idxmax()
        trend='meer' if target[strongest]>0 else 'minder'
        story(f'<b>{strongest}</b> laat in {year} het sterkste verband zien: een hogere waarde gaat samen met <b>{trend} aankomstvertraging</b>. Dit is een patroon op dezelfde dag; het vertelt niet welke factor de vertraging veroorzaakt.')
        ranked=target.sort_values()
        highlight=set(target.abs().nlargest(2).index)
        fig=go.Figure(go.Bar(x=ranked,y=ranked.index,orientation='h',marker_color=[(ORANGE if v>0 else TEAL) if k in highlight else GREY for k,v in ranked.items()],text=[f'{v:+.2f}' for v in ranked],textposition='outside',cliponaxis=False,hovertemplate='%{y}<br>Samenhang met vertraging: %{x:+.2f}<extra></extra>'))
        fig.update_layout(title=f'Hogere {strongest.lower()} gaat samen met {trend} vertraging · {year}',xaxis=dict(range=[-1,1],tickvals=[-1,-.5,0,.5,1],ticktext=['Sterk minder','Minder','Geen verband','Meer','Sterk meer']),yaxis_title='',showlegend=False)
        fig.add_vline(x=0,line_color=DARK,line_width=1)
        chart(fig,height=340)
        st.caption(f'{len(complete)} complete dagen; {len(weather_daily)-len(complete)} dagen uitgesloten door ontbrekende waarden of minder dan 10 landingen. Balklengte = Pearson-correlatie (−1 tot +1), geen minuten of voorspelde oorzaak. Seizoen en routes kunnen ook een rol spelen.')
        rainwind=complete[['Wind','Regen']].corr().iloc[0,1]
        st.caption(f'Wind en regen veranderen ook samen (r = {rainwind:+.2f}). Het voorspelmodel neemt daarom meerdere variabelen mee en gebruikt eerder beschikbare weerwaarden.')
    else:
        st.info('Te weinig complete dagen om deze verbanden betrouwbaar te tonen.')
    st.divider();st.subheader('De windhypothese: reageren kleinere types anders?')
    summary,diff,x=wind(year,threshold,trim,ANALYSIS_VERSION,D)
    rdelta=diff.set_index('groep').verschil_pp
    outcome=f'Regionale types: <b>{rdelta.get("Regionaal",float("nan")):+.1f} procentpunt</b>; widebody-types: <b>{rdelta.get("Widebody",float("nan")):+.1f} procentpunt</b> verschil bij meer wind. '
    story(outcome+f'We vergelijken <b>alleen landingen in {year}</b>. Blauw toont dagen met minder wind; rood toont dagen met meer wind. De afstand tussen beide punten toont het verschil per vliegtuigklasse. “Meer wind” betekent hier een <b>daggemiddelde ≥{threshold} km/h</b> — niet de wind tijdens de landing.')
    st.caption('We vergelijken grootteklassen, geen gemeten landingsgewicht. Actuele massa, windrichting en uurweer ontbreken. Uitgevallen of uitgeweken vluchten kunnen buiten het rooster vallen.')
    fig=go.Figure()
    for group in GROUPS:
        pair=summary.loc[summary.groep.eq(group)].set_index('windgroep')
        if {'Minder wind','Meer wind'}.issubset(pair.index):
            fig.add_trace(go.Scatter(x=pair.loc[['Minder wind','Meer wind'],'percentage'],y=[group,group],mode='lines',line=dict(color=GREY,width=3),showlegend=False,hoverinfo='skip'))
    for wg,col in [('Minder wind',BLUE),('Meer wind',RED)]:
        b=summary.loc[summary.windgroep.eq(wg)].set_index('groep').reindex(GROUPS)
        fig.add_trace(go.Scatter(y=b.index,x=b.percentage,mode='markers',name=wg,marker=dict(size=13,color=col),error_x=dict(type='data',array=b.hoog-b.percentage,arrayminus=b.percentage-b.laag,color=col),customdata=b[['dagen','vluchten']],hovertemplate='%{y}: %{x:.1f}%<br>%{customdata[0]} dagen · %{customdata[1]} landingen<extra>%{fullData.name}</extra>'))
    wind_direction='sterker' if rdelta.get('Regionaal',0)>rdelta.get('Widebody',0) else 'niet sterker'
    fig.update_layout(title=f'Het windverschil is bij regionale types {wind_direction} dan bij widebody · {year}',xaxis_title='Gemiddeld dagelijks aandeel ≥15 minuten vertraagd (%)',yaxis_title='')
    chart(fig)
    st.caption('Blauw = minder wind; rood = meer wind. De verbinding maakt het verschil binnen één klasse zichtbaar. Elke dag weegt even zwaar. De strepen tonen de onzekerheidsmarge uit 1.500 hersteekproeven van hele dagen; overlap of kleine aantallen maken conclusies minder stevig.')
    for wg in ['Minder wind','Meer wind']:
        rows=summary.loc[summary.windgroep.eq(wg)]
        st.caption(wg + ': ' + ' · '.join(f'{r.groep}: {int(r.dagen)} dagen, {num(r.vluchten)} landingen' for r in rows.itertuples()))
    if not diff.empty:
        regional=diff.loc[diff.groep.eq('Regionaal')]
        heavy=diff.loc[diff.groep.eq('Widebody')]
        if not regional.empty and not heavy.empty:
            a=regional.iloc[0];b=heavy.iloc[0]
            st.markdown(f'**Bij meer wind verandert het vertraagde aandeel met {a.verschil_pp:+.1f} procentpunt bij regionale types en {b.verschil_pp:+.1f} bij widebody-types.**')
            st.write('Dit patroon ondersteunt de richting van de hypothese beschrijvend.' if a.verschil_pp>b.verschil_pp else 'Deze vergelijking ondersteunt de voorgestelde richting van de hypothese niet. Ook dat is een onderzoeksresultaat.')
    st.caption('Regionaal = kleinere jets en turboprops; narrowbody = toestellen met één gangpad; widebody = grotere toestellen met twee gangpaden. Onbekende types tellen hier niet mee. Grootte is een benadering, geen gemeten gewicht.')
    st.subheader('Blijft het windverschil zichtbaar binnen elk kwartaal?')
    st.write('We vergelijken nu meer en minder wind binnen hetzelfde kwartaal. Kies één vliegtuigklasse: elke balk laat één verschil zien, in plaats van zes lijnen tegelijk.')
    group=st.sidebar.selectbox('Vliegtuigklasse voor de seizoenscontrole',GROUPS,key='season_group')
    daily=x.groupby(['datum','kwartaal','groep']).agg(late=('te_laat','mean'),wind=('wspd','first')).reset_index()
    daily['windgroep']=np.where(daily.wind.ge(threshold),'Meer wind','Minder wind')
    q=daily.loc[daily.groep.eq(group)].groupby(['kwartaal','windgroep']).agg(p=('late','mean'),dagen=('datum','size')).reset_index()
    rates=q.pivot(index='kwartaal',columns='windgroep',values='p').reindex(index=range(1,5),columns=['Minder wind','Meer wind'])
    counts=q.pivot(index='kwartaal',columns='windgroep',values='dagen').reindex(index=range(1,5),columns=['Minder wind','Meer wind']).fillna(0)
    differences=100*(rates['Meer wind']-rates['Minder wind'])
    reliable=counts.min(axis=1).ge(10)&differences.notna()
    shown=differences.where(reliable)
    labels=['Jan–mrt','Apr–jun','Jul–sep','Okt–dec']
    fig=go.Figure(go.Bar(x=labels,y=shown,marker_color=[RED if pd.notna(v) and v>=0 else BLUE for v in shown],text=[f'{v:+.1f}' if pd.notna(v) else '' for v in shown],textposition='outside',customdata=counts[['Meer wind','Minder wind']].to_numpy(),hovertemplate='%{x}: %{y:+.1f} procentpunt<br>Meer wind: %{customdata[0]:.0f} dagen<br>Minder wind: %{customdata[1]:.0f} dagen<extra></extra>',showlegend=False))
    positive=int(shown.gt(0).sum());available=int(shown.notna().sum())
    title=f'{group}: meer wind gaat in {positive} van {available} vergelijkbare kwartalen samen met meer vertraging' if available else f'{group}: te weinig dagen voor een betrouwbare kwartaalvergelijking'
    fig.update_layout(title=title,xaxis_title=f'Kwartalen van {year}',yaxis_title='Verschil in vertraagd aandeel (procentpunt)')
    fig.add_hline(y=0,line_color=DARK,line_width=1.5)
    for i,v in enumerate(shown):
        if pd.isna(v):
            fig.add_annotation(x=labels[i],y=0,text='Te weinig dagen',showarrow=False,yshift=18,font=dict(color='#64717B',size=11))
    chart(fig,height=380)
    st.caption('Rood boven nul = bij meer wind vaker vertraging. Blauw onder nul = bij meer wind minder vaak vertraging. Bijvoorbeeld +5 betekent 5 procentpunt meer vertraagde landingen, niet 5 minuten vertraging.')
    st.caption('Een balk verschijnt alleen als beide windgroepen minstens 10 dagen bevatten. Elke dag weegt even zwaar. Vergelijken binnen een kwartaal beperkt seizoensverschillen, maar corrigeert niet voor route, maatschappij of drukte en bewijst geen windoorzaak.')
    st.caption(' · '.join(f'{labels[i-1]}: {int(counts.loc[i,"Meer wind"])} dagen met meer wind / {int(counts.loc[i,"Minder wind"])} met minder wind' for i in counts.index))

elif PAGE=='Het coronajaar':
    header('03 / een ander systeem','Van een druk 2019 naar een stil 2020','Bekijk eerst dezelfde verbindingen in beide jaren, en daarna wanneer het verkeer en de vertraging veranderen.')
    region=st.sidebar.selectbox('Kaartgebied',['Europa','Wereld'],key='map_region')
    map_years=st.sidebar.multiselect('Jaren op de kaart',[2019,2020],default=[2019,2020],key='map_years')
    movement=st.sidebar.radio('Beweging',['Beide','Landing','Vertrek'],key='corona_movement')
    x=D if movement=='Beide' else D.loc[D.beweging.eq(movement)]
    totals=x.groupby('jaar').size();fall=1-totals[2020]/totals[2019]
    cards=st.columns(3)
    cards[0].metric('Bewegingen in 2019',num(totals[2019]))
    cards[1].metric('Bewegingen in 2020',num(totals[2020]))
    cards[2].metric('Minder verkeer in 2020',percent(fall))
    story(f'Het geregistreerde verkeer daalt in 2020 met <b>{percent(fall)}</b>. De kaarten vergelijken <b>dezelfde doelbewust gekozen verbindingen</b>. De tijdgrafieken eronder tonen beide jaren en markeren maart 2020 als pandemiereferentie.')
    st.subheader('Waar krimpt het netwerk het sterkst?')
    ap=pd.read_csv(Path(__file__).parent/'airports-extended.dat',header=None,na_values=[r'\N'])
    europe=set(ap.loc[ap[11].fillna('').str.startswith('Europe/'),5].dropna())
    eligible=x.ICAO.notna() & (x['Org/Des'].isin(europe) if region=='Europa' else True)
    routes=x.loc[eligible].groupby(['Org/Des','jaar']).size().unstack('jaar',fill_value=0).reindex(columns=[2019,2020],fill_value=0)
    if region=='Europa':
        top=routes.nlargest(15,2019).copy()
    else:
        # Show global reach deliberately: busy routes plus busiest beyond Europe.
        chosen=list(routes.nlargest(10,2019).index)
        overseas=routes.loc[~routes.index.isin(europe)].nlargest(5,2019).index
        chosen=list(dict.fromkeys(chosen+list(overseas)))
        top=routes.loc[chosen].copy()
    top['afname']=100*(1-top[2020]/top[2019])
    top=top.join(D[['Org/Des','City','Latitude','Longitude']].drop_duplicates().set_index('Org/Des'))
    top['code']=[airport_code(i) for i in top.index]
    extreme=top.afname.nlargest(2).index
    winner=top.loc[top.afname.idxmax()]
    st.write(f'**{winner.City} ({airport_code(winner.name)})** krimpt het sterkst binnen deze selectie: **{winner.afname:.1f}%** minder bewegingen. De twee sterkste krimpers zijn in beide kaarten rood; de andere routes geven grijze context.')
    if not map_years:
        st.info('Kies links minstens één kaartjaar. De tijdgrafieken blijven beide jaren tonen.')
    maps=st.columns(len(map_years)) if map_years else []
    size_ref=2*top[[2019,2020]].to_numpy().max()/32**2
    for panel,yy in zip(maps,sorted(map_years)):
        with panel:
            st.markdown(f'#### {yy} · {num(top[yy].sum())} bewegingen op deze routes')
            fig=go.Figure()
            for _,row in top.iterrows():
                fig.add_trace(go.Scattermap(lon=[8.54917,row.Longitude],lat=[47.46472,row.Latitude],mode='lines',line=dict(width=1,color='#CBD1D3'),showlegend=False,hoverinfo='skip'))
            # No minimum marker size: a vanished route must not look like traffic.
            fig.add_trace(go.Scattermap(lon=top.Longitude,lat=top.Latitude,mode='markers+text',text=[row.code if idx in extreme else '' for idx,row in top.iterrows()],textposition='top right',marker=dict(size=top[yy],sizemode='area',sizeref=size_ref,color=[RED if idx in extreme else '#8D9BA4' for idx in top.index]),customdata=top[['code','City',yy,'afname']],hovertemplate='%{customdata[1]} (%{customdata[0]})<br>Bewegingen: %{customdata[2]:,.0f}<br>Krimp 2020: %{customdata[3]:.1f}%<extra></extra>',showlegend=False))
            fig.add_trace(go.Scattermap(lon=[8.54917],lat=[47.46472],mode='markers+text',marker=dict(color=DARK,size=10),text=['ZRH'],textposition='bottom right',showlegend=False))
            fig.update_layout(map=dict(style='carto-positron',center=dict(lat=49,lon=9) if region=='Europa' else dict(lat=25,lon=10),zoom=2.4 if region=='Europa' else .2),showlegend=False,margin=dict(l=0,r=0,t=0,b=0),height=400)
            st.plotly_chart(fig,use_container_width=True,key=f'map_{yy}',config={'displaylogo':False})
    selection='de 15 drukste Europese routes van 2019' if region=='Europa' else 'de 10 drukste routes plus de 5 drukste buiten Europa in 2019'
    st.caption(f'Selectie: {selection}, met betrouwbare locaties. Zo toont de wereldkaart ook het intercontinentale netwerk. Kaartjaren gebruiken dezelfde selectie, zoom en puntoppervlakschaal. Rood = de twee grootste procentuele krimpers; grijs = context. Lijnen zijn schematisch. CARTO/OpenStreetMap.')
    st.divider();st.subheader('Wanneer begint het verschil zichtbaar te worden?')
    # A chronological axis makes the event marker apply to 2020 alone.
    source_dates=pd.date_range('2019-01-01','2020-12-31')
    day_counts=x.groupby('datum').size().reindex(source_dates)
    weekly=day_counts.resample('W-SUN').sum(min_count=1)
    fig=go.Figure()
    for yy,col in [(2019,GREY),(2020,PURPLE)]:
        part=weekly.loc[weekly.index.year==yy]
        fig.add_trace(go.Scatter(x=part.index,y=part,name=str(yy),mode='lines',line=dict(color=col,width=2.5),connectgaps=False))
    event='2020-03-11'
    fig.add_vline(x=event,line_color=RED,line_dash='dash',line_width=2)
    fig.add_annotation(x=event,y=.98,yref='paper',text='11 maart 2020<br>WHO: pandemie',showarrow=False,xanchor='left',xshift=8,font=dict(color=RED))
    fig.update_layout(title='Na maart 2020 zakt het geregistreerde verkeer sterk terug',xaxis_title='2019 en 2020 op één tijdlijn',yaxis_title='Bewegingen per week')
    chart(fig,height=410)
    st.caption('Weektotalen van geregistreerde bewegingen, zonder ontbrekende dagen automatisch als nul in te vullen. De laatste week kan onvolledig zijn. De rode lijn is een historische referentie, niet de eerste besmetting of de datum van alle reisbeperkingen.')
    st.markdown('[Referentie: WHO-aanduiding als pandemie op 11 maart 2020](https://www.who.int/news-room/speeches/item/who-director-general-s-opening-remarks-at-the-media-briefing-on-covid-19---11-march-2020)')
    valid=x.loc[x.geldig]
    wd=valid.groupby('datum').agg(late=('te_laat','sum'),n=('FLT','size')).reindex(source_dates)
    weeks=wd.resample('W-SUN').sum(min_count=1)
    weeks['p']=100*weeks.late/weeks.n
    fig=go.Figure()
    for yy,col in [(2019,GREY),(2020,TEAL)]:
        part=weeks.loc[weeks.index.year==yy]
        fig.add_trace(go.Scatter(x=part.index,y=part.p,name=str(yy),mode='lines',line=dict(color=col,width=2.5),connectgaps=False))
    fig.add_vline(x=event,line_color=RED,line_dash='dash',line_width=2)
    fig.update_layout(title='Ook het aandeel vertraagde vluchten verandert in 2020',xaxis_title='2019 en 2020 op één tijdlijn',yaxis_title='≥15 minuten vertraagd per week (%)')
    chart(fig)
    st.caption('Een kleiner vertraagd aandeel kan samenhangen met minder drukte én een andere mix van overblijvende routes en toestellen. Dit rooster bewijst geen afzonderlijk corona-effect.')
    rt=x.groupby(['Org/Des','jaar']).size().unstack('jaar',fill_value=0).reindex(columns=[2019,2020],fill_value=0)
    route=st.sidebar.selectbox('Verbinding voor de jaarvergelijking',list(rt.sort_values(2019,ascending=False).index[:40]),format_func=airport_label)
    st.subheader(f'Dezelfde verbinding vergelijken: {airport_label(route)}')
    z=valid.loc[valid['Org/Des'].eq(route)].groupby('jaar').agg(bewegingen=('FLT','size'),vertraagd=('te_laat','mean'))
    for yy in [2019,2020]:
        if yy in z.index:
            row=z.loc[yy];st.write(f'**{yy}:** {num(row.bewegingen)} bewegingen met bruikbare tijden; **{percent(row.vertraagd)}** minstens 15 minuten vertraagd.')
        else:st.write(f'**{yy}:** geen bewegingen met bruikbare tijden voor deze selectie.')



st.divider()
st.markdown('**Van bron naar betrouwbare vergelijking**')
st.caption(f'{num(A["bronrijen"])} bronrijen gecontroleerd; {A["middernachtcorrecties"]} duidelijke middernachtovergangen hersteld. {A["ambigue_tijden"]} onduidelijke tijdverschillen tellen mee voor verkeersvolume, maar niet voor vertraging. Koppelingen op luchthaven en datum voegen geen extra vluchten toe.')
st.caption('Dagweer komt van Meteostat-station Zürich-Kloten. Luchthavenlocaties komen van OpenFlights; de vluchtplanning is aangeleverd door HvA. De losse Amsterdam–Barcelona-profielen horen niet bij deze Zürich-vluchten en zijn daarom niet samengevoegd. Verbanden zijn beschrijvend; ze bewijzen geen oorzaak.')
st.markdown('[Weerbron: Meteostat](https://dev.meteostat.net/bulk/daily.html) · [Luchthavenbron: OpenFlights](https://github.com/jpatokal/openflights/blob/master/data/airports-extended.dat)')

st.download_button('Bronnen en methodische toelichting', '- **Rooster:** `schedule_airport.csv` via Brightspace / HvA, door de groep aangeleverd. 323.461 geregistreerde bewegingen, 2019–2020. Het originele CSV-bestand is verliesvrij opnieuw gzip-gecomprimeerd. Publicatierechten van cursusmateriaal blijven bij de oorspronkelijke rechthebbende.\n- **Luchthavens:** [OpenFlights / oorspronkelijke database](https://github.com/jpatokal/openflights/blob/master/data/airports-extended.dat), blob `dc3392c076b769fc28f31fc798cba4af05a5f35b`, opgehaald 5 oktober 2026. 12.668 locaties; 8.264 airports, ook stations/havens/onbekend. [Kaggle-lesbron](https://www.kaggle.com/datasets/open-flights/airports-train-stations-and-ferry-terminals) vereist inloggen. Daarom is de oorspronkelijke database gebruikt, niet het semikolon/decimale-komma lesbestand. Deze bron wordt gelezen met komma en decimale punt; join op **ICAO**, nooit op IATA. [OpenFlights data en ODbL/Database Contents-licentie](https://openflights.org/data.html). De meegeleverde luchthavenbron behoudt die licentie; deze appcode verandert die niet.\n- **Weer:** Meteostat, station **06670 / Zürich-Kloten**, dagbestanden [2019](https://data.meteostat.net/daily/2019/06670.csv.gz) en [2020](https://data.meteostat.net/daily/2020/06670.csv.gz), opgehaald 5 oktober 2026. [Station](https://meteostat.net/en/station/06670), [bestandsformaat](https://dev.meteostat.net/data/timeseries/daily.html), [eenheden](https://dev.meteostat.net/api/stations/daily.html), [licentie](https://dev.meteostat.net/terms.html). Wind km/h, temperatuur °C, neerslag mm, luchtdruk hPa. Bestanden bevatten bronkolommen; Meteostat kan modeldata gebruiken om observatiegaten aan te vullen. De actuele bron vermeldt CC BY-NC 4.0; onderwijsgebruik, geen commerciële verspreiding. De oude link in de opdracht is vervangen door de huidige jaarlijkse endpoint.\n- **Optionele vluchtprofielen:** `flightdata.zip` via HvA, 14 Excel-bestanden voor 7 Amsterdam–Barcelona-vluchten. Bewust niet gekoppeld aan Zürich: andere route en geen betrouwbare joinsleutel. Dit project claimt niet dat vier datasets aan elkaar gekoppeld zijn.\n- **Kaart:** [Plotly Scattermap](https://plotly.com/python/tile-scatter-maps/), MapLibre met CARTO positron / OpenStreetMap; kaartattributie staat op de kaart. De locaties komen uit OpenFlights, niet uit een geschatte positie.\n\n**Code en methoden:** projectcode is voor deze opdracht met hulp van Codex gemaakt en aangepast aan de eigen data; er zijn geen letterlijk overgenomen StackOverflow-snippets. Gebruikte API-documentatie: [Streamlit cache_data](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data), [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing), [pandas merge/validate](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html), [Plotly graph objects](https://plotly.com/python/graph-objects/), [scikit-learn GradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html), [MAE](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_error.html) en [permutatiebelang](https://scikit-learn.org/stable/modules/permutation_importance.html). De groep moet verwerking, bootstrap, temporele splitsing en MAE zelf kunnen uitleggen.\n', 'SOURCES.md', 'text/markdown')
st.caption('Minor Data Science · Zürich Airport 2019–2020 · historische voorspelling')
