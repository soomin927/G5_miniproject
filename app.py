import random
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="🍣 Sushi Voca 3000", page_icon="🍣", layout="centered")
st.markdown("""<style>.stApp{background:#fff9f1}h1,h2,h3{color:#9e475b}.stButton>button{border-radius:14px}div[data-testid='stMetric']{background:#fff0df;border-radius:14px;padding:12px}</style>""",unsafe_allow_html=True)

@st.cache_data
def load_words():
    path=Path(__file__).parent/'Voca_3000.csv'
    df=pd.read_csv(path,encoding='utf-8-sig').fillna('')
    required=['Word','Level','Korean meaning (뜻)']
    if not all(c in df.columns for c in required):
        raise ValueError('CSV에 필요한 열이 없습니다: '+', '.join(required))
    df=df.rename(columns={'Word':'word','Level':'level','Korean meaning (뜻)':'meaning'})
    df['word']=df['word'].astype(str).str.strip()
    df['meaning']=df['meaning'].astype(str).str.strip()
    return df[(df.word!='') & (df.meaning!='')].reset_index(drop=True)

try:
    df=load_words()
except Exception as e:
    st.error(f'어휘 CSV를 읽을 수 없습니다: {e}')
    st.stop()

for k,default in {'studied':set(),'correct':0,'collected':set(),'wrong':set(),'current':None,'options':[],'attempts':0,'hint':False,'done':False,'message':'','question_type':'뜻 고르기','question_id':0}.items():
    if k not in st.session_state: st.session_state[k]=default
s=st.session_state

def choose(pool,kind):
    if pool.empty:
        s.current=None;return
    row=pool.sample(1).iloc[0]
    s.current={'word':str(row.word),'meaning':str(row.meaning),'level':str(row.level)}
    s.question_type=kind
    s.attempts=0;s.hint=False;s.done=False;s.message='';s.question_id+=1
    alternatives=pool.loc[pool.word!=row.word,'meaning'].drop_duplicates().tolist()
    if len(alternatives)<3:
        alternatives=df.loc[df.word!=row.word,'meaning'].drop_duplicates().tolist()
    s.options=random.sample(alternatives,min(3,len(alternatives)))+[str(row.meaning)]
    random.shuffle(s.options)

def check(answer):
    if s.current is None or s.done:return
    w=s.current['word']; correct=s.current['meaning'] if s.question_type=='뜻 고르기' else w
    ok=answer.strip().casefold()==correct.strip().casefold()
    s.studied.add(w)
    if ok:
        s.correct+=1;s.collected.add(w);s.wrong.discard(w);s.done=True
        s.message='✅ 정답! 🍣 초밥을 획득했어요!'
    else:
        s.wrong.add(w);s.attempts+=1
        if s.attempts==1:
            s.hint=True;s.message='❌ 아쉬워요! 힌트를 보고 한 번 더 도전하세요.'
        else:
            s.done=True;s.message=f'정답: {correct} — 다음에 다시 복습해요.'

st.title('🍣 Sushi Voca 3000')
st.caption('중학교 1학년을 위한 어휘 학습 · 전체 CSV 데이터 사용 · 로그인 불필요')
a,b,c=st.columns(3)
a.metric('전체 단어',f'{len(df):,}')
b.metric('학습한 단어',len(s.studied))
c.metric('수집한 초밥',len(s.collected))
st.progress(min(len(s.studied)/len(df),1.0))
st.caption('학습 기록은 현재 브라우저 세션에 저장되며 새 세션에서는 초기화될 수 있어요.')

st.subheader('🎯 학습 설정')
levels={'전체':'all','기초 (800)':'Elementary','중급 (1,200)':'MidHigh','확장 (1,000)':'Extended'}
level_label=st.selectbox('단어 수준',list(levels))
kind=st.radio('문제 유형',['뜻 고르기','영어 단어 쓰기'],horizontal=True)
pool=df if levels[level_label]=='all' else df[df.level==levels[level_label]]
mode=st.radio('학습 방식',['랜덤 학습','오답 복습'],horizontal=True)
if mode=='오답 복습':pool=pool[pool.word.isin(s.wrong)]
if st.button('🎲 새 문제 시작',type='primary',use_container_width=True):choose(pool,kind)
if mode=='오답 복습' and pool.empty:st.info('이 수준에서 복습할 오답이 없어요. 먼저 랜덤 학습을 해 보세요!')

st.subheader('📝 어휘 퀴즈')
if s.current:
    q=s.current
    st.caption(f"난이도: {q['level']} · 문제 {s.question_id}")
    if s.question_type=='뜻 고르기':
        st.markdown(f"### **{q['word']}** 의 뜻은?")
        if s.hint and not s.done:st.info(f"💡 힌트: 정답의 첫 글자는 **{q['meaning'][:1]}** 입니다.")
        for i,opt in enumerate(s.options,1):
            if st.button(f'{i}. {opt}',key=f'opt_{s.question_id}_{i}',disabled=s.done,use_container_width=True):
                check(opt);st.rerun()
    else:
        st.markdown(f"### **{q['meaning']}** 에 해당하는 영어 단어는?")
        if s.hint and not s.done:st.info(f"💡 힌트: **{q['word'][:1]}** 로 시작하고, 총 {len(q['word'])}글자예요.")
        with st.form(key=f'write_{s.question_id}_{s.attempts}'):
            answer=st.text_input('영어 단어 입력',disabled=s.done)
            submitted=st.form_submit_button('정답 확인',disabled=s.done)
            if submitted:
                if answer.strip():check(answer);st.rerun()
                else:st.warning('단어를 입력해 주세요.')
if s.get("message"):
    st.success(s["message"])

if s.get("done", False) and q["word"] in s.get("collected", []):
    st.write("🍣 초밥을 수집했어요!")    if s.done and st.button('➡️ 다음 문제',use_container_width=True):choose(pool,kind);st.rerun()
else:st.info('위에서 학습 방식을 선택한 후 「새 문제 시작」을 눌러 주세요.')

st.subheader('🏆 나의 초밥 컬렉션')
st.write('🍣 ' * min(len(s.collected),20) if s.collected else '아직 수집한 초밥이 없어요. 정답을 맞혀 보세요!')
st.caption(f'정답 횟수: {s.correct}회 · 복습할 단어: {len(s.wrong)}개')
with st.expander('📒 오답노트 보기'):
    wrong_df=df[df.word.isin(s.wrong)][['word','meaning','level']]
    if wrong_df.empty:st.write('오답이 없어요!')
    else:st.dataframe(wrong_df.rename(columns={'word':'단어','meaning':'뜻','level':'수준'}),hide_index=True,use_container_width=True)
with st.expander('📚 CSV 데이터 정보'):
    st.write('`Voca_3000.csv`의 영어 단어, 한국어 뜻, 수준 정보를 직접 읽어 퀴즈를 생성합니다.')
    st.dataframe(df[['word','meaning','level']].head(10),hide_index=True,use_container_width=True)
    st.markdown('[원본 CSV 파일 (GitHub)](https://github.com/soomin927/Streamlit_app/blob/main/Voca_3000.csv)')
