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

def main():

    # 구글 시트 매니저 인스턴스 생성
    gs = GoogleSheetsManager()
    
    st.sidebar.title("⚙️ 관리 메뉴")
    menu = st.sidebar.radio("이동할 메뉴", ["오늘의 주제 설정", "전체 응답 현황"])

    # 메뉴 1: 오늘의 주제 설정
    if menu == "오늘의 주제 설정":
        st.title("📍 오늘의 주제 설정")
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
                    # 캐시를 삭제하여 업데이트된 주제가 즉시 반영되도록 합니다.
                    st.cache_resource.clear() 

    # 메뉴 2: 학생 응답 현황 확인 및 다운로드
    elif menu == "전체 응답 현황":
        st.title("📊 학생 응답 현황")
        # 시트에서 모든 응답 데이터를 불러옵니다.
        df = gs.get_all_responses()
        
        if not df.empty:
            st.write(f"총 **{len(df)}**건의 응답이 있습니다.")
            # 데이터프레임으로 화면에 표시
            st.dataframe(df, use_container_width=True)
            
            # 엑셀 보고서용 CSV 다운로드 (한글 깨짐 방지를 위해 utf-8-sig 인코딩 적용)
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
