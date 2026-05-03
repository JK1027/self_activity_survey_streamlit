import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime
import json

class GoogleSheetsManager:
    """
    구글 스프레드시트 매니저 (JSON 통째로 읽기 버전)
    TOML의 문자열 처리 오류를 방지하기 위해 JSON 데이터를 직접 파싱합니다.
    """
    def __init__(self):
        try:
            # 1. Secrets에서 GCP_JSON 항목 확인
            if "GCP_JSON" in st.secrets:
                # JSON 문자열을 딕셔너리로 변환
                info = json.loads(st.secrets["GCP_JSON"])
            elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
                # 기존 방식 호환용
                info = dict(st.secrets["connections"]["gsheets"])
                if "private_key" in info:
                    pk = info["private_key"].replace("\\n", "\n").strip()
                    info["private_key"] = pk
            else:
                st.error("Secrets 설정에 [GCP_JSON] 항목이 없습니다.")
                self.connected = False
                return

            # 2. 인증 및 연결
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            self.client = gspread.authorize(creds)
            
            # 3. 시트 열기
            self.spreadsheet_id = st.secrets["spreadsheet_id"]
            self.sheet = self.client.open_by_key(self.spreadsheet_id)
            self.connected = True
            st.caption("✓ 구글 시트 연결 성공 (JSON-Direct)")
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
