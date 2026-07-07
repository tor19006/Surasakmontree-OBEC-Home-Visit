# เอกสารส่งมอบระบบ (Project Handshake)
## ระบบซิงค์ข้อมูลการเยี่ยมบ้าน สพฐ. (OBEC) โรงเรียนสุรศักดิ์มนตรี
---

เอกสารฉบับนี้ใช้สำหรับส่งมอบและอธิบายโครงสร้างระบบบันทึกการเยี่ยมบ้านนักเรียน ม.5/12 โรงเรียนสุรศักดิ์มนตรี โดยใช้แบบฟอร์มหน้าเว็บดั้งเดิมจาก D-School บันทึกรูปภาพและข้อมูลลง Google Sheets/Drive และซิงค์เชื่อมต่อเข้าสู่เซิร์ฟเวอร์ D-School อัตโนมัติ (100% Serverless & Automation)

---

## 📌 สถานะการดีพลอย (Deployment Status)

| รายการ | สถานะ | รายละเอียด |
|---|---|---|
| Google Apps Script Web App | ✅ ดีพลอยแล้ว | Version ล่าสุด |
| Web App URL (ฟอร์มนักเรียน) | ✅ พร้อมใช้งาน | [เปิดฟอร์ม](https://script.google.com/macros/s/AKfycbwnFQWes2OFB51bgXUddBzWbUfpv0WTFokMhP9dwY9XNYxF2c3z16GCNtnf9Xmt-288/exec) |
| Google Sheets DB | ✅ เชื่อมต่อแล้ว | [เปิดชีท](https://docs.google.com/spreadsheets/d/15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo/edit) |
| Sheet ID | `15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo` | ตั้งค่าใน Code.gs และ .env แล้ว |
| ครูผู้บันทึกข้อมูล | ✅ กำหนดค่า default | นายเอกณัฐ  ลุผลแท้ / ครูที่ปรึกษา (readonly) |
| อัปโหลดรูปภาพ | ✅ บังคับ 2 รูป | ภาพบ้าน + ภาพครอบครัว (แนวนอนเท่านั้น) |
| ผู้ให้ข้อมูลนักเรียน | ✅ บังคับกรอก | placeholder: "กรุณาใส่ชื่อ-นามสกุลผู้ให้ข้อมูล" |
| พิกัด GPS อัตโนมัติ | ⚠️ ข้อจำกัด | Google Apps Script iframe sandbox อาจบล็อก Geolocation API — ดูหัวข้อ 6 |

---

## 🛠️ 1. สถาปัตยกรรมระบบ (System Architecture)

การทำงานของระบบแบ่งออกเป็น 3 ส่วนหลัก ดังนี้:

```
[นักเรียน/ผู้ปกครอง] 
       │ (1. เปิด Web App URL กรอกข้อมูล & อัปโหลดรูปภาพ)
       ▼
[visit_form.html (Google Apps Script Web App)] 
       │ (2. ส่งข้อมูลฟอร์ม 155 ฟิลด์ + รูปภาพ Base64 ผ่าน google.script.run)
       ▼
[Google Apps Script Backend (Code.gs / obec_backend_web_app.js)]
       ├── (3. บันทึกรูปภาพ) ──> [Google Drive: โฟลเดอร์ OBEC_Home_Visit_Photos]
       └── (4. เขียนข้อมูลแถวใหม่) ──> [Google Sheets ID: 15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo]
                                               │
                                               │ (5. ดึงข้อมูลชีตคำตอบ & ดึงรูปภาพผ่าน OAuth)
                                               ▼
                                    [dschool_visit_sync.py (บอทบน WSL ของครู)]
                                               │
                                               │ (6. ส่งเซสชันเด็ก -> ส่งรูป -> บันทึกแบบฟอร์ม 155 ฟิลด์)
                                               ▼
                                    [เซิร์ฟเวอร์หลัก D-School (visit.php)]
```

---

## 📂 2. โครงสร้างไฟล์และการจัดเก็บ (File Directory)

ไฟล์ทั้งหมดที่เกี่ยวข้องกับโปรเจกต์นี้ได้รับการเก็บอยู่ในโฟลเดอร์โครงการ `/home/tor19006/dschool-weekly-report-bot/` และสำรองไว้บน Google Drive:

1. **`visit_form.html`** (~1,940 บรรทัด) - หน้าแบบฟอร์มหลักที่ให้เด็กกรอกข้อมูลหน้าตาเหมือน D-School ดั้งเดิม 100%
2. **`obec_backend_web_app.js`** (208 บรรทัด) - โค้ด Apps Script สำหรับทำหน้าที่เป็น API รับข้อมูลจากฟอร์ม (ใช้วางใน `Code.gs`)
3. **`dschool_visit_sync.py`** (316 บรรทัด) - สคริปต์ Python ในการดึงข้อมูลจากชีตมาประมวลผลและซิงค์ข้อมูลภาพ/ฟิลด์เข้า D-School
4. **`dashboard.html`** (348 บรรทัด) - แดชบอร์ดบอกสถานะและคู่มืออย่างง่ายสำหรับเครื่อง Local ของคุณครู
5. **`house_sample.jpg`** และ **`family_sample.jpg`** - ภาพตัวอย่างประกอบแนวนอนที่ฝังในฟอร์มในรูปแบบ Base64
6. **`.env`** - ไฟล์เก็บคอนฟิกูเรชันความปลอดภัย พิกัดโรงเรียนสุรศักดิ์มนตรี (`13.7753, 100.5556`) และ Sheet ID
7. **`handshake_project.md`** - เอกสารส่งมอบโครงการฉบับนี้

---

## 🚀 3. ขั้นตอนการตั้งค่าและดีพลอย (Deployment Guide)

### 3.1 การจัดเตรียมในฝั่ง Google Apps Script (Web App)
1. เข้าสู่ **[script.google.com](https://script.google.com)** ด้วยบัญชี Google ของคุณครู
2. สร้างโปรเจกต์ใหม่และนำโค้ดใน **`obec_backend_web_app.js`** ไปวางทับในไฟล์ `Code.gs` ทั้งหมด
3. ตัวแปร `var SPREADSHEET_ID` ถูกตั้งค่าเชื่อมไปยังชีต `15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo` เรียบร้อยแล้ว
4. กดปุ่ม **"+"** ข้างคำว่า Files -> เลือกประเภทไฟล์ **"HTML"** -> ตั้งชื่อว่า **`visit_form`** (ไม่ต้องใส่สกุล .html)
5. เปิดไฟล์ **`visit_form.html`** ทำการคัดลอกโค้ดทั้งหมดไปวางทับในไฟล์ `visit_form` ที่เพิ่งสร้างใหม่นี้
6. ทำการ **Deploy** (ปุ่มสีน้ำเงินมุมบนขวา) -> เลือก **New deployment**
   * **Select type:** เลือกไอคอนเฟืองและเลือก **Web app**
   * **Execute as:** เลือกเป็น **Me** (บัญชีของคุณครู)
   * **Who has access:** เลือกเป็น **Anyone** (ทุกคน)
7. กด Deploy และทำการกดยอมรับสิทธิ์การเข้าถึงความปลอดภัย (Authorize Access)
8. คัดลอก **Web app URL** ส่งให้นักเรียนกรอกข้อมูลเยี่ยมบ้านได้ทันที

### 3.2 URL ที่ดีพลอยแล้ว
```
https://script.google.com/macros/s/AKfycbwnFQWes2OFB51bgXUddBzWbUfpv0WTFokMhP9dwY9XNYxF2c3z16GCNtnf9Xmt-288/exec
```

### 3.3 การอัปเดตโค้ด
เมื่อต้องการอัปเดตโค้ดใหม่:
1. แก้ไขไฟล์ `Code.gs` หรือ `visit_form.html` ใน Apps Script
2. กด **Deploy** → **Manage deployments** → คลิกไอคอนดินสอ ✏️ → เปลี่ยน Version เป็น **"New version"** → กด **Deploy**

---

## 🐍 4. คู่มือการซิงค์ข้อมูลผ่าน Python Bot

เมื่อมีเด็กๆ ทยอยกรอกข้อมูลและส่งรูปภาพบ้านเข้ามา ข้อมูลจะถูกเก็บเรียงแถวใน Google Sheets และเก็บไฟล์ภาพใน Drive หน้าที่ของคุณครูมีเพียงการรันบอทเพื่อโอนย้ายข้อมูลทั้งหมดเข้า D-School ของโรงเรียนโดยอัตโนมัติ

### 4.1 การตั้งค่าระบบหลังบ้านคุณครู (บน WSL)
1. เปิดไฟล์ **`.env`** ในเครื่อง WSL (`/home/tor19006/dschool-weekly-report-bot/.env`) ยืนยันว่ามีค่า:
   ```env
   GOOGLE_SHEET_ID=15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo
   ```
2. โทเค็นความปลอดภัยของครูและพิกัดโรงเรียนสุรศักดิ์มนตรีจะถูกดึงผ่าน `gog` CLI อัตโนมัติโดยไม่จำเป็นต้องระบุ API Key ใดๆ เพิ่มเติม

### 4.2 การสั่งซิงค์ข้อมูล
เปิด Terminal และทำการรันคำสั่ง:
```bash
python3 dschool_visit_sync.py
```

**ขั้นตอนการซิงค์ที่บอททำให้อัตโนมัติ:**
1. ดึงแถวข้อมูลเยี่ยมบ้านทั้งหมดจาก Google Sheet
2. ตรวจสอบว่าแถวใดถูกประมวลผลไปแล้ว (ใช้ Timestamp ในการแยกแยะ) เพื่อซิงค์เฉพาะแถวข้อมูลใหม่
3. ดาวน์โหลดภาพ 2 ภาพของนักเรียนจาก Google Drive ผ่าน OAuth token ปลอดภัยสูง
4. ทำการ Login เข้าสู่ D-School และจับคู่การบันทึกของนักเรียนรายคน
5. ส่งภาพถ่ายบ้านและครอบครัวเข้าไปที่ uploader สารสนเทศของโรงเรียน (`savetofile.php`)
6. กรอกและส่งคำตอบแบบฟอร์ม 155 รายการตรงเข้าเมนูหลัก สพฐ. ของ D-School
7. บันทึกประวัติการส่งลงในไฟล์ `dschool_visit_sync_state.json` เพื่อป้องกันการส่งข้อมูลซ้ำซ้อน

---

## 🔧 5. ค่า Default ที่ตั้งไว้ในฟอร์ม

| ฟิลด์ | ค่า Default | สถานะ |
|---|---|---|
| คุณครูที่ไปเยี่ยมบ้าน (`teacher`) | นายเอกณัฐ  ลุผลแท้ | readonly (นักเรียนแก้ไขไม่ได้) |
| ตำแหน่ง/หน้าที่ (`teacher_position`) | ครูที่ปรึกษา | readonly (นักเรียนแก้ไขไม่ได้) |
| รหัสโรงเรียน (`school_id`) | 1010126001 | hidden |
| ภาคเรียน (`term`) | 0 | hidden |
| สถานการณ์เยี่ยม (`visit_status`) | เยี่ยมแล้ว | checked default |
| รูปแบบการเยี่ยม (`visit_type`) | ออนไซต์ | checked default |
| ครั้งที่เยี่ยม (`visit_time`) | 1 | default |

---

## ⚠️ 6. ข้อจำกัดที่ทราบ (Known Issues)

### พิกัด GPS อัตโนมัติ
Google Apps Script render หน้า HTML ภายใน **sandboxed iframe** ซึ่งมีข้อจำกัดด้าน Geolocation API — เบราว์เซอร์อาจไม่ขอ permission ตำแหน่งจากผู้ใช้โดยอัตโนมัติ

**วิธีแก้ไขชั่วคราว:**
- ฟิลด์ latitude/longitude ตั้งเป็น `readonly` + `required` — หากดึง GPS อัตโนมัติไม่ได้ จะมีปุ่ม **"📍 กดอนุญาตเพื่อดึงพิกัดตำแหน่งปัจจุบัน"** ให้กดด้วยตนเอง
- หากยังไม่ทำงาน ให้นักเรียนใส่พิกัดจาก Google Maps ด้วยตัวเอง (ปลด readonly ผ่าน DevTools หรือเพิ่มช่องกรอกแยก)

**วิธีแก้ไขถาวร (แนะนำสำหรับอนาคต):**
- ย้ายหน้าฟอร์มไป host บน static hosting (เช่น GitHub Pages, Cloudflare Pages) แทน Google Apps Script → จะได้ full Geolocation API access
- ใช้ Apps Script เป็น API backend อย่างเดียว (ผ่าน `doPost`)

---

## 🛡️ 7. ข้อมูลสำคัญในการบำรุงรักษาระบบ (Maintenance & Troubleshooting)

* **ความปลอดภัยของพิกัด GPS:** การกรอกฟิลด์ GPS ถูกจำกัดให้เป็น `readonly` และดึงค่าจากอุปกรณ์ตรงๆ เพื่อความเที่ยงตรง หากเด็กเปิดฟอร์มแล้วขึ้นเตือนเบราว์เซอร์ไม่รองรับ GPS ให้แนะนำให้เด็กเปิดเข้าใช้งานฟอร์มโดยใช้ **HTTPS** (เช่น ดีพลอยผ่าน Web App URL ปลายทางของ Google Apps Script ซึ่งเป็น https อยู่แล้ว)
* **ความปลอดภัยของภาพถ่าย:** ระบบบังคับคัดกรองให้อัปโหลดเฉพาะรูปภาพที่มีความกว้างมากกว่าความสูง (แนวนอน) เท่านั้น โดยระบบจะเช็คและบล็อกรูปแนวตั้งก่อนส่งเข้าระบบตั้งแต่แรก
* **รูปภาพบังคับอัปโหลด 2 รูป:** ฟอร์มจะไม่ยอมส่งหากไม่อัปโหลดทั้งรูปบ้านและรูปครอบครัว (validation ฝั่ง JavaScript)
* **เซสชันหมดอายุ:** บอทซิงค์พัฒนาขึ้นโดยเชื่อมโยงผ่าน Client API ของ D-School และ OAuth ของกูเกิลอย่างเป็นทางการ หากเกิดปัญหาการเชื่อมต่อหรือข้อมูลไม่ซิงค์ ให้รันเช็คสิทธิ์ด้วยคำสั่ง:
  ```bash
  GOG_KEYRING_PASSWORD=tp121158 gog status
  ```
  *(เพื่อยืนยันสถานะล็อกอิน หรือใช้แดชบอร์ด `dashboard.html` ในการตรวจสอบระบบ)*
