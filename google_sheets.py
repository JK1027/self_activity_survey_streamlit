import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime

class GoogleSheetsManager:
    """
    구글 스프레드시트와의 연동을 담당하는 클래스입니다.
    데이터 읽기, 쓰기, 업데이트 및 중복 체크 로직을 포함합니다.
    """
    def __init__(self):
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        try:
            # .streamlit/secrets.toml에서 구글 서비스 계정 정보를 가져옵니다.
            if "gcp_service_account" in st.secrets:
                self.creds = Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"],
                    scopes=self.scope
                )
                self.client = gspread.authorize(self.creds)
                self.spreadsheet_id = st.secrets["spreadsheet_id"]
                self.sheet = self.client.open_by_key(self.spreadsheet_id)
            else:
                self.sheet = None
        except Exception as e:
            st.error(f"구글 시트 연결 실패: {e}")
            self.sheet = None

    def is_connected(self):
        return self.sheet is not None

    def get_today_topic(self):
        """Settings 탭에서 오늘의 주제를 가져옵니다."""
        if not self.sheet: return "연결 오류"
        try:
            settings_sheet = self.sheet.worksheet("Settings")
            data = settings_sheet.get_all_records()
            for row in data:
                if row.get("Key") == "today_topic":
                    return row.get("Value")
            return "설정된 주제가 없습니다."
        except Exception:
            return "주제 불러오기 실패"

    def update_today_topic(self, topic):
        """Settings 탭의 오늘의 주제를 업데이트합니다."""
        if not self.sheet: return False
        try:
            settings_sheet = self.sheet.worksheet("Settings")
            cell = settings_sheet.find("today_topic")
            settings_sheet.update_cell(cell.row, cell.col + 1, topic)
            return True
        except Exception as e:
            st.error(f"주제 업데이트 실패: {e}")
            return False

    def check_existing_response(self, student_id, name, topic):
        """기존에 동일한 [학번+이름+주제]로 제출된 기록이 있는지 확인합니다."""
        if not self.sheet: return None
        try:
            responses_sheet = self.sheet.worksheet("Responses")
            data = responses_sheet.get_all_records()
            df = pd.DataFrame(data)
            if df.empty: return None
            
            # 학번, 이름, 주제가 모두 일치하는 행 찾기
            # 학번은 문자열로 비교 (시트 데이터 형식에 따라 다를 수 있음)
            match = df[(df['학번'].astype(str) == str(student_id)) & 
                       (df['이름'] == name) & 
                       (df['주제'] == topic)]
            
            if not match.empty:
                # gspread는 1-indexed이며, 헤더가 1번이므로 index+2가 해당 행 번호입니다.
                return int(match.index[0] + 2)
            return None
        except Exception as e:
            st.warning(f"중복 체크 중 오류 발생: {e}")
            return None

    def submit_response(self, student_id, name, topic, content, row_to_update=None):
        """응답을 제출하거나 기존 응답을 업데이트합니다."""
        if not self.sheet: return False
        try:
            responses_sheet = self.sheet.worksheet("Responses")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [str(student_id), name, topic, content, now]
            
            if row_to_update:
                # 특정 행 업데이트
                responses_sheet.update(range_name=f"A{row_to_update}:E{row_to_update}", values=[new_row])
            else:
                # 새 행 추가
                responses_sheet.append_row(new_row)
            return True
        except Exception as e:
            st.error(f"제출 실패: {e}")
            return False

    def get_all_responses(self):
        """모든 응답 데이터를 가져옵니다 (관리자용)."""
        if not self.sheet: return pd.DataFrame()
        try:
            responses_sheet = self.sheet.worksheet("Responses")
            return pd.DataFrame(responses_sheet.get_all_records())
        except Exception:
            return pd.DataFrame()
