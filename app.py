"""Streamlit-dashboard Zürich, gebouwd rond vragen en onderbouwde bevindingen."""
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from analysis import load_data, daily_frame, fit_forecast, wind_analysis, GROUPS

st.set_page_config(page_title='Zürich | Wind, vertraging & corona',page_icon='✈',layout='wide',initial_sidebar_state='expanded')
ORANGE='#E75C37'; TEAL='#087F83'; GREY='#BCC3C8'; DARK='#202C37'; PURPLE='#705CC5'
PALETTE={'Regionaal':ORANGE,'Narrowbody':GREY,'Widebody':TEAL,'2019':GREY,'2020':ORANGE,'Landing':TEAL,'Vertrek':ORANGE}
st.markdown('''<style>
.stApp {background:#F7F6F2;color:#202C37;}
.block-container {max-width:1250px;padding-top:2.5rem;padding-bottom:3rem;}
h1 {font-weight:750!important;letter-spacing:-1.5px!important;}
h2 {letter-spacing:-.6px!important;} [data-testid="stMetric"] {background:#fff;border-radius:12px;padding:18px;border:1px solid #E2E5E4;}
[data-testid="stMetricValue"] {font-size:2rem;} [data-testid="stSidebar"] {border-right:1px solid #ddd;}
.story {background:#202C37;color:white;padding:24px 28px;border-radius:14px;margin:16px 0 26px;line-height:1.7;font-size:1.08rem;}
.story b {color:#FFA17F;} .eyebrow {color:#64717B;text-transform:uppercase;letter-spacing:2px;font-size:.76rem;margin-bottom:14px;}
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner='Brondata inspecteren en koppelen…')
def data(): return load_data()
@st.cache_data(show_spinner='Voorspelling trainen en toetsen op latere dagen…')
def forecast(daily):
    return fit_forecast(daily)
@st.cache_data
def wind(year,threshold,trim,_df):
    return wind_analysis(_df,year,threshold,trim)

def story(text): st.markdown(f'<div class="story">{text}</div>',unsafe_allow_html=True)
def header(kicker,title,subtitle):
    st.markdown(f'<div class="eyebrow">{kicker}</div>',unsafe_allow_html=True)
    st.title(title); st.markdown(subtitle)
def chart(fig,key=None,height=370):
    fig.update_layout(height=height,font=dict(family='Arial',size=13,color=DARK),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',margin=dict(l=15,r=25,t=60,b=20),legend=dict(orientation='h',y=1.12,x=0),hoverlabel=dict(bgcolor='white'),title_font=dict(size=18))
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

D,W,A=data()
with st.sidebar:
    st.markdown('### ZÜRICH / LSZH')
    st.caption('Van rooster naar inzicht · 2019–2020')
    PAGE=st.radio('Verhaal', ['Vertraging & voorspelling','Wind & vliegtuigtype','Het coronajaar'],label_visibility='collapsed')
    st.divider()
    st.caption('Oranje = aandacht · grijs = context · groenblauw = vergelijking')
    st.caption('Vertraagd: ≥15 minuten. Landing en vertrek worden waar nodig apart geanalyseerd.')
    st.caption('Bronnen: HvA-rooster, Meteostat 06670 en OpenFlights. Alle bronbestanden zijn meegeleverd.')

if PAGE=='Vertraging & voorspelling':
    header('01 / begrijpen → toetsen','Vertraging herkennen én voorspellen','Eerst het patroon per uur; daarna een eerlijke toets: kunnen we morgen de gemiddelde aankomstvertraging voorspellen?')
    year=st.selectbox('Jaar voor de beschrijvende analyse',[2019,2020],key='delay_year')
    x=D.loc[D.jaar.eq(year)&D.geldig]
    h=x.groupby(['uur','beweging']).agg(percentage=('te_laat','mean'),n=('FLT','size')).reset_index()
    reliable=h.loc[h.n.ge(100)]
    if not reliable.empty:
        peak=reliable.loc[reliable.percentage.idxmax()]
        story(f'In {year} heeft <b>{peak.beweging.lower()} rond {int(peak.uur):02d}:00</b> het hoogste aandeel vertraagde vluchten onder uurvakken met minstens 100 bewegingen: <b>{percent(peak.percentage)}</b>. Dat is een patroon in het rooster, geen bewezen effect van het tijdstip.')
    fig=go.Figure()
    for b,col in [('Landing',TEAL),('Vertrek',ORANGE)]:
        hh=h.loc[h.beweging.eq(b)].set_index('uur').reindex(range(24))
        fig.add_trace(go.Scatter(x=hh.index,y=100*hh.percentage,name=b,mode='lines+markers',line=dict(color=col,width=3),customdata=hh.n,hovertemplate='%{x}:00 · %{y:.1f}%<br>n=%{customdata}<extra>%{fullData.name}</extra>',connectgaps=False))
    fig.update_layout(title=f'Op welk uur stapelt vertraging zich op? · {year}',xaxis_title='Gepland lokaal uur',yaxis_title='Vluchten ≥15 minuten vertraagd (%)')
    chart(fig);st.caption('Alleen geldige tijden; aankomst en vertrek apart. Geen lijn over ontbrekende uren. Het dagritme is geen gecontroleerde causale vergelijking.')
    st.divider();st.subheader('De volgende dag: een getoetste voorspelling')
    F=forecast(daily_frame(D,W)); M=F['metrics']; T=F['test']; S=F['stress']; SM=F['stress_metrics']
    gain=100*(M['baseline_MAE']-M['MAE'])/M['baseline_MAE']
    direction='lager' if gain>=0 else 'hoger'
    story(f'De gemiddelde fout is <b>{M["MAE"]:.1f} minuten</b> op {M["dagen"]} ongeziene testdagen. Dat is <b>{abs(gain):.1f}% {direction}</b> dan simpelweg de vertraging van gisteren gebruiken. Het model voorspelt een daggemiddelde; de fout voor een individuele vlucht kan veel groter zijn.')
    c=st.columns(4)
    c[0].metric('Model · MAE',f'{M["MAE"]:.1f} min');c[1].metric('Gisteren als voorspelling',f'{M["baseline_MAE"]:.1f} min');c[2].metric('Vaste trainingsmediaan',f'{M["constant_MAE"]:.1f} min');c[3].metric('Dekking foutband',percent(M['dekking']))
    mode=st.radio('Toetsperiode',['Normaal jaar · okt–dec 2019','Stresstest · 2020'],horizontal=True)
    t=T if mode.startswith('Normaal') else S
    plot_t=t.reindex(pd.date_range(t.index.min(),t.index.max(),freq='D'))
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.bovengrens,line=dict(width=0),showlegend=False,hoverinfo='skip',connectgaps=False))
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.ondergrens,line=dict(width=0),fill='tonexty',fillcolor='rgba(231,92,55,.13)',name='Empirische 90%-foutband',hoverinfo='skip',connectgaps=False))
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.doel,name='Werkelijk',line=dict(color=DARK,width=1.8),connectgaps=False))
    fig.add_trace(go.Scatter(x=plot_t.index,y=plot_t.voorspeld,name='Voorspeld',line=dict(color=ORANGE,width=2.5),connectgaps=False))
    fig.update_layout(title='Waar volgt het model het patroon, en waar mist het pieken?',xaxis_title='Voorspelde dag',yaxis_title='Gemiddelde positieve aankomstvertraging (min)')
    chart(fig,height=420)
    st.caption('Train: jan–aug 2019. Foutband: absolute voorspelfouten in september 2019 (90e percentiel). Test: okt–dec 2019. Model en band blijven vast in 2020. De band is empirisch en biedt geen gegarandeerde dekking bij veranderende omstandigheden.')
    with st.expander('Welke informatie is vóór morgen beschikbaar?'):
        st.write('Voorspelmoment: einde van de voorgaande lokale dag. Invoer: vertraging gisteren en afgelopen zeven dagen, weer gisteren, weekdag, maand, geplande bewegingen en grootteverdeling van morgen. Geen actuele vertraging, gatewissel, vertragingscode of gemeten weer van morgen.')
        st.warning('Dit rooster bevat de geregistreerde bewegingen met geplande én werkelijke tijden; geannuleerde vluchten ontbreken mogelijk. De roosterkenmerken zijn daarom een historische benadering van wat vooraf bekend was. In productie moet een volledig vooraf gepubliceerd rooster worden gebruikt. Weerwaarden kunnen achteraf worden herzien; dit is een historische toets, geen live dienst.')
        st.write(f'Dagen met <10 geldige landingen krijgen geen voorspeldoel. Trainingsdagen: {F["train_n"]}; kalibratiedagen: {F["cal_n"]}. Ontbrekende kenmerken krijgen uitsluitend de trainingsmediaan; ontbrekende doelen worden nooit ingevuld.')
    l,r=st.columns([1,1])
    with l:
        imp=F['importance'].head(6).sort_values('MAE_toename')
        cols=[ORANGE if v==imp.MAE_toename.max() and v>0 else GREY for v in imp.MAE_toename]
        fig=go.Figure(go.Bar(x=imp.MAE_toename,y=imp.kenmerk,orientation='h',marker_color=cols,error_x=dict(type='data',array=imp.spreiding,color=DARK)))
        fig.update_layout(title='Welke invoer helpt op de kalibratiemaand?',xaxis_title='Extra MAE na verwisselen (min)',yaxis_title='')
        chart(fig);st.caption('Permutatiebelang op september, geen causaal effect. Balkjes tonen spreiding over 15 verwisselingen. Correlatie tussen kenmerken kan belang verdelen.')
    with r:
        st.markdown('#### De grootste missers')
        worst=t.reindex(t.fout.abs().sort_values(ascending=False).head(5).index)
        show=worst[['doel','voorspeld','fout']].round(1).rename(columns={'doel':'Werkelijk (min)','voorspeld':'Voorspeld (min)','fout':'Werkelijk − voorspeld'})
        st.dataframe(show,width='stretch')
        st.write('Positieve fout = model onderschat de vertraging. Pieken kunnen samenhangen met storingen, stakingen of plotseling weer; de beschikbare gegevens bevestigen die oorzaak niet.')
        st.write(f'In 2020: MAE **{SM["MAE"]:.1f} min**, tegenover gisteren **{SM["baseline_MAE"]:.1f} min**; dekking **{percent(SM["dekking"])}**.')
    with st.expander('Bekijk één historische voorspelling'):
        chosen=st.selectbox('Testdag',list(t.index),format_func=lambda v:v.strftime('%d-%m-%Y'))
        row=t.loc[chosen]
        st.write(f'Voorspelling: **{row.voorspeld:.1f} min**. Foutband: **{row.ondergrens:.1f}–{row.bovengrens:.1f} min**. Werkelijk: **{row.doel:.1f} min**. Dit is een historische voorspelling met gisteren bekende informatie, geen voorspelling voor een actuele vlucht.')
    st.download_button('Download alle testvoorspellingen',t.to_csv().encode(),'testvoorspellingen.csv','text/csv')

elif PAGE=='Wind & vliegtuigtype':
    header('02 / de hypothese','Maakt een groter vliegtuig wind minder voelbaar?','Hypothese: op dagen met meer wind neemt vertraging bij kleinere vliegtuigtypes sterker toe dan bij widebody-types.')
    c=st.columns(3)
    year=c[0].selectbox('Jaar',[2019,2020],key='wind_year')
    threshold=c[1].slider('Daggemiddelde wind: grens (km/h)',10,25,15)
    trim=c[2].checkbox('Gevoeligheid: zonder |vertraging| >180 min',False)
    summary,diff,x=wind(year,threshold,trim,D)
    rdelta=diff.set_index('groep').verschil_pp
    outcome=f'Regionale types: <b>{rdelta.get("Regionaal",float("nan")):+.1f} procentpunt</b>; widebody-types: <b>{rdelta.get("Widebody",float("nan")):+.1f} procentpunt</b> verschil bij meer wind. '
    story(outcome+f'We vergelijken <b>alleen landingen in {year}</b>. Oranje markeert regionale types en groenblauw widebody-types; narrowbody is context. “Meer wind” betekent hier een <b>daggemiddelde ≥{threshold} km/h</b> — niet de wind tijdens de landing.')
    st.warning('Grootteklasse is geen gemeten landingsgewicht. Zonder actuele massa, windrichting en uurweer kunnen we niet vaststellen of zwaardere vliegtuigen beter kunnen landen. Uitgevallen of uitgeweken vluchten zijn mogelijk afwezig: ook daardoor kan de groep overblijvende landingen gunstiger lijken.')
    fig=go.Figure()
    for wg,symbol in [('Minder wind','circle-open'),('Meer wind','circle')]:
        b=summary.loc[summary.windgroep.eq(wg)].set_index('groep').reindex(GROUPS)
        fig.add_trace(go.Scatter(x=b.index,y=b.percentage,mode='markers',name=wg,marker=dict(size=16,symbol=symbol,color=[PALETTE[z] for z in b.index],line=dict(width=2)),error_y=dict(type='data',array=b.hoog-b.percentage,arrayminus=b.percentage-b.laag),customdata=b[['dagen','vluchten']],hovertemplate='%{x}: %{y:.1f}%<br>%{customdata[0]} dagen · %{customdata[1]} landingen<extra>%{fullData.name}</extra>'))
    fig.update_layout(title='Vertraagde landingen: minder wind tegenover meer wind',yaxis_title='Gemiddeld dagelijks aandeel ≥15 minuten vertraagd (%)',xaxis_title='Grootteklasse')
    chart(fig)
    st.caption('Elke dag weegt even zwaar per klasse. Punten: gemiddeld dagelijks aandeel. Strepen: 95%-bootstrapinterval, 1.500 hersteekproeven van hele dagen. Open punt = minder wind, gevuld punt = meer wind. Geen causale schatting; verschillen in routes, maatschappijen, drukte en seizoen blijven aanwezig.')
    if not diff.empty:
        regional=diff.loc[diff.groep.eq('Regionaal')]
        heavy=diff.loc[diff.groep.eq('Widebody')]
        if not regional.empty and not heavy.empty:
            a=regional.iloc[0];b=heavy.iloc[0]
            st.markdown(f'**Bij meer wind verandert het vertraagde aandeel met {a.verschil_pp:+.1f} procentpunt bij regionale types en {b.verschil_pp:+.1f} bij widebody-types.**')
            st.write('Dit patroon ondersteunt de richting van de hypothese beschrijvend.' if a.verschil_pp>b.verschil_pp else 'Deze vergelijking ondersteunt de voorgestelde richting van de hypothese niet. Ook dat is een onderzoeksresultaat.')
    with st.expander('Controleer aantallen en vliegtuigindeling'):
        st.dataframe(summary.round(2),width='stretch',hide_index=True)
        st.dataframe(D[['ACT','groep']].drop_duplicates().sort_values(['groep','ACT']),hide_index=True,width='stretch')
        st.write('Widebody en narrowbody zijn toestelconfiguraties; de regionale groep bevat kleinere jets en turboprops. Er worden geen kilogrammen geschat. Onbekende types worden buiten deze vergelijking gehouden en gerapporteerd bij de inspectie.')
    st.subheader('Is het een windpatroon of een seizoenspatroon?')
    daily=x.groupby(['datum','kwartaal','groep']).agg(late=('te_laat','mean'),wind=('wspd','first')).reset_index()
    daily['windgroep']=np.where(daily.wind.ge(threshold),'Meer wind','Minder wind')
    q=daily.groupby(['kwartaal','groep','windgroep']).agg(p=('late','mean'),dagen=('datum','size')).reset_index()
    q['p']=100*q.p
    q.loc[q.dagen.lt(10),'p']=np.nan
    fig=px.line(q,x='kwartaal',y='p',color='groep',line_dash='windgroep',markers=True,color_discrete_map=PALETTE,custom_data=['dagen'],labels={'p':'Dagelijks vertraagd aandeel (%)','kwartaal':'Kwartaal','groep':'Klasse','windgroep':'Wind'},title='Controle per kwartaal: blijft de vergelijking overeind?')
    fig.update_traces(connectgaps=False);chart(fig)
    st.caption('Een kwartaalgroep met minder dan 10 dagen is zwak onderbouwd. Bekijk de tabel; deze uitsplitsing corrigeert niet voor route of maatschappij.')
    with st.expander('Aantal dagen per kwartaalgroep'):st.dataframe(q.round(1),hide_index=True)

elif PAGE=='Het coronajaar':
    header('03 / een ander systeem','2020 verandert het verkeer én de vergelijking','Vergelijk dezelfde maanden, dezelfde bewegingen en dezelfde routes. Een gezamenlijk jaargemiddelde verbergt de breuk.')
    tab_trend,tab_map=st.tabs(['Verkeer & vertraging','Europese routekaart'])
    with tab_trend:
        counts=D.groupby('jaar').size();fall=1-counts[2020]/counts[2019]
        story(f'Het geregistreerde verkeer daalt met <b>{percent(fall)}</b>. De volgende vraag is niet alleen hoeveel vluchten verdwijnen, maar ook <b>welke verbindingen overblijven</b> en hoe hun vertraging verandert.')
        movement=st.radio('Beweging',['Beide','Landing','Vertrek'],horizontal=True,key='corona_movement')
        x=D if movement=='Beide' else D.loc[D.beweging.eq(movement)]
        m=monthly_counts(x)
        fig=go.Figure()
        for y in [2019,2020]:
            for b in ['Landing','Vertrek']:
                if movement!='Beide' and b!=movement:continue
                z=m.loc[m.jaar.eq(y)&m.beweging.eq(b)].set_index('maand').reindex(range(1,13))
                fig.add_trace(go.Scatter(x=z.index,y=z.vluchten,name=f'{y} · {b}',mode='lines+markers',line=dict(color=ORANGE if y==2020 else GREY,width=3,dash='solid' if b=='Landing' else 'dash'),connectgaps=False))
        fig.update_layout(title='Maandelijkse bewegingen: normale zomer tegenover corona',xaxis_title='Maand',yaxis_title='Geregistreerde vluchtbewegingen')
        fig.update_xaxes(dtick=1);chart(fig)
        st.caption('Kleur markeert het jaar; lijnstijl maakt landing/vertrek zichtbaar. Maanden zijn dezelfde noemer, maar hebben verschillende aantallen dagen. De aantallen komen uit het aangeleverde rooster.')
        l,r=st.columns(2)
        with l:
            p=x.loc[x.geldig].groupby(['jaar','maand']).te_laat.mean().mul(100).rename('percentage').reset_index()
            fig=go.Figure()
            for y,col in [(2019,GREY),(2020,ORANGE)]:
                z=p.loc[p.jaar.eq(y)].set_index('maand').reindex(range(1,13))
                fig.add_trace(go.Scatter(x=z.index,y=z.percentage,name=str(y),mode='lines+markers',line=dict(color=col,width=3),connectgaps=False))
            fig.update_layout(title='Vertraagd aandeel per maand',xaxis_title='Maand',yaxis_title='≥15 minuten vertraagd (%)');chart(fig)
        with r:
            rt=x.groupby(['Org/Des','jaar']).size().unstack('jaar',fill_value=0).reindex(columns=[2019,2020],fill_value=0)
            top=rt.sort_values(2019,ascending=False).head(10).copy();top['afname']=100*(1-top[2020]/top[2019])
            names=D[['Org/Des','City']].drop_duplicates().set_index('Org/Des').City
            top['label']=[f'{names.get(i) if pd.notna(names.get(i)) else i} · {i}' for i in top.index]
            highlight=top.afname.nlargest(2).index
            colors=[ORANGE if i in highlight else GREY for i in top.index]
            fig=go.Figure(go.Bar(x=top.afname,y=top.label,orientation='h',marker_color=colors,text=top.afname.round(1).astype(str)+'%',textposition='outside'))
            fig.update_layout(title='Twee sterkste krimpers binnen de top 10 van 2019',xaxis_title='Minder bewegingen in 2020 (%)',yaxis_title='');fig.update_yaxes(autorange='reversed');chart(fig,height=430)
            st.caption('Eerst top 10 selecteren op volume 2019, daarna de twee grootste procentuele dalingen markeren. Geen willekeurige keuze van opvallende routes.')
        st.subheader('Vergelijk dezelfde verbindingen')
        route=st.selectbox('Route',list(rt.sort_values(2019,ascending=False).index[:40]),format_func=lambda i:f'{i} · {names.get(i) if pd.notna(names.get(i)) else "naam ontbreekt"}')
        z=x.loc[x['Org/Des'].eq(route)&x.geldig].groupby('jaar').agg(bewegingen=('FLT','size'),vertraagd=('te_laat','mean'),mediaan=('vertraging','median'))
        z['vertraagd']=100*z.vertraagd
        st.dataframe(z.round(1).rename(columns={'vertraagd':'Vertraagd (%)','mediaan':'Mediaan verschil (min)'}),width='stretch')
        st.caption('Dezelfde route maakt de vergelijking specifieker; veranderingen in tijdstip, toesteltype en maatschappij blijven mogelijke verklaringen. Het rooster bewijst geen afzonderlijk corona-effect op vertraging.')

    with tab_map:
        st.subheader('Welke drukke Europese routes krompen het sterkst?')
        st.caption('Europa is hier operationeel gekozen als luchthavens met een Europe/*-tijdzone in de bron. De selectie is vast op 2019; een verdwijnende route blijft daardoor zichtbaar.')
        ap=pd.read_csv(Path(__file__).parent/'airports-extended.dat',header=None,na_values=[r'\N'])
        europe=set(ap.loc[ap[11].fillna('').str.startswith('Europe/'),5].dropna())
        x=D.loc[D['Org/Des'].isin(europe)&D.ICAO.notna()]
        rt=x.groupby(['Org/Des','jaar']).size().unstack('jaar',fill_value=0).reindex(columns=[2019,2020],fill_value=0)
        top=rt.nlargest(15,2019).copy();top['afname']=100*(1-top[2020]/top[2019])
        top=top.join(D[['Org/Des','City','Name','Latitude','Longitude']].drop_duplicates().set_index('Org/Des'))
        extreme=top.afname.nlargest(2).index
        if len(top):
            winner=top.loc[top.afname.idxmax()]
            story(f'Binnen deze vaste groep krimpt <b>{winner.City}</b> het sterkst: <b>{winner.afname:.1f}%</b> minder bewegingen. De kaart toont <b>15 geselecteerde verbindingen</b>; kleur staat voor procentuele krimp en puntoppervlak voor volume in 2019.')
        # MapLibre open tiles; no Mapbox token. Marker AREA scales with 2019 volume.
        top['code']=top.index;top['label']=[f'{row.City} ({idx})' if idx in extreme else '' for idx,row in top.iterrows()]
        fig=go.Figure()
        for _,row in top.iterrows():
            fig.add_trace(go.Scattermap(lon=[8.54917,row.Longitude],lat=[47.46472,row.Latitude],mode='lines',line=dict(width=1,color='#C5CDCF'),showlegend=False,hoverinfo='skip'))
        fig.add_trace(go.Scattermap(lon=top.Longitude,lat=top.Latitude,mode='markers+text',text=top.label,textposition='top right',marker=dict(size=top[2019],sizemode='area',sizeref=2*top[2019].max()/30**2,sizemin=6,color=top.afname,colorscale=[[0,'#FFE6C9'],[.5,'#F89860'],[1,'#B83A20']],cmin=0,cmax=100,showscale=True,colorbar=dict(title='Krimp (%)')),customdata=top[['code','City',2019,2020,'afname']],hovertemplate='%{customdata[1]} · %{customdata[0]}<br>2019: %{customdata[2]:,}<br>2020: %{customdata[3]:,}<br>Krimp: %{customdata[4]:.1f}%<extra></extra>',name='Europese verbinding'))
        fig.add_trace(go.Scattermap(lon=[8.54917],lat=[47.46472],mode='markers+text',marker=dict(color=DARK,size=12),text=['Zürich'],textposition='bottom right',name='Zürich',showlegend=False))
        fig.update_layout(map=dict(style='carto-positron',center=dict(lat=49,lon=9),zoom=2.8),title='Top 15 van 2019 · kleur toont krimp in 2020',height=560)
        st.plotly_chart(fig,use_container_width=True,config={'displaylogo':False})
        st.caption('Donkerder oranje = sterkere krimp (vaste schaal 0–100%). Groter puntoppervlak = meer bewegingen in 2019; geen radius evenredig aan volume. Alleen de twee grootste krimpers krijgen een tekstlabel. Lijnen zijn schematische verbindingen, geen echte vliegroutes. Achtergrond: CARTO/OpenStreetMap.')
        st.dataframe(top[['City',2019,2020,'afname']].sort_values('afname',ascending=False).round(1).rename(columns={'City':'Stad',2019:'2019',2020:'2020','afname':'Krimp (%)'}),width='stretch')
        st.info(f'{A["bestemmingscodes"]-A["icao_match_codes"]} herkomst-/bestemmingscodes koppelen niet aan een unieke luchthaven in deze bronversie. Ze worden niet op een verzonnen locatie geplaatst. Details staan onderaan bij Data-inspectie, bronnen & verantwoording.')


st.divider()
with st.expander('Data-inspectie, bronnen & verantwoording'):
    story(f'<b>{num(A["bronrijen"])}</b> bronrijen → <b>{num(A["rijen_na_joins"])}</b> rijen na gecontroleerde joins. Geen ongecontroleerde vermenigvuldiging van vluchten. <b>{A["ambigue_tijden"]}</b> tijden zijn apart gemarkeerd en alleen uitgesloten van vertragingsanalyses.')
    edits=pd.DataFrame([
        ['Volledig dubbele rijen',A['volledig_dubbele_rijen'],'Alleen exacte duplicaten verwijderen; geen deduplicatie op alleen vluchtnummer.'],
        ['Middernacht',A['middernachtcorrecties'],'Gepland ≥20:00 en werkelijk ≤04:00 bij verschil <−12 uur: +24 uur.'],
        ['Ambigue tijdverschillen',A['ambigue_tijden'],'|verschil| >6 uur: behouden voor aantallen, uitsluiten van vertraging; werkelijke datum ontbreekt.'],
        ['Niet-gekoppelde vluchten',A['bronrijen']-A['icao_match_vluchten'],'Behouden in tijd-/vertragingsanalyse; geen kaartpunt.'],
        ['Dubbele ICAO bij luchthavenbron',A['dubbele_airport_icao'],'Ambigue ICAOs volledig uitsluiten van join; many_to_one-controle.'],
        ['Weerdata',A['weer_dagen'],'Join op lokale kalenderdatum; many_to_one; geen doelen invullen.'],
    ],columns=['Controle','Aantal','Behandeling'])
    st.dataframe(edits,hide_index=True,width='stretch')
    st.subheader('Ontbrekend is niet hetzelfde als nul')
    st.write('“−” in gates/vertragingscodes wordt ontbrekend. Org/Des ontbreekt bij een deel van de bewegingen. Deze rijen blijven meetellen; alleen hun locatie is onbekend. Weer ontbreekt op sommige neerslagdagen. Voor de windanalyse wordt alleen een gemeten dagwind vereist; voor het voorspelmodel komt imputatie uitsluitend uit de training.')
    st.markdown('**Exacte ontbrekende waarden en niet-gekoppelde codes**')
    st.dataframe(pd.Series(A['ontbrekend_per_kolom'],name='Ontbrekend').to_frame(),width='stretch')
    st.write('Weer:',A['weer_ontbrekend']);st.write('Niet-gekoppelde codes:',A['niet_gekoppelde_codes']);st.write('Onbekende vliegtuigtypes:',A['onbekende_types'])
    st.subheader('Uitschieters behouden, conclusie controleren')
    valid=D.loc[D.geldig]
    st.write(f'Gemiddeld getekend tijdverschil met ambigue tijden: **{A["gemiddelde_met_ambigue"]:.2f} min**; zonder: **{A["gemiddelde_zonder_ambigue"]:.2f} min**. Grote maar interpreteerbare vertragingen blijven staan; er wordt niet op basis van de gewenste uitkomst opgeschoond.')
    sens=valid[['jaar','FLT','vertraging','te_laat']].assign(selectie='Alle geldige tijden')
    comparison=pd.concat([sens,valid.loc[valid.vertraging.abs().le(180),['jaar','FLT','vertraging','te_laat']].assign(selectie='Zonder |verschil| >180 min')]).groupby(['selectie','jaar']).agg(n=('FLT','size'),gemiddeld=('vertraging','mean'),mediaan=('vertraging','median'),vertraagd=('te_laat','mean'))
    comparison['vertraagd']*=100
    st.dataframe(comparison.round(2),width='stretch')
    st.caption('De windpagina heeft dezelfde gevoeligheidskeuze. Deze uitschietercontrole gaat over beschrijvende conclusies; de getoonde modeltest blijft op alle geldige testdagen staan.')
    st.markdown('**Welke tijdverschillen zijn ambigu?**')
    st.dataframe(D.loc[D.tijd_ambigu,['STD','FLT','STA_STD_ltc','ATA_ATD_ltc','LSV','vertraging']],hide_index=True,width='stretch')
    st.subheader('Waarom de vluchtprofielen niet worden gemerged')
    st.write('flightdata.zip bevat zeven Amsterdam–Barcelona-vluchten, op seconden- en 30-secondenniveau. Dat zijn geen Zürich-vluchten en er is geen betrouwbare sleutel naar dit rooster. Het toevoegen ervan zou een schijnkoppeling opleveren. De kernanalyse gebruikt daarom drie bij elkaar passende datasets: rooster, luchthavenlocaties en Zürich-weer. De vierde bron is geïnspecteerd en bewust buiten de onderzoeksscope gehouden.')
    st.subheader('Wat de data niet kunnen bewijzen')
    st.write('Geen landingsmassa, geen uurlijkse dwarswind, geen volledige annulerings-/uitwijkregistratie en geen experimentele controle. Wind wordt op dagbasis geanalyseerd. Een verband kan ontstaan door drukte, seizoen, route, maatschappij of selectie van overblijvende vluchten. Gate- en vertragingscodes zijn geen bewijs van een onafhankelijke oorzaak.')
    st.subheader('Bronnen & gebruikte documentatie')
    st.markdown((Path(__file__).parent/'SOURCES.md').read_text())
    st.download_button('Download inspectierapport',(Path(__file__).parent/'inspection.json').read_bytes(),'inspection.json','application/json')
    st.markdown('**Presentatie in maximaal 10 minuten**')
    st.markdown((Path(__file__).parent/'PRESENTATIE.md').read_text())

st.divider();st.caption('Minor Data Science · Zürich Airport 2019–2020 · beschrijvende verbanden en een historische voorspelling, geen operationeel vliegadvies.')
