import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title='AI ESG Assessment | Demo', page_icon='◈', layout='wide')
DATA=json.loads((Path(__file__).parent/'workbook_data.json').read_text(encoding='utf-8'))
METRICS=DATA['metrics']; PILLARS={'Environmental':['Carbon Intensity'],'Social':['Accessibility','Bias Mitigation'],'Governance':['Transparency','Auditability','Logging & Monitoring']}
ASSESS=['Not Implemented','Partially Implemented','Fully Implemented']; EVID=['Self Declared','Internally Verified','Independently Verified']; AVAL={ASSESS[0]:0,ASSESS[1]:.5,ASSESS[2]:1}; EVAL={EVID[0]:0,EVID[1]:.5,EVID[2]:1}

st.markdown('''<style>.block-container{padding-top:1.3rem;max-width:1350px}.stMetric{background:#f3f6fa;border-radius:12px;padding:15px;border:1px solid #e3e8ee}h1,h2,h3{letter-spacing:-.03em}.stButton button{border-radius:9px}</style>''',unsafe_allow_html=True)
if 'records' not in st.session_state:st.session_state.records=json.loads(json.dumps(METRICS))
if 'carbon' not in st.session_state:st.session_state.carbon=DATA['carbon'].copy()
if 'status' not in st.session_state:st.session_state.status='In Progress'
if 'role' not in st.session_state:st.session_state.role='Risk Engineer / Assessor'
if 'page' not in st.session_state:st.session_state.page='Overview'
if 'note' not in st.session_state:st.session_state.note=''

def score_metric(rows):
 applicable=[r for r in rows if r['na']!='Yes'];den=sum(float(r['weight']) for r in applicable)
 score=sum(float(r['weight'])*AVAL.get(r['assessment'],0) for r in applicable if r['assessment'] in AVAL)/den*100 if den else None
 coverage=len(applicable)/len(rows)*100 if rows else None
 evidence=[r for r in applicable if r['evidence'] in EVAL]
 confidence=sum(EVAL[r['evidence']] for r in evidence)/len(evidence)*100 if evidence else None
 if coverage is None or confidence is None:quality='Not rated'
 elif coverage>=80 and confidence>=80:quality='High'
 elif coverage<50 or confidence<50:quality='Low'
 else:quality='Medium'
 maturity=('Initial' if score<=20 else 'Developing' if score<=40 else 'Defined' if score<=60 else 'Managed' if score<=80 else 'Optimized') if score is not None else 'N/A'
 priorities=sorted([(AVAL[r['assessment']],i,r) for i,r in enumerate(rows) if r['na']!='Yes' and r['assessment'] in ASSESS[:2]],key=lambda x:(x[0],x[1]))[:3]
 return dict(score=score,coverage=coverage,confidence=confidence,quality=quality,maturity=maturity,priorities=priorities,applicable=len(applicable),answered=sum(r['assessment'] in AVAL for r in applicable))

def calculate():
 c=st.session_state.carbon
 energy=float(c['gpu_count'])*float(c['training_hours'])*float(c['gpu_power'])/1000*float(c['pue']);emissions=energy*float(c['grid_intensity']);environment=max(0,100-emissions)
 results={k:score_metric(v) for k,v in st.session_state.records.items()}
 social=sum(results[k]['score'] for k in PILLARS['Social'] if results[k]['score'] is not None)/2
 governance=sum(results[k]['score'] for k in PILLARS['Governance'] if results[k]['score'] is not None)/3
 overall=(environment+social+governance)/3
 conf=sum(r['confidence'] or 0 for r in results.values())/5
 cov=sum(r['coverage'] or 0 for r in results.values())/5
 qual='High' if cov>=80 and conf>=80 else 'Low' if cov<50 or conf<50 else 'Medium'
 return results,dict(Environmental=environment,Social=social,Governance=governance,Overall=overall,energy=energy,emissions=emissions,coverage=cov,confidence=conf,quality=qual)

def fmt(v):return '—' if v is None else f'{v:.1f}'
def select_metric(name):st.session_state.page=name;st.rerun()

