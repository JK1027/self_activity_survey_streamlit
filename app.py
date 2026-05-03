import streamlit as st

def main():
    st.set_page_config(page_title="Self Activity Survey", layout="wide")
    st.title("📌 자가 활동 설문 시스템")
    st.write("설문을 시작하려면 아래 버튼을 클릭하세요.")
    
    if st.button("설문 시작"):
        st.info("설문 기능은 현재 준비 중입니다.")

if __name__ == "__main__":
    main()
