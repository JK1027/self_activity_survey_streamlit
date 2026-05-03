from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
from datetime import datetime

class GoogleSheetsManager:
    """
    구글 스프레드시트와 데이터를 주고받는 핵심 로직을 담당하는 클래스입니다.
    Streamlit의 GSheetsConnection을 사용하여 보안성과 안정성을 높였습니다.
    """
    def __init__(self):
        try:
            # st.connection을 통해 구글 시트 연결 (secrets의 정보를 자동으로 사용)
            self.conn = st.connection("gsheets", type=GSheetsConnection)
            self.spreadsheet_id = st.secrets["spreadsheet_id"]
            self.sheet_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
            self.connected = True
        except Exception as e:
            st.error(f"구글 시트 연결 실패: {e}")
            self.connected = False

    def is_connected(self):
        """현재 구글 시트와 연결된 상태인지 확인합니다."""
        return self.connected

    def get_today_topic(self):
        """Settings 탭에서 현재 설정된 '오늘의 주제' 값을 가져옵니다."""
        if not self.connected: return "연결 오류"
        try:
            # Settings 시트 읽기
            df = self.conn.read(spreadsheet=self.sheet_url, worksheet="Settings", ttl=0)
            # 'Key' 열이 'today_topic'인 행의 'Value'를 가져옵니다.
            topic = df[df["Key"] == "today_topic"]["Value"].values[0]
            return topic
        except Exception:
            return "설정된 주제가 없습니다."

    def update_today_topic(self, topic):
        """관리자가 입력한 새로운 주제를 Settings 탭에 저장합니다."""
        if not self.connected: return False
        try:
            # 현재 데이터 읽기
            df = self.conn.read(spreadsheet=self.sheet_url, worksheet="Settings", ttl=0)
            # 값 변경
            df.loc[df["Key"] == "today_topic", "Value"] = topic
            # 시트 업데이트
            self.conn.update(spreadsheet=self.sheet_url, worksheet="Settings", data=df)
            return True
        except Exception as e:
            st.error(f"주제 업데이트 실패: {e}")
            return False

    def check_existing_response(self, student_id, name, topic):
        """동일한 주제로 이미 제출한 기록이 있는지 확인합니다."""
        if not self.connected: return None
        try:
            df = self.conn.read(spreadsheet=self.sheet_url, worksheet="Responses", ttl=0)
            if df.empty: return None
            
            match = df[(df['학번'].astype(str) == str(student_id)) & 
                       (df['이름'] == name) & 
                       (df['주제'] == topic)]
            
            if not match.empty:
                # 행 번호 반환 (헤더 제외, 0부터 시작하므로 +2)
                return int(match.index[0] + 2)
            return None
        except Exception:
            return None

    def submit_response(self, student_id, name, topic, content, row_to_update=None):
        """학생의 응답을 시트에 저장합니다."""
        if not self.connected: return False
        try:
            # 현재 데이터 읽기
            df = self.conn.read(spreadsheet=self.sheet_url, worksheet="Responses", ttl=0)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if row_to_update:
                # 기존 행 업데이트 (index는 row-2)
                idx = row_to_update - 2
                df.iloc[idx] = [str(student_id), name, topic, content, now]
            else:
                # 새 행 추가
                new_data = pd.DataFrame([[str(student_id), name, topic, content, now]], 
                                       columns=['학번', '이름', '주제', '소감문', '제출시간'])
                df = pd.concat([df, new_data], ignore_index=True)
            
            # 시트 전체 업데이트
            self.conn.update(spreadsheet=self.sheet_url, worksheet="Responses", data=df)
            return True
        except Exception as e:
            st.error(f"제출 실패: {e}")
            return False

    def get_all_responses(self):
        """모든 응답 데이터를 가져옵니다."""
        if not self.connected: return pd.DataFrame()
        try:
            return self.conn.read(spreadsheet=self.sheet_url, worksheet="Responses", ttl=0)
        except Exception:
            return pd.DataFrame()