with st.sidebar:
 st.title('◈ AI ESG')
 st.caption('ASSESSMENT PLATFORM · MVP')
 role=st.selectbox('Demo role', ['Risk Engineer / Assessor','Vertical Risk Head','Organization Head','Administrator'],index=['Risk Engineer / Assessor','Vertical Risk Head','Organization Head','Administrator'].index(st.session_state.role))
 if role!=st.session_state.role:st.session_state.role=role;st.session_state.page='Overview';st.rerun()
 st.divider();st.caption('DEMONSTRATION CASE');st.write('**HR Chatbot**');st.caption('Business vertical: Human Resources')
 st.caption('One sample system only. No authentication or shared backend.')
 if role=='Risk Engineer / Assessor':
  st.divider()
  if st.button('Assessment Overview',use_container_width=True):st.session_state.page='Overview';st.rerun()
  for p,items in PILLARS.items():
   st.caption(p.upper())
   for name in items:
    if st.button(name,use_container_width=True,key='nav'+name):select_metric(name)
  if st.button('Review & Submit',use_container_width=True):st.session_state.page='Review';st.rerun()
 if st.button('Reset to workbook sample',use_container_width=True):
  st.session_state.records=json.loads(json.dumps(METRICS));st.session_state.carbon=DATA['carbon'].copy();st.session_state.status='In Progress';st.session_state.page='Overview';st.rerun()
 st.divider();st.caption('Data is stored only in this browser session. Demo roles do not enforce security.')

results,summary=calculate()
st.title('AI ESG Assessment Platform')
st.caption('HR Chatbot  /  Human Resources  /  '+role)

if role=='Risk Engineer / Assessor':
 page=st.session_state.page
 if page=='Overview':
  st.subheader('Assessment overview');st.info('Open a metric to review or update its controls. Scores are calculated from the entered responses.')
  c1,c2,c3,c4=st.columns(4)
  for col,k in zip([c1,c2,c3,c4],['Environmental','Social','Governance','Overall']):col.metric(k+' score',fmt(summary[k])+'/100')
  st.write('**Assessment quality:**',summary['quality'],'  ·  **Applicable-control coverage:**',fmt(summary['coverage'])+'%','  ·  **Evidence confidence:**',fmt(summary['confidence'])+'%')
  for pillar,items in PILLARS.items():
   st.markdown('### '+pillar)
   for name in items:
    a,b,c=st.columns([4,2,1])
    a.write('**'+name+'**')
    if name=='Carbon Intensity':b.caption('Score: '+fmt(summary['Environmental']))
    else:
     r=results[name];b.caption('Score: '+fmt(r['score'])+' · Quality: '+r['quality'])
    if c.button('Open →',key='open'+name):select_metric(name)
 elif page=='Carbon Intensity':
  st.subheader('Carbon Intensity');st.caption('Exact environmental equations extracted from the uploaded workbook.')
  c=st.session_state.carbon
  left,right=st.columns(2)
  with left:
   c['model_size']=st.number_input('Model size (B parameters)',min_value=0.0,value=float(c['model_size']),step=1.0)
   c['gpu_type']=st.text_input('GPU type',value=str(c['gpu_type']))
   c['gpu_count']=st.number_input('GPU count',min_value=0,value=int(c['gpu_count']))
   c['training_hours']=st.number_input('Training hours',min_value=0.0,value=float(c['training_hours']))
  with right:
   c['gpu_power']=st.number_input('GPU power (W)',min_value=0.0,value=float(c['gpu_power']))
   c['pue']=st.number_input('PUE',min_value=1.0,value=float(c['pue']),step=.1)
   c['grid_intensity']=st.number_input('Grid carbon intensity (kg CO₂e/kWh)',min_value=0.0,value=float(c['grid_intensity']),step=.1)
  _,s=calculate();a,b,d=st.columns(3);a.metric('Energy (kWh)',fmt(s['energy']));b.metric('Emissions (kg CO₂e)',fmt(s['emissions']));d.metric('Environmental score',fmt(s['Environmental']))
  st.caption('Workbook formula: energy = GPU count × hours × GPU power(kW) × PUE; emissions = energy × grid intensity; score = MAX(0, 100 − emissions). Model size and GPU type are descriptive inputs, not formula factors.')
 elif page in METRICS:
  st.subheader(page);r=results[page];a,b,c,d=st.columns(4);a.metric('Metric score',fmt(r['score']));b.metric('Coverage',fmt(r['coverage'])+'%');c.metric('Evidence confidence',fmt(r['confidence'])+'%');d.metric('Quality',r['quality'])
  st.caption(f"Maturity: {r['maturity']} · Applicable answered: {r['answered']}/{r['applicable']}")
  st.info('N/A = Yes excludes a control from the metric score. The coverage indicator mirrors the workbook: applicable controls ÷ all controls, not completion rate.')
  for i,item in enumerate(st.session_state.records[page]):
   with st.expander(f"{i+1:02d} · {item['question']}",expanded=i==0):
    st.caption('Weight: '+str(item['weight'])+'  ·  Recommendation: '+item['recommendation'])
    x,y,z=st.columns(3)
    item['assessment']=x.selectbox('Assessment', ['']+ASSESS,index=(['']+ASSESS).index(item['assessment']) if item['assessment'] in ['']+ASSESS else 0,key=page+str(i)+'a')
    item['evidence']=y.selectbox('Evidence status',['']+EVID,index=(['']+EVID).index(item['evidence']) if item['evidence'] in ['']+EVID else 0,key=page+str(i)+'e')
    item['na']=z.selectbox('N/A',['No','Yes'],index=1 if item['na']=='Yes' else 0,key=page+str(i)+'n')
    item['remarks']=st.text_area('Evidence reference / remarks',value=str(item['remarks']),key=page+str(i)+'r',height=75)
  st.markdown('#### Top improvement priorities')
  current=score_metric(st.session_state.records[page])
  if not current['priorities']:st.success('No actionable Not Implemented or Partially Implemented controls among applicable questions.')
  for _,i,item in current['priorities']:st.write(f"**{i+1}. {item['question']}** — {item['recommendation']}")
  if st.button('Refresh metric results'):st.rerun()
 elif page=='Review':
  st.subheader('Review assessment')
  st.dataframe([{'Metric':k,'Score':fmt(v['score']),'Coverage %':fmt(v['coverage']),'Evidence confidence %':fmt(v['confidence']),'Quality':v['quality']} for k,v in results.items()],hide_index=True,use_container_width=True)
  missing=sum(r['applicable']-r['answered'] for r in results.values());st.write('Unanswered applicable controls:',missing)
  if missing:st.warning('Complete all applicable control assessments before submitting.')
  if st.button('Submit to Vertical Risk Head',disabled=missing>0):st.session_state.status='Submitted';st.success('Submitted in this demo session (not persisted to a server).')

