import streamlit as st
import pandas as pd
from google_sheets import GoogleSheetsManager
import time
import base64
import json

st.set_page_config(page_title="자율활동 설문 시스템", page_icon="📝", layout="centered")

st.markdown("""
<style>
    .main-header { text-align: center; color: #1E88E5; margin-bottom: 30px; }
    .topic-container { background-color: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 5px solid #1E88E5; margin-bottom: 25px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #1E88E5; color: white; }
</style>
""", unsafe_allow_html=True)

def admin_topic_setting(gs):
    st.markdown("<h1 class='main-header'>📍 오늘의 주제 설정</h1>", unsafe_allow_html=True)
    current_topic = gs.get_today_topic()
    st.info(f"현재 설정된 주제: **{current_topic}**")
    new_topic = st.text_area("주제 내용", value=current_topic if current_topic != '설정된 주제가 없습니다.' else '', height=100)
    if st.button("설정 저장"):
        if new_topic and gs.update_today_topic(new_topic):
            st.success("주제가 업데이트되었습니다!")
            time.sleep(1)
            st.rerun()

def admin_response_status(gs):
    st.markdown("<h1 class='main-header'>📊 학생 응답 현황</h1>", unsafe_allow_html=True)
    df = gs.get_all_responses()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.download_button(label="📥 CSV 다운로드", data=df.to_csv(index=False).encode('utf-8-sig'), file_name="survey.csv", mime="text/csv")

