import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime

class GoogleSheetsManager:
    """
    구글 스프레드시트와 데이터를 주고받는 핵심 로직을 담당하는 클래스입니다.
    라이브러리: gspread, google-auth 등을 사용합니다.
    """
    def __init__(self):
        # 구글 드라이브 및 스프레드시트 API 접근 권한 설정
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        try:
            # Streamlit의 secrets 기능을 사용하여 보안 정보(JSON 키 등)를 안전하게 불러옵니다.
            if "gcp_service_account" in st.secrets:
                self.creds = Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"],
                    scopes=self.scope
                )
                self.client = gspread.authorize(self.creds)
                # 시트 ID도 secrets에서 관리합니다.
                self.spreadsheet_id = st.secrets["spreadsheet_id"]
                self.sheet = self.client.open_by_key(self.spreadsheet_id)
            else:
                self.sheet = None
        except Exception as e:
            # 연결 실패 시 사용자에게 에러 메시지를 표시합니다.
            st.error(f"구글 시트 연결 실패: {e}")
            self.sheet = None

    def is_connected(self):
        """현재 구글 시트와 연결된 상태인지 확인합니다."""
        return self.sheet is not None

    def get_today_topic(self):
        """Settings 탭에서 현재 설정된 '오늘의 주제' 값을 가져옵니다."""
        if not self.sheet: return "연결 오류"
        try:
            settings_sheet = self.sheet.worksheet("Settings")
            data = settings_sheet.get_all_records()
            # 'Key' 열이 'today_topic'인 행의 'Value'를 찾아 반환합니다.
            for row in data:
                if row.get("Key") == "today_topic":
                    return row.get("Value")
            return "설정된 주제가 없습니다."
        except Exception:
            return "주제 불러오기 실패"

    def update_today_topic(self, topic):
        """관리자가 입력한 새로운 주제를 Settings 탭에 저장합니다."""
        if not self.sheet: return False
        try:
            settings_sheet = self.sheet.worksheet("Settings")
            # 'today_topic'이라는 키워드가 있는 셀을 찾아 그 옆 칸(Value)을 업데이트합니다.
            cell = settings_sheet.find("today_topic")
            settings_sheet.update_cell(cell.row, cell.col + 1, topic)
            return True
        except Exception as e:
            st.error(f"주제 업데이트 실패: {e}")
            return False

    def check_existing_response(self, student_id, name, topic):
        """
        동일한 주제로 이미 제출한 기록이 있는지 확인합니다.
        체크 기준: 학번 + 이름 + 주제
        """
        if not self.sheet: return None
        try:
            responses_sheet = self.sheet.worksheet("Responses")
            data = responses_sheet.get_all_records()
            df = pd.DataFrame(data)
            if df.empty: return None
            
            # 학번, 이름, 주제가 모두 일치하는 행을 필터링합니다.
            match = df[(df['학번'].astype(str) == str(student_id)) & 
                       (df['이름'] == name) & 
                       (df['주제'] == topic)]
            
            if not match.empty:
                # 데이터가 있다면 해당 행 번호를 반환합니다. (gspread는 1부터 시작하며 헤더를 포함하므로 index+2)
                return int(match.index[0] + 2)
            return None
        except Exception as e:
            st.warning(f"중복 체크 중 오류 발생: {e}")
            return None

    def submit_response(self, student_id, name, topic, content, row_to_update=None):
        """
        학생의 응답을 시트에 저장합니다.
        row_to_update 값이 있으면 해당 행을 덮어쓰고, 없으면 새 행으로 추가합니다.
        """
        if not self.sheet: return False
        try:
            responses_sheet = self.sheet.worksheet("Responses")
            # 현재 시간을 기록합니다.
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = [str(student_id), name, topic, content, now]
            
            if row_to_update:
                # 지정된 행의 범위를 업데이트합니다.
                responses_sheet.update(range_name=f"A{row_to_update}:E{row_to_update}", values=[new_row])
            else:
                # 시트의 마지막에 새로운 행을 추가합니다.
                responses_sheet.append_row(new_row)
            return True
        except Exception as e:
            st.error(f"제출 실패: {e}")
            return False

    def get_all_responses(self):
        """관리자 페이지에서 활용할 모든 응답 데이터를 데이터프레임 형태로 가져옵니다."""
        if not self.sheet: return pd.DataFrame()
        try:
            responses_sheet = self.sheet.worksheet("Responses")
            return pd.DataFrame(responses_sheet.get_all_records())
        except Exception:
            return pd.DataFrame()