elif role=='Vertical Risk Head':
 st.subheader('Vertical ESG review · Human Resources');st.caption('One system is available in this MVP; vertical aggregation requires additional assessments.')
 c1,c2,c3,c4=st.columns(4)
 for col,k in zip([c1,c2,c3,c4],['Environmental','Social','Governance','Overall']):col.metric(k,fmt(summary[k]))
 st.write('**Assessment workflow:**',st.session_state.status,'  ·  **Assessment quality:**',summary['quality'])
 st.dataframe([{'Metric':k,'Score / 100':fmt(v['score']),'Assessment quality':v['quality'],'Coverage %':fmt(v['coverage']),'Evidence confidence %':fmt(v['confidence'])} for k,v in results.items()],hide_index=True,use_container_width=True)
 if st.session_state.status=='Submitted':
  a,b=st.columns(2)
  if a.button('Approve assessment'):st.session_state.status='Approved';st.rerun()
  if b.button('Return for correction'):st.session_state.status='Returned';st.rerun()
 else:st.info('Approval controls activate when the Risk Engineer submits the assessment.')

elif role=='Organization Head':
 st.subheader('Enterprise ESG dashboard');st.warning('Demonstration scope: one HR Chatbot in one business vertical. Figures below are not enterprise-wide aggregates.')
 a,b,c,d=st.columns(4)
 for col,k in zip([a,b,c,d],['Environmental','Social','Governance','Overall']):col.metric(k,fmt(summary[k]))
 st.bar_chart({'Environmental':summary['Environmental'],'Social':summary['Social'],'Governance':summary['Governance']})
 st.write('**Assessment quality:**',summary['quality'],'  ·  **Evidence confidence:**',fmt(summary['confidence'])+'%')
 lowest=min(results,key=lambda k:results[k]['score'] if results[k]['score'] is not None else 1e9)
 st.write('**Lowest-scoring metric:**',lowest,'('+fmt(results[lowest]['score'])+')')
 if results[lowest]['priorities']:st.write('**Top recommended action:**',results[lowest]['priorities'][0][2]['recommendation'])

else:
 st.subheader('Framework administration · Read-only MVP');st.info('Framework editing, user provisioning and framework versioning are reserved for the next release. This view exposes configuration without allowing changes that would invalidate workbook parity.')
 st.dataframe([{'Metric':k,'Controls':len(v),'Default total weight':sum(float(r['weight']) for r in v)} for k,v in METRICS.items()],hide_index=True,use_container_width=True)
 st.write('**Assessment mapping:**',AVAL,'  ·  **Evidence mapping:**',EVAL)
 st.write('**Quality thresholds:** High ≥80% coverage and confidence; Low if either <50%; otherwise Medium.')
 st.write('**Maturity:** Initial ≤20; Developing ≤40; Defined ≤60; Managed ≤80; Optimized >80.')

st.divider();st.caption('MVP demonstration • Source: uploaded AI ESG Assessment Calculator HR Chatbot v1 Candidate • Browser session only • No live AI or production authentication')
