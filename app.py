import streamlit as st
from google_sheets import GoogleSheetsManager
import time

# 페이지 설정
st.set_page_config(
    page_title="자율활동 설문 앱",
    page_icon="📝",
    layout="centered" # 아이패드 등 태블릿 최적화
)

# 커스텀 CSS (파스텔톤 UI 및 둥근 버튼 15px)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }
    
    /* 배경색 및 전체 디자인 */
    .stApp {
        background-color: #FDFCF0; /* 연한 파스텔톤 노란색/크림색 */
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 15px !important;
        background-color: #FFD1DC !important; /* 파스텔 핑크 */
        color: #4A4A4A !important;
        border: none !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #FFB7C5 !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    /* 입력창 스타일 */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 15px !important;
        border: 1px solid #E0E0E0 !important;
    }
    
    /* 헤더 스타일 */
    .main-header {
        color: #5D5D5D;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .topic-container {
        background-color: #E3F2FD; /* 파스텔 블루 */
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 25px;
        border-left: 10px solid #90CAF9;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    # 구글 시트 매니저 인스턴스 생성
    gs = GoogleSheetsManager()

    st.markdown("<h1 class='main-header'>📝 자율활동 설문 제출</h1>", unsafe_allow_html=True)

    # 연결 상태 확인
    if not gs.is_connected():
        st.error("구글 시트가 연결되지 않았습니다. .streamlit/secrets.toml 설정을 확인해주세요.")
        return

    # 구글 시트의 Settings 탭에서 '오늘의 주제'를 실시간으로 가져옵니다.
    today_topic = gs.get_today_topic()
    
    # 주제 표시 레이아웃
    st.markdown(f"""
        <div class='topic-container'>
            <h4 style='margin:0; color:#1565C0;'>오늘의 주제</h4>
            <p style='margin:10px 0 0 0; font-size:1.2rem; font-weight:bold;'>{today_topic}</p>
        </div>
    """, unsafe_allow_html=True)

    # 학생 정보 및 소감문 입력 폼
    with st.form("survey_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            student_id = st.text_input("학번 (예: 10101)", placeholder="5자리 학번 입력")
        with col2:
            student_name = st.text_input("이름", placeholder="이름 입력")
        
        content = st.text_area("소감문 (100자 이상 입력)", height=250, placeholder="오늘의 주제에 대한 자신의 생각을 자유롭게 적어주세요.")
        
        submit_btn = st.form_submit_button("제출하기")

    # 제출 버튼 클릭 시 로직
    if submit_btn:
        # 1. 필수 입력 항목 확인
        if not student_id or not student_name or not content:
            st.warning("모든 항목을 입력해주세요.")
        # 2. 글자 수 제한 확인 (100자 미만 제출 제한)
        elif len(content) < 100:
            st.error(f"소감문이 너무 짧습니다. (현재 {len(content)}자 / 최소 100자 이상 작성해야 합니다.)")
        else:
            # 3. 중복 제출 여부 확인 (학번+이름+주제 기준)
            existing_row = gs.check_existing_response(student_id, student_name, today_topic)
            
            if existing_row:
                # 이미 제출된 기록이 있는 경우: 다이얼로그(팝업)를 통해 덮어쓰기 여부를 묻습니다.
                st.session_state.pending_data = {
                    "student_id": student_id,
                    "name": student_name,
                    "topic": today_topic,
                    "content": content,
                    "row": existing_row
                }
                show_overwrite_dialog()
            else:
                # 신규 제출인 경우: 바로 시트에 저장합니다.
                if gs.submit_response(student_id, student_name, today_topic, content):
                    st.success("성공적으로 제출되었습니다!")
                    st.balloons()
                    time.sleep(2)

@st.dialog("이미 제출된 기록이 있습니다.")
def show_overwrite_dialog():
    """중복 제출 시 나타나는 확인 팝업창입니다."""
    st.write(f"**{st.session_state.pending_data['name']}** 학생의 동일한 주제에 대한 기록이 이미 존재합니다.")
    st.write("기존 내용을 새로운 소감문으로 덮어쓸까요?")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("예 (업데이트)", use_container_width=True):
            data = st.session_state.pending_data
            # '예'를 선택하면 기존 행 번호(row)를 사용하여 데이터를 업데이트합니다.
            if gs_instance().submit_response(data['student_id'], data['name'], data['topic'], data['content'], data['row']):
                st.success("기존 기록이 업데이트되었습니다!")
                time.sleep(1)
                del st.session_state.pending_data
                st.rerun() # 화면을 새로고침하여 반영
    with c2:
        if st.button("아니오 (취소)", use_container_width=True):
            # '아니오'를 선택하면 작업을 취소하고 팝업을 닫습니다.
            del st.session_state.pending_data
            st.rerun()

# 구글 시트 연결 인스턴스를 캐싱하여 앱의 성능을 최적화합니다.
@st.cache_resource
def gs_instance():
    return GoogleSheetsManager()

if __name__ == "__main__":
    main()