def main():
    gs = gs_instance()
    if not st.session_state.get("magic_key_fixed", False):
        import base64, json
        MAGIC_INFO_B64 = "eyJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsICJwcm9qZWN0X2lkIjogInNtYXJ0LWF0dGVuZGFuY2UtMjAyNCIsICJwcml2YXRlX2tleV9pZCI6ICJlMmRmZWFkNTYyMWUxZjBlOTZkYzg5ZmI0OTdiMjIyYTFlOTAxMWQ4IiwgInByaXZhdGVfa2V5IjogIi0tLS0tQkVHSU4gUFJJVkFURSBLRVktLS0tLVxuTUlJRXZ3SUJBREFOQmdrcWhoa2lHOXcwQkFRRUZBQVNDQktrd2dnU2xBZ0VBQW9JQkFRREhwbnMwelp3cDFxUXJcbi9FWnlWVlZXS2NzN0o0VlwvVXBaM08zMDJGY1wvQ2MwTUxwT01GMFwvTGN6UGJxd1JUTzdkSUJQblpQWks2enpGNFxuV21ZOVFjYm9qTGlERTJVeGIsVmZra20xdnZueVwvWVE3dGVVVmg0cFJwVFdoR2dEYTZ3T09HQ3JSdzlLSks0N3JmXG45MTRWSzdrNW1ZcThMcElDdjVFNUg2MHVoZ0dIOHplM2JMQ0xWWURJS3FoZlVQRjd2OFVOZkg3UGxGZ29aTWpxXG50a1JhazFUZmFLUzdZY00rNm5IeU9QZXpwMWJ1REZPemp1SElaTllWcmVmVnZ1NXBoMEZrVHhnSStWd3VzVmRMXG51ZkpxXCtrb3lcL0Mxais4QSArSG9zV3VlSnMwYVV0TjZTWm8rRk9PbEZ5RTNpMmNqZnhXTUtsV2UrZytad0RMWmlcL0tcblhHTFl1MG5oQWdNQkFBRUNnZ0VBVXZBRTlLMkpkeFAwaFFPclE5UVFmXC9EaEdkZDk0S0tsUldsWTcKS2pHcmFoTFxucHdqZVFHOGF0ZUM0cFVPSSsyNnVOOXZoVXU2eU9xcUIyWVpzUEh4THZpVmZMUXhzc3MrYWNaS1RyeE9ZWmsrR1xueFA0QTVhWHprejhWMTF2QjRKanpxZTljd0NQUkc1NDQ3bnRiZVIzOXgwRFNrbFFpVWPQMzl5OENpWFlmd3JKNVxua25idHJjcWY3aG1aXC9VdUJ6eWhmZEEySURZTnB2M1djUGlPMW0xV2lhKzRkbFZFUmdGdTlmRDNTRGhuZGdaYVNcbjh5YTh3d1U5V0tsc3F4M2hCVVZ0dDgxMXBcLytYeDJtdVlmZmt3MFdCb2wrMFwvVDZvelpOUytVR3dYREFHbGxGTVxuVzFrSkxhODRxVDM1MnN2a1ArQ2l0T2pNWlp4bnU0VFRlZnkwV0t5bTlRS0JnUUR2SStUTmN2d2FLS09DUytGVW9cbnl5NjN2YklYZHFRbjhaWTkxUDU3UWtwVVV1TGxGRk1cL1pkN3RZQnRwakJMdzlXemNiSXI0TTNjbG9JT25mdDdDS1xuM3BrUGVYLkVNaEF5WnkwaW1nai9haGxnWmVVY3BUOWwwOHBNVEcvaUpDYk9BQk0vbEwwWEcvamt5K0ErVjJ2ZGFcbnBSdG4v dSsrOFpEWVJCWFpMS2t5S2k2cmhNd0tCZ1FETVU4dm94T3FjZkFBYnFWRXFGNzJwdUJMMWNZUXRDM2o5XG5XQTZVQVVZcHFMMGhzczlaTlV1TitWdmQ4MEx1OFNcL0hxUVJcL0NZbGRLbTVpSER1UGUwVU9tVkRzRFpqVm5LbG8KdXoxSWpEby9OTiswL1g4dDkzQkppcm9sZHdmUHNwZWtiK2ZGcjNraWVSakVSNDZZVTIrMHM3YThpeHNMYXZKZFxuODZPSllJZFFtd0tCZ1FEZjRYcHF5K3lKK1dZdkJPY3JrTmRxaXZVMy9POGw5UnVVa2V1SEpLamtXaDlNQzJvTFxuQjBHRTBnMFc1ZEVhSzNcL1l0YW1ZUm0vd2xIN2hUak5RTkp2aDFtaXN0bVk2eG8vNUFQdm1wdTY1a2RtRFR2KzBcblF1QUFkRVY3Z1FIZVJNRDFta20zd2toOWQyQm9TOVIySTJ0Znh0NEtZNmxSZDNkQW9iSEdnd1hCY3dLQmdRQ3FcblZha0ZjVE5NSkt0S1pBb1wvbHU4THoySXVydVZMVCtjYVwvQStiSHJ6SStkeEJmWGtSbXpaVE11OTh4ZENrdFBmcFxuOEdMSkxNQVFwTkRFaFZpNXNqXC9OZmM1U0dydXdTQnVLTFoxWEgxOW5WY0t3ZFN0U3ZKWWxHTHM1aEZORXVGTm1cblI4dmxwdlRLNGp6ZFUvSHgxb3luRGJKbTEyaENTbk9tRXZmZ0RGS0J4UUtCZ1FDNzViRW9pU0pQRkVtblMxVWtcbnloRzJ2YXpVZStOYkVPDnY2TXAxU2RCSXRRZktQSlA3ZTVNWUhHbUZ5NEpKWTkwa05sTjFJcU1LSkRnQ1E4ck1cbiRod05pY1QyTkpTZ1dOTVZ4NCtwVTFLdHQxSzNyRCsyUXJSbkpQejlBZ3QxbGZxVUZMUmNWbHlMZk04QjNXSThcbiBRc3FhUkFMWVhKY2tZclVSeXdBK2RtdWdnPT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1cbiIsICJjbGllbnRfZW1haWwiOiAic21hcnQtYXR0ZW5kYW5jZS1zZXJ2aWNlQHNtYXJ0LWF0dGVuZGFuY2UtMjAyNC5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0aCIsICJ0b2tlbl91cmkiOiAiaHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4iLCAiYXV0aF9wcm92aWRlcl94NTA5X2NlcnRfdXJsIjogImh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tI29hdXRoMi92MS9jZXJ0cyIsICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L3NtYXJ0LWF0dGVuZGFuY2Utc2VydmljZSU0MHNtYXJ0LWF0dGVuZGFuY2UtMjAyNC5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsICJ1bml2ZXJzYWxfZG9tYWluIjogImdvb2dsZWFwaXMuY29tIn0=\"
        try:
            info = json.loads(base64.b64decode(MAGIC_INFO_B64).decode('utf-8'))
            if gs.connect(magic_key=info['private_key']):
                st.session_state.magic_key_fixed = True
        except: pass

    st.sidebar.title("📱 메뉴 선택")
    app_mode = st.sidebar.radio("기능 선택", ["학생용 설문 제출", "관리자 - 주제 설정", "관리자 - 응답 현황"])

    if app_mode == "학생용 설문 제출":
        st.markdown("<h1 class='main-header'>📝 자율활동 설문 제출</h1>", unsafe_allow_html=True)
        if not gs.is_connected():
            st.error("연결 오류")
            return
        today_topic = gs.get_today_topic()
        st.markdown(f"<div class='topic-container'>오늘의 주제: <b>{today_topic}</b></div>", unsafe_allow_html=True)
        with st.form("survey_form"):
            sid = st.text_input("학번 (예: 1102)")
            name = st.text_input("이름")
            txt = st.text_area("소감문 (100자 이상)", height=200)
            if st.form_submit_button("제출하기"):
                if sid and name and len(txt) >= 100:
                    if gs.submit_response(sid, name, today_topic, txt):
                        st.success("제출 완료!")
                        st.balloons()
                else: st.warning("입력 확인 (학번/이름/소감문 100자)")
    elif app_mode == "관리자 - 주제 설정": admin_topic_setting(gs)
    elif app_mode == "관리자 - 응답 현황": admin_response_status(gs)

@st.dialog("중복 제출 확인")
def show_overwrite_dialog(): pass

@st.cache_resource
def gs_instance(): return GoogleSheetsManager()

if __name__ == \"__main__\": main()
