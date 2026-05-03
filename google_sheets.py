import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime

class GoogleSheetsManager:
    """
    구글 스프레드시트 매니저 (최종 안정화 버전)
    사용자가 입력한 키를 스스로 분석하여 올바른 PEM 형식으로 재조립합니다.
    """
    def __init__(self):
        try:
            # 1. 인증 정보 가져오기
            if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
                info = dict(st.secrets["connections"]["gsheets"])
            elif "gcp_service_account" in st.secrets:
                info = dict(st.secrets["gcp_service_account"])
            else:
                st.error("Secrets 설정에 [connections.gsheets] 섹션이 없습니다.")
                self.connected = False
                return

            # 2. 프라이빗 키 강제 재조립 (가장 강력한 방식)
            if "private_key" in info:
                raw_key = info["private_key"]
                # 헤더/푸터 및 모든 공백, 줄바꿈 제거하여 '알맹이'만 추출
                core_key = raw_key.replace("-----BEGIN PRIVATE KEY-----", "")
                core_key = core_key.replace("-----END PRIVATE KEY-----", "")
                core_key = core_key.replace("\\n", "").replace("\n", "").replace(" ", "").strip()
                
                # 표준 PEM 형식으로 강제 재조립
                clean_key = f"-----BEGIN PRIVATE KEY-----\n{core_key}\n-----END PRIVATE KEY-----"
                info["private_key"] = clean_key

            # 3. 인증 및 연결
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            self.client = gspread.authorize(creds)
            
            # 4. 시트 열기
            self.spreadsheet_id = st.secrets["spreadsheet_id"]
            self.sheet = self.client.open_by_key(self.spreadsheet_id)
            self.connected = True
            st.caption("✓ 구글 시트 연결 성공")
        except Exception as e:
            st.error(f"연결 최종 실패: {e}")
            self.connected = False

    def is_connected(self): return self.connected

    def get_today_topic(self):
        if not self.connected: return "연결 오류"
        try:
            ws = self.sheet.worksheet("Settings")
            df = pd.DataFrame(ws.get_all_records())
            return df[df["Key"] == "today_topic"]["Value"].values[0]
        except Exception: return "설정된 주제가 없습니다."

    def update_today_topic(self, topic):
        if not self.connected: return False
        try:
            ws = self.sheet.worksheet("Settings")
            df = pd.DataFrame(ws.get_all_records())
            idx = df[df["Key"] == "today_topic"].index[0]
            ws.update_cell(idx + 2, 2, topic)
            return True
        except Exception as e:
            st.error(f"주제 업데이트 실패: {e}"); return False

    def check_existing_response(self, student_id, name, topic):
        if not self.connected: return None
        try:
            ws = self.sheet.worksheet("Responses")
            df = pd.DataFrame(ws.get_all_records())
            match = df[(df['학번'].astype(str) == str(student_id)) & (df['이름'] == name) & (df['주제'] == topic)]
            return int(match.index[0] + 2) if not match.empty else None
        except Exception: return None

    def submit_response(self, student_id, name, topic, content, row_to_update=None):
        if not self.connected: return False
        try:
            ws = self.sheet.worksheet("Responses")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [str(student_id), name, topic, content, now]
            if row_to_update: ws.update(f"A{row_to_update}:E{row_to_update}", [new_row])
            else: ws.append_row(new_row)
            return True
        except Exception as e: st.error(f"제출 실패: {e}"); return False

    def get_all_responses(self):
        if not self.connected: return pd.DataFrame()
        try:
            ws = self.sheet.worksheet("Responses")
            return pd.DataFrame(ws.get_all_records())
        except Exception: return pd.DataFrame()
