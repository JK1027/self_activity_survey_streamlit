import streamlit as st
import pandas as pd
from datetime import datetime
import re
import json

# --- 연결 방식을 자동 선택하는 로직 ---
# 방법 1: st-gsheets-connection (학생 앱에서 성공한 방식)
# 방법 2: gspread 직접 연결 (fallback)

def _clean_private_key(pk: str) -> str:
    """어떤 형식의 private key든 표준 PEM으로 재조립합니다."""
    # 헤더/푸터 제거
    core = pk.replace("-----BEGIN PRIVATE KEY-----", "")
    core = core.replace("-----END PRIVATE KEY-----", "")
    # 핵심: 리터럴 \n(백슬래시+n)을 먼저 제거해야 n이 남지 않음
    core = core.replace("\\n", "\n")   # 리터럴 \n → 실제 줄바꿈으로 통일
    core = core.replace("\r", "")      # CR 제거
    core = core.replace("\n", "")      # 줄바꿈 제거
    core = core.replace(" ", "")       # 공백 제거
    core = core.strip()
    # 표준 PEM 형식으로 재조립
    return f"-----BEGIN PRIVATE KEY-----\n{core}\n-----END PRIVATE KEY-----\n"


def _get_service_account_info() -> dict:
    """Secrets에서 서비스 계정 정보를 읽고, private_key를 세척합니다."""
    # GCP_JSON이 있으면 최우선
    if "GCP_JSON" in st.secrets:
        info = json.loads(st.secrets["GCP_JSON"])
    elif "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        info = dict(st.secrets["connections"]["gsheets"])
    elif "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
    else:
        raise ValueError("Secrets에 인증 정보가 없습니다.")

    # split-key 방식 지원
    pk = info.get("private_key", "")
    if not pk:
        k1 = st.secrets.get("key1", "")
        k2 = st.secrets.get("key2", "")
        if k1 and k2:
            pk = k1 + k2

    if not pk:
        raise ValueError("private_key를 찾을 수 없습니다.")

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
        self._sheet = None  # gspread용
        self._conn = None   # GSheetsConnection용

        try:
            self.spreadsheet_id = st.secrets["spreadsheet_id"]
        except Exception:
            st.error("Secrets에 spreadsheet_id가 없습니다.")
            return

        self.sheet_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"

        # 방법 1: GSheetsConnection 시도
        try:
            from streamlit_gsheets import GSheetsConnection
            self._conn = st.connection("gsheets", type=GSheetsConnection)
            # 실제 읽기 테스트
            self._conn.read(spreadsheet=self.sheet_url, worksheet="Settings", ttl=0)
            self.connected = True
            return
        except Exception:
            pass  # 실패하면 방법 2로

        # 방법 2: gspread 직접 연결
        try:
            info = _get_service_account_info()
            client = _connect_gspread(info)
            self._sheet = client.open_by_key(self.spreadsheet_id)
            self._use_gspread = True
            self.connected = True
        except Exception as e:
            st.error(f"연결 실패: {e}")

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
