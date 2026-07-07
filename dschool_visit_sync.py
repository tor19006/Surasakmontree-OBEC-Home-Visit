#!/usr/bin/env python3
"""
D-School Home Visit / OBEC Sync Bot (Self-healing dictionary-based sync with image sync)
Downloads responses and photos from Google Sheets/Drive and uploads them to D-School.
"""

import os
import re
import csv
import json
import datetime
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path
import requests

def load_env(env_path):
    env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    return env

def get_google_access_token():
    try:
        gog_bin = "/home/tor19006/gogcli/bin/gog"
        keyring_pwd = os.environ.get("GOG_KEYRING_PASSWORD", "tp121158")
        env = {**os.environ, "GOG_KEYRING_PASSWORD": keyring_pwd}
        
        res = subprocess.run(
            [gog_bin, "auth", "export", "-a", "eakanat.teach@gmail.com"],
            env=env, capture_output=True, text=True, check=True
        )
        data = json.loads(res.stdout)
        
        refresh_token = data.get("refresh_token")
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        
        token_url = "https://oauth2.googleapis.com/token"
        payload = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }).encode("utf-8")
        
        req = urllib.request.Request(token_url, data=payload, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("access_token")
    except Exception as e:
        print(f"Error fetching Google access token: {e}")
        return None

def login_dschool(env):
    mobile_id = env.get("DSCHOOL_MOBILE_ID")
    gcm_regid = env.get("DSCHOOL_GCM_REGID")
    user_id = env.get("DSCHOOL_USER_ID")
    school_id = env.get("DSCHOOL_SCHOOL_ID")
    
    base_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
        'Referer': 'https://dschool-g5w.gp-education.com/dschool_app_v2020/index.php'
    }

    app_params = {
        'app': 't', 'mobile_id': mobile_id, 'gcm_regid': gcm_regid,
        'user_id': user_id, 'school_id': school_id, 'type': 'a', 'change_stat': '1'
    }
    app_url = "https://dschool-g5w.gp-education.com/dschool_app_v2020/index.php"
    
    session = requests.Session()
    init_res = session.get(app_url, params=app_params, headers=base_headers, allow_redirects=False)
    phpsessid = session.cookies.get("PHPSESSID")
    
    if not phpsessid:
        set_cookie = init_res.headers.get('set-cookie', '')
        match = re.search(r'PHPSESSID=([^;]+)', set_cookie)
        if match:
            phpsessid = match.group(1)
            session.cookies.set("PHPSESSID", phpsessid, domain="dschool-g5w.gp-education.com")
        else:
            raise Exception("No PHPSESSID cookie found")
            
    d = datetime.datetime.now()
    qr_number = f"DSCHOOL-SC{d.year}{d.month:02d}{d.day:02d}10101010"
    qr_params = {
        'mobile_id': mobile_id, 'gcm_regid': gcm_regid, 'app': 't',
        'user_id': user_id, 'school_id': school_id, 'change_stat': '1', 'type': 'a',
        'qr': qr_number, 'latitude': '13.7753', 'longitude': '100.5556',
        'servername': 'dschool-g5w.gp-education.com', 'qr_pin': 'pass'
    }
    qr_url = "http://dschool-g5w.gp-education.com/dschoolapp_service/read_qrcode.php"
    qr_res = session.get(qr_url, params=qr_params, headers=base_headers)
    
    if "คุณได้เข้าสู่ระบบแล้ว" in qr_res.text:
        return session, phpsessid
    else:
        raise Exception(f"QR Confirmation failed")

