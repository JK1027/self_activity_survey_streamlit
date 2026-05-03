import streamlit as st
import pandas as pd
from datetime import datetime
import re
import json

# --- 연결 방식을 자동 선택하는 로직 ---
# 방법 1: st-gsheets-connection (학생 앱에서 성공한 방식)
# 방법 2: gspread 직접 연결 (fallback)

def _clean_private_key(pk: str) -> str:
    """
    학생용 앱에서 성공한 방식대로, 오직 리터럴 \\n만 실제 줄바꿈으로 바꿉니다.
    """
    if not pk:
        return pk
    # 리터럴 \n을 실제 줄바꿈으로 변환
    cleaned = pk.replace("\\n", "\n")
    # 이미 줄바꿈이 포함된 경우 중복 방지 및 PEM 헤더 정돈
    if "-----BEGIN PRIVATE KEY-----" not in cleaned:
        cleaned = f"-----BEGIN PRIVATE KEY-----\n{cleaned}\n-----END PRIVATE KEY-----\n"
    return cleaned


def _get_service_account_info(magic_key=None) -> dict:
    """Secrets에서 정보를 읽거나, 비상용 '매직 키'를 주입받습니다."""
    if "GCP_JSON" in st.secrets:
        info = json.loads(st.secrets["GCP_JSON"])
    elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        info = dict(st.secrets["connections"]["gsheets"])
    else:
        info = {}

    # 매직 키가 있으면 오염된 키 대신 사용
    if magic_key:
        info["private_key"] = magic_key
    else:
        pk = info.get("private_key", "")
        info["private_key"] = _clean_private_key(pk)
    
    return info


def _connect_gspread(info: dict):
    """gspread로 직접 연결합니다."""
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)


class GoogleSheetsManager:
    """
    구글 스프레드시트 매니저.
    먼저 st-gsheets-connection을 시도하고, 실패하면 gspread 직접 연결로 전환합니다.
    """

    def __init__(self):
        self.connected = False
        self._use_gspread = False
        self._sheet = None
        self._conn = None
        self._magic_key = None # 비상용 키 저장소

        try:
            self.spreadsheet_id = st.secrets["spreadsheet_id"]
        except Exception:
            return

        self.sheet_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
        self.connect()

    def connect(self, magic_key=None):
        """연결을 시도합니다. 매직 키가 주입되면 gspread 방식을 우선하여 강제 연결합니다."""
        if magic_key:
            self._magic_key = magic_key
        
        # 매직 키가 있으면 gspread(방법 2)로 즉시 강제 연결 (가장 확실함)
        if self._magic_key:
            try:
                info = _get_service_account_info(magic_key=self._magic_key)
                client = _connect_gspread(info)
                self._sheet = client.open_by_key(self.spreadsheet_id)
                self._use_gspread = True
                self.connected = True
                return True
            except Exception as e:
                st.error(f"비상 연결 실패: {e}")
                return False

        # 일반적인 경우에는 학생용 방식(방법 1) 우선 시도
        try:
            from streamlit_gsheets import GSheetsConnection
            self._conn = st.connection("gsheets", type=GSheetsConnection)
            self._conn.read(spreadsheet=self.sheet_url, worksheet="Settings", ttl=0)
            self.connected = True
            self._use_gspread = False
            return True
        except Exception:
            # 실패하면 gspread(방법 2)로 시도
            try:
                info = _get_service_account_info()
                client = _connect_gspread(info)
                self._sheet = client.open_by_key(self.spreadsheet_id)
                self._use_gspread = True
                self.connected = True
                return True
            except Exception as e:
                if not magic_key: # 매직키 입력 시도가 아닐 때만 에러 표시
                    st.error(f"구글 시트 연결 실패: {e}")
                return False

    def is_connected(self):
        return self.connected

    def get_today_topic(self):
        if not self.connected:
            return "연결 오류"
        try:
            if self._use_gspread:
                ws = self._sheet.worksheet("Settings")
                df = pd.DataFrame(ws.get_all_records())
            else:
                df = self._conn.read(spreadsheet=self.sheet_url, worksheet="Settings", ttl=0)
            return df[df["Key"] == "today_topic"]["Value"].values[0]
        except Exception:
            return "설정된 주제가 없습니다."

    def update_today_topic(self, topic):
        if not self.connected:
            return False
        try:
            if self._use_gspread:
                ws = self._sheet.worksheet("Settings")
                df = pd.DataFrame(ws.get_all_records())
                idx = df[df["Key"] == "today_topic"].index[0]
                ws.update_cell(idx + 2, 2, topic)
            else:
                df = self._conn.read(spreadsheet=self.sheet_url, worksheet="Settings", ttl=0)
                df.loc[df["Key"] == "today_topic", "Value"] = topic
                self._conn.update(spreadsheet=self.sheet_url, worksheet="Settings", data=df)
            return True
        except Exception as e:
            st.error(f"주제 업데이트 실패: {e}")
            return False

    def check_existing_response(self, student_id, name, topic):
        if not self.connected:
            return None
        try:
            if self._use_gspread:
                ws = self._sheet.worksheet("Responses")
                df = pd.DataFrame(ws.get_all_records())
            else:
                df = self._conn.read(spreadsheet=self.sheet_url, worksheet="Responses", ttl=0)
            if df.empty:
                return None
            match = df[
                (df["학번"].astype(str) == str(student_id))
                & (df["이름"] == name)
                & (df["주제"] == topic)
            ]
            return int(match.index[0] + 2) if not match.empty else None
        except Exception:
            return None

    def submit_response(self, student_id, name, topic, content, row_to_update=None):
        if not self.connected:
            return False
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self._use_gspread:
                ws = self._sheet.worksheet("Responses")
                new_row = [str(student_id), name, topic, content, now]
                if row_to_update:
                    ws.update(f"A{row_to_update}:E{row_to_update}", [new_row])
                else:
                    ws.append_row(new_row)
            else:
                df = self._conn.read(spreadsheet=self.sheet_url, worksheet="Responses", ttl=0)
                if row_to_update:
                    idx = row_to_update - 2
                    df.iloc[idx] = [str(student_id), name, topic, content, now]
                else:
                    new_data = pd.DataFrame(
                        [[str(student_id), name, topic, content, now]],
                        columns=["학번", "이름", "주제", "소감문", "제출시간"],
                    )
                    df = pd.concat([df, new_data], ignore_index=True)
                self._conn.update(spreadsheet=self.sheet_url, worksheet="Responses", data=df)
            return True
        except Exception as e:
            st.error(f"제출 실패: {e}")
            return False

    def get_all_responses(self):
        if not self.connected:
            return pd.DataFrame()
        try:
            if self._use_gspread:
                ws = self._sheet.worksheet("Responses")
                return pd.DataFrame(ws.get_all_records())
            else:
                return self._conn.read(spreadsheet=self.sheet_url, worksheet="Responses", ttl=0)
        except Exception:
            return pd.DataFrame()
