import streamlit as st
from google_sheets import GoogleSheetsManager
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="관리자 페이지 - 자율활동 설문 앱",
    page_icon="⚙️",
    layout="wide"
)

# CSS 적용
st.markdown("""
    <style>
    .stButton > button {
        border-radius: 15px !important;
        background-color: #B2DFDB !important; /* 파스텔 민트 */
        color: #004D40 !important;
        font-weight: bold !important;
    }
    .stApp {
        background-color: #F1F8E9; /* 아주 연한 초록색 */
    }
    </style>
    """, unsafe_allow_html=True)

def check_password():
    """관리자 비밀번호를 확인합니다."""
    def password_entered():
        # secrets.toml에 admin_password가 정의되어 있지 않으면 기본값 'admin1234' 사용
        correct_password = st.secrets.get("admin_password", "admin1234")
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 세션에서 비밀번호 제거
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 비밀번호 입력창 표시
        st.title("🔒 관리자 로그인")
        st.text_input(
            "관리자 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password"
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("😕 비밀번호가 일치하지 않습니다.")
        return False
    elif not st.session_state["password_correct"]:
        # 비밀번호가 틀린 경우 다시 입력창 표시
        st.text_input(
            "관리자 비밀번호를 입력하세요", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 비밀번호가 일치하지 않습니다.")
        return False
    else:
        # 비밀번호가 맞는 경우
        return True

def main():
    if not check_password():
        return

    gs = GoogleSheetsManager()
    
    st.sidebar.title("⚙️ 관리 메뉴")
    menu = st.sidebar.radio("이동할 메뉴", ["오늘의 주제 설정", "전체 응답 현황"])

    if menu == "오늘의 주제 설정":
        st.title("📍 오늘의 주제 설정")
        current_topic = gs.get_today_topic()
        
        with st.container():
            st.info(f"현재 설정된 주제: **{current_topic}**")
            new_topic = st.text_area("새로운 주제 입력", value=current_topic, height=100)
            
            if st.button("설정 저장"):
                if not new_topic:
                    st.warning("주제를 입력해주세요.")
                elif gs.update_today_topic(new_topic):
                    st.success("✅ 주제가 성공적으로 변경되었습니다!")
                    st.balloons()
                    st.cache_resource.clear() # 캐시 초기화하여 학생 화면에도 즉시 반영되게 함

    elif menu == "전체 응답 현황":
        st.title("📊 학생 응답 현황")
        df = gs.get_all_responses()
        
        if not df.empty:
            st.write(f"총 **{len(df)}**건의 응답이 있습니다.")
            st.dataframe(df, use_container_width=True)
            
            # CSV 다운로드 (Excel 호환을 위해 utf-8-sig 사용)
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 응답 데이터(CSV) 다운로드",
                data=csv,
                file_name="survey_responses.csv",
                mime="text/csv",
            )
        else:
            st.info("아직 제출된 응답이 없습니다.")

if __name__ == "__main__":
    main()