def download_sheet_csv(spreadsheet_id, access_token):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def get_drive_file_bytes(drive_url, access_token):
    """Downloads file bytes from a Google Drive sharing URL using OAuth token."""
    file_id = None
    match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', drive_url)
    if match:
        file_id = match.group(1)
    else:
        match = re.search(r'id=([a-zA-Z0-9_-]+)', drive_url)
        if match:
            file_id = match.group(1)
            
    if not file_id:
        return None
        
    download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
    req = urllib.request.Request(
        download_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Error downloading image {drive_url}: {e}")
        return None

def upload_image_to_dschool(session, sd_no, student_name, filename, file_bytes, env):
    """Initializes uploader session and uploads a photo to D-School."""
    # 1. POST to index.php to set session variables inside visit_home_obec/php/
    index_url = "https://dschool-g5w.gp-education.com/dschool_app_v2020/visit_home_obec/php/index.php"
    payload = {
        'year': env.get("DSCHOOL_ACADEMIC_YEAR", "2569"),
        'school_id': env.get("DSCHOOL_SCHOOL_ID", "1010126001"),
        'edlevel': '3',
        'cls_no': '5/12',
        'term': '0',
        'teacher_name': env.get("DSCHOOL_TEACHER_NAME", "นายเอกณัฐ  ลุผลแท้"),
        'teacher_id': env.get("DSCHOOL_USER_ID", "1385"),
        'mainmenu': 'e',
        'submenu': 'e1',
        'sd_no': sd_no,
        'sd_name': student_name,
        'prefix': '1'
    }
    
    headers = {
        'Referer': 'https://dschool-g5w.gp-education.com/dschool_app_v2020/menu_p01.php?menu=system&submenu_id=p01',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
    }
    
    session.post(index_url, data=payload, headers=headers)

    # 2. POST to savetofile.php to save the file
    upload_url = "https://dschool-g5w.gp-education.com/dschool_app_v2020/visit_home_obec/php/savetofile.php"
    files = {
        'myFile': (filename, file_bytes, 'image/jpeg')
    }
    
    upload_headers = {
        'Referer': 'https://dschool-g5w.gp-education.com/dschool_app_v2020/visit_home_obec/php/index.php',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
    }
    
    res = session.post(upload_url, files=files, headers=upload_headers)
    res_text = res.text.strip().lower()
    if 'success' in res_text:
        print(f"  📷 Photo '{filename}' uploaded successfully.")
        return True
    elif 'full' in res_text:
        print(f"  📷 Photo '{filename}' already uploaded (maximum 2 photos reached).")
        return True
    else:
        print(f"  ❌ Failed to upload photo '{filename}': {res.text.strip()}")
        return False

def sync_obec():
    env_path = "/home/tor19006/dschool-weekly-report-bot/.env"
    env = load_env(env_path)
    
    spreadsheet_id = env.get("GOOGLE_SHEET_ID")
    if not spreadsheet_id:
        print("Error: GOOGLE_SHEET_ID not defined in .env")
        return
        
    print("Fetching Google Form responses...")
    access_token = get_google_access_token()
    if not access_token:
        print("Failed to get Google access token.")
        return
        
    try:
        csv_data = download_sheet_csv(spreadsheet_id, access_token)
    except Exception as e:
        print(f"Error downloading Google Sheet responses: {e}")
        return
        
    state_file = Path("/home/tor19006/dschool-weekly-report-bot/dschool_visit_sync_state.json")
    state = {}
    if state_file.exists():
        state = json.loads(state_file.read_text())
    processed_timestamps = set(state.get("processed_timestamps", []))
    
    lines = csv_data.strip().splitlines()
    if not lines or len(lines) < 2:
        print("No responses found in sheet.")
        return
        
    reader = csv.DictReader(lines)
    rows = list(reader)
    print(f"Total entries in sheet: {len(rows)}")
    
    print("Logging into D-School...")
    try:
        session, phpsessid = login_dschool(env)
        print("Logged in successfully.")
    except Exception as e:
        print(f"Failed to log into D-School: {e}")
        return
        
    new_processed = []
    success_count = 0
    fail_count = 0
    
    for row_idx, data_row in enumerate(rows):
        timestamp = data_row.get("timestamp")
        student_name = data_row.get("sd_name")
        sd_no = data_row.get("sd_no")
        
        if not timestamp or not student_name or not sd_no:
            print(f"Warning: Row {row_idx+1} is missing key identification fields. Skipped.")
            continue
            
        if timestamp in processed_timestamps:
            continue
            
        print(f"\nProcessing row {row_idx+1}: {student_name} ({timestamp})...")
        
        # 1. Handle image downloads & uploads to D-School uploader
        house_url = data_row.get("house_image_url")
        family_url = data_row.get("family_image_url")
        
        if house_url:
            print("  Downloading house photo from Google Drive...")
            house_bytes = get_drive_file_bytes(house_url, access_token)
            if house_bytes:
                upload_image_to_dschool(session, sd_no, student_name, f"{sd_no}_house.jpg", house_bytes, env)
                
        if family_url:
            print("  Downloading family photo from Google Drive...")
            family_bytes = get_drive_file_bytes(family_url, access_token)
            if family_bytes:
                upload_image_to_dschool(session, sd_no, student_name, f"{sd_no}_family.jpg", family_bytes, env)
        
        # 2. Prepare POST payload for form fields
        payload = data_row.copy()
        
        sheet_only_keys = ["timestamp", "house_image_url", "family_image_url", "student_select", ""]
        for key in sheet_only_keys:
            if key in payload:
                del payload[key]
                
        payload["submit"] = "บันทึกข้อมูล"
        
        # Set session for student in D-School
        sess_params = {
            'url': 'visit_home_obec/visit.php',
            'sname': 'sd_no', 'sdata': sd_no,
            'sname2': 'year', 'sdata2': payload.get("year", "2569"),
            'sname3': 'term', 'sdata3': '0',
            'sdata4': student_name
        }
        session.get("https://dschool-g5w.gp-education.com/dschool_app_v2020/set_sesstion.php", params=sess_params)
        
        # POST form data to visit.php
        post_url = "https://dschool-g5w.gp-education.com/dschool_app_v2020/visit_home_obec/visit.php"
        headers = {
            'Referer': 'https://dschool-g5w.gp-education.com/dschool_app_v2020/menu_p01.php?menu=system&submenu_id=p01',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
        }
        res_post = session.post(post_url, data=payload, headers=headers)
        
        if res_post.status_code == 200:
            print(f"✅ Synchronized OBEC Home Visit record and images for {student_name}")
            processed_timestamps.add(timestamp)
            new_processed.append(timestamp)
            success_count += 1
        else:
            print(f"❌ Failed to sync: HTTP {res_post.status_code}")
            fail_count += 1
            
    # Save state
    state["processed_timestamps"] = list(processed_timestamps)
    state_file.write_text(json.dumps(state, indent=2))
    
    print(f"\nOBEC Synchronization completed: {success_count} succeeded, {fail_count} failed.")

if __name__ == "__main__":
    sync_obec()
