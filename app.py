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
        padding: 12px 28px !important; /* 높이 확보를 위해 패딩 증가 */
        min-height: 44px !important;   /* 아이패드 터치 최적화 (룰 준수) */
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

def admin_topic_setting(gs):
    st.markdown("<h2 class='main-header'>📍 오늘의 주제 설정</h2>", unsafe_allow_html=True)
    current_topic = gs.get_today_topic()
    
    with st.container():
        st.info(f"현재 설정된 주제: **{current_topic}**")
        new_topic = st.text_area("새로운 주제 입력 (학생용 화면에 즉시 반영됩니다)", value=current_topic, height=100)
        
        if st.button("설정 저장"):
            if not new_topic:
                st.warning("주제를 입력해주세요.")
            elif gs.update_today_topic(new_topic):
                st.success("✅ 주제가 성공적으로 변경되었습니다!")
                st.balloons()
                st.cache_resource.clear() 
                st.rerun()

def admin_response_status(gs):
    st.markdown("<h2 class='main-header'>📊 학생 응답 현황</h2>", unsafe_allow_html=True)
    df = gs.get_all_responses()
    
    if not df.empty:
        st.write(f"총 **{len(df)}**건의 응답이 있습니다.")
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 응답 데이터(CSV) 다운로드",
            data=csv,
            file_name="survey_responses.csv",
            mime="text/csv",
        )
    else:
        st.info("아직 제출된 응답이 없습니다.")

def main():
    # 구글 시트 매니저 인스턴스 생성
    gs = gs_instance()

    # 사이드바 메뉴 (관리자 기능 통합)
    st.sidebar.title("📱 메뉴 선택")
    
    # 세션 상태에 로그인 여부 저장
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    # 메뉴 옵션 설정
    menu_options = ["학생용 설문 제출"]
    if st.session_state.admin_authenticated:
        menu_options += ["관리자 - 주제 설정", "관리자 - 응답 현황"]
    
    app_mode = st.sidebar.radio("원하는 기능을 선택하세요", menu_options)

    # 관리자 로그인 섹션
    if not st.session_state.admin_authenticated:
        with st.sidebar.expander("🔐 관리자 로그인"):
            password = st.text_input("비밀번호를 입력하세요", type="password")
            if st.button("로그인"):
                if password == "6661":
                    st.session_state.admin_authenticated = True
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("비밀번호가 틀렸습니다.")
    else:
        if st.sidebar.button("로그아웃"):
            st.session_state.admin_authenticated = False
            st.rerun()

    if app_mode == "학생용 설문 제출":
        st.markdown("<h1 class='main-header'>📝 자율활동 설문 제출</h1>", unsafe_allow_html=True)

        # 연결 상태 확인
        if not gs.is_connected():
            st.error("구글 시트가 연결되지 않았습니다. Secrets 설정을 확인해주세요.")
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
                student_id = st.text_input("학번 (예: 1102)", placeholder="4자리 학번 입력")
            with col2:
                student_name = st.text_input("이름", placeholder="이름 입력")
            
            content = st.text_area("소감문 (100자 이상 입력)", height=250, placeholder="오늘의 주제에 대한 자신의 생각을 자유롭게 적어주세요.")
            
            submit_btn = st.form_submit_button("제출하기")

        # 제출 버튼 클릭 시 로직
        if submit_btn:
            if not student_id or not student_name or not content:
                st.warning("모든 항목을 입력해주세요.")
            elif not (len(student_id) == 4 and student_id.isdigit()):
                st.error("학번은 4자리 숫자로 입력해 주세요. (예: 1학년 1반 2번 → 1102)")
            elif len(content) < 100:
                st.error(f"소감문이 너무 짧습니다. (현재 {len(content)}자 / 최소 100자 이상 작성해야 합니다.)")
            else:
                existing_row = gs.check_existing_response(student_id, student_name, today_topic)
                if existing_row:
                    st.session_state.pending_data = {
                        "student_id": student_id,
                        "name": student_name,
                        "topic": today_topic,
                        "content": content,
                        "row": existing_row
                    }
                    show_overwrite_dialog()
                else:
                    if gs.submit_response(student_id, student_name, today_topic, content):
                        st.success("성공적으로 제출되었습니다!")
                        st.balloons()
                        time.sleep(2)

    elif app_mode == "관리자 - 주제 설정":
        admin_topic_setting(gs)
    elif app_mode == "관리자 - 응답 현황":
        admin_response_status(gs)

@st.dialog("이미 제출된 기록이 있습니다.")
def show_overwrite_dialog():
    """중복 제출 시 나타나는 확인 팝업창입니다."""
    st.write(f"**{st.session_state.pending_data['name']}** 학생의 동일한 주제에 대한 기록이 이미 존재합니다.")
    st.write("기존 내용을 새로운 소감문으로 덮어쓸까요?")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("예 (업데이트)", use_container_width=True):
            data = st.session_state.pending_data
            if gs_instance().submit_response(data['student_id'], data['name'], data['topic'], data['content'], data['row']):
                st.success("기존 기록이 업데이트되었습니다!")
                time.sleep(1)
                del st.session_state.pending_data
                st.rerun()
    with c2:
        if st.button("아니오 (취소)", use_container_width=True):
            del st.session_state.pending_data
            st.rerun()

# 구글 시트 연결 인스턴스를 캐싱하여 앱의 성능을 최적화합니다.
@st.cache_resource
def gs_instance():
    return GoogleSheetsManager()

if __name__ == "__main__":
    main()
