import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import toml
import os

def test_connection():
    try:
        secrets_path = "c:/Coding3/self_activity_survey_streamlit/.streamlit/secrets.toml"
        if not os.path.exists(secrets_path):
            print(f"Error: {secrets_path} not found")
            return
            
        with open(secrets_path, "r", encoding="utf-8") as f:
            secrets = toml.load(f)
        
        info = dict(secrets["gcp_service_account"])
        # 치환 로직 (중요: \n을 실제 개행으로)
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
        
        creds = Credentials.from_service_account_info(
            info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        print("Success: Credentials loaded.")
        
        client = gspread.authorize(creds)
        spreadsheet_id = secrets["spreadsheet_id"]
        sheet = client.open_by_key(spreadsheet_id)
        print(f"Success: Connected to spreadsheet: {sheet.title}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
