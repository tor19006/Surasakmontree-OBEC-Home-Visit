# เอกสารส่งมอบระบบ (Project Handshake)
## ระบบซิงค์ข้อมูลการเยี่ยมบ้าน สพฐ. (OBEC) โรงเรียนสุรศักดิ์มนตรี
---

เอกสารฉบับนี้ใช้สำหรับส่งมอบและอธิบายโครงสร้างระบบบันทึกการเยี่ยมบ้านนักเรียน ม.5/12 โรงเรียนสุรศักดิ์มนตรี โดยใช้แบบฟอร์มหน้าเว็บดั้งเดิมจาก D-School บันทึกรูปภาพและข้อมูลลง Google Sheets/Drive และซิงค์เชื่อมต่อเข้าสู่เซิร์ฟเวอร์ D-School อัตโนมัติ (100% Serverless & Automation)

---

## 📌 สถานะการดีพลอย (Deployment Status)

| รายการ | สถานะ | รายละเอียด |
|---|---|---|
| ฟอร์มเยี่ยมบ้าน (Frontend) | ✅ GitHub Pages | https://tor19006.github.io/Surasakmontree-OBEC-Home-Visit/visit_form.html |
| Backend API | ✅ Google Apps Script | https://script.google.com/macros/s/AKfycbwnFQWes2OFB51bgXUddBzWbUfpv0WTFokMhP9dwY9XNYxF2c3z16GCNtnf9Xmt-288/exec |
| GitHub Repository | ✅ Public | https://github.com/tor19006/Surasakmontree-OBEC-Home-Visit |
| Google Sheets DB | ✅ เชื่อมต่อแล้ว | https://docs.google.com/spreadsheets/d/15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo/edit |
| Sheet ID | — | `15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo` |
| พิกัด GPS อัตโนมัติ | ✅ ทำงานได้ | Host แยกบน GitHub Pages ไม่ถูก iframe sandbox บล็อก |

---

## 🛠️ 1. สถาปัตยกรรมระบบ (System Architecture)

```
[นักเรียน/ผู้ปกครอง]
       │ (1. เปิด GitHub Pages URL → ดึง GPS อัตโนมัติ / คำนวณระยะทางถนนจริง)
       ▼
[visit_form.html @ GitHub Pages]
       │ (2. fetch POST ข้อมูลฟอร์ม 155 ฟิลด์ + รูปภาพ Base64)
       ▼
[Google Apps Script Web App (Code.gs)]
       ├── (3. บันทึกรูปภาพ) ──> [Google Drive: โฟลเดอร์ OBEC_Home_Visit_Photos]
       └── (4. เขียนข้อมูลแถวใหม่) ──> [Google Sheets DB (คอลัมน์ Self-healing)]
                                               │
                                               │ (5. ดึงข้อมูลชีต & ดึงรูปภาพเพื่อส่งต่อเข้า D-School)
                                               ▼
                                    [เซิร์ฟเวอร์หลัก D-School (visit.php)]
```

---

## 📂 2. โครงสร้างไฟล์ (File Directory)

GitHub: `https://github.com/tor19006/Surasakmontree-OBEC-Home-Visit`

| ไฟล์ | ขนาด | คำอธิบาย |
|---|---|---|
| `visit_form.html` | ~1,940 บรรทัด | หน้าแบบฟอร์มหลัก 155 ฟิลด์ (host บน GitHub Pages) |
| `index.html` | 10 บรรทัด | Redirect ไปยัง visit_form.html |
| `obec_backend_web_app.js` | 208 บรรทัด | โค้ด Apps Script Backend (วางใน Code.gs) |
| `dashboard.html` | 348 บรรทัด | แดชบอร์ดคู่มือคุณครู |
| `house_sample.jpg` | 823 KB | ภาพตัวอย่างบ้าน (ฝังเป็น Base64 ในฟอร์ม) |
| `family_sample.jpg` | 918 KB | ภาพตัวอย่างครอบครัว (ฝังเป็น Base64 ในฟอร์ม) |
| `.env` | — | คอนฟิก D-School + Sheet ID (ไม่อัปขึ้น GitHub) |
| `handshake_project.md` | — | เอกสารส่งมอบฉบับนี้ |

---

## 🚀 3. ขั้นตอนการดีพลอย (Deployment Guide)

### 3.1 ฝั่ง Google Apps Script (Backend API)
1. เข้า **[script.google.com](https://script.google.com)** ด้วยบัญชี Google ของครู
2. สร้างโปรเจกต์ใหม่ → วางโค้ด **`obec_backend_web_app.js`** ทับในไฟล์ `Code.gs`
3. ตัวแปร `SPREADSHEET_ID` ถูกตั้งค่าเชื่อมชีต `15WANqgFkntecn1oYcmPuFaQ_ORtZIdvnifhhUvNd-Mo` แล้ว
4. สร้างไฟล์ HTML ชื่อ **`visit_form`** → วางโค้ด `visit_form.html` (สำหรับเข้าผ่าน GAS URL โดยตรง — ทางเลือกสำรอง)
5. Deploy → Web app → Execute as: Me → Who has access: Anyone
6. คัดลอก Web App URL

### 3.2 ฝั่ง GitHub Pages (Frontend หลัก)
1. แก้ไขไฟล์ `visit_form.html` ในเครื่อง
2. Commit & Push:
   ```bash
   git add -A && git commit -m "อัปเดตฟอร์ม" && git push
   ```
3. GitHub Pages จะอัปเดตอัตโนมัติภายใน 1-2 นาที
4. URL: `https://tor19006.github.io/Surasakmontree-OBEC-Home-Visit/visit_form.html`

### 3.3 การอัปเดต Backend
1. แก้ไข `Code.gs` ใน Apps Script
2. Deploy → Manage deployments → ✏️ → New version → Deploy

---

## 🔧 4. ค่า Default ที่ตั้งไว้ในฟอร์ม

| ฟิลด์ | ค่า Default | สถานะ |
|---|---|---|
| คุณครูที่ไปเยี่ยมบ้าน (`teacher`) | นายเอกณัฐ  ลุผลแท้ | readonly ล็อก |
| ตำแหน่ง/หน้าที่ (`teacher_position`) | ครูที่ปรึกษา | readonly ล็อก |
| ผู้ให้ข้อมูลนักเรียน (`parent`) | — | บังคับกรอกชื่อ-นามสกุล |
| รูปภาพบ้าน (`house_image`) | — | บังคับอัปโหลด (แนวนอนเท่านั้น) |
| รูปภาพครอบครัว (`family_image`) | — | บังคับอัปโหลด (แนวนอนเท่านั้น) |
| รหัสโรงเรียน (`school_id`) | 1010126001 | hidden |
| ภาคเรียน (`term`) | 0 | hidden |
| สถานการณ์เยี่ยม (`visit_status`) | เยี่ยมแล้ว | checked |
| รูปแบบการเยี่ยม (`visit_type`) | ออนไซต์ | checked |
| ครั้งที่เยี่ยม (`visit_time`) | 1 | default |

---

## 📍 5. ระบบพิกัด GPS อัตโนมัติ

### การทำงาน
1. เมื่อเปิดฟอร์ม → เบราว์เซอร์ขอ permission ตำแหน่งทันที
2. ดึงพิกัด latitude/longitude จาก Geolocation API
3. คำนวณระยะทางถนนจริงไปโรงเรียน (ผ่าน OSRM Routing API)
4. Fallback: คำนวณระยะทางเส้นตรง (Haversine formula)
5. พิกัดโรงเรียนสุรศักดิ์มนตรี: `13.7753, 100.5556`

### เหตุผลที่ Host บน GitHub Pages
Google Apps Script render HTML ใน sandboxed iframe ที่บล็อก Geolocation API → ย้ายฟอร์มมา host บน GitHub Pages เพื่อให้ GPS ทำงานได้เต็มรูปแบบ โดยใช้ Apps Script เป็น Backend API อย่างเดียว (ส่งข้อมูลผ่าน `fetch POST`)

---

## 🛡️ 6. การบำรุงรักษา (Maintenance & Troubleshooting)

* **GPS ไม่ทำงาน:** ตรวจสอบว่านักเรียนเปิด URL ของ GitHub Pages (ไม่ใช่ URL ของ Google Apps Script) และอนุญาต permission ตำแหน่งในเบราว์เซอร์
* **ภาพถ่าย:** ระบบบังคับอัปโหลดรูปแนวนอน (กว้าง > สูง) เท่านั้น — ระบบจะบล็อกรูปแนวตั้งอัตโนมัติ
* **ภาพบังคับ 2 รูป:** ฟอร์มไม่ยอมส่งหากไม่อัปโหลดทั้งรูปบ้านและรูปครอบครัว
* **อัปเดตฟอร์ม:** แก้ไข `visit_form.html` → `git add -A && git commit -m "..." && git push` → GitHub Pages อัปเดตอัตโนมัติ
* **อัปเดต Backend:** แก้ `Code.gs` ใน Apps Script → Deploy → Manage deployments → New version

---

## 📋 7. รายชื่อนักเรียน ม.5/12 (32 คน)

| ลำดับ | รหัส | ชื่อ-นามสกุล |
|---|---|---|
| 1 | 51655 | นายธนพงษ์ นาเอก |
| 2 | 51666 | นายนนทวัฒน์ โอรทัต |
| 3 | 51669 | นายนราธิป เมืองศรีสุข |
| 4 | 51705 | นายพิรภพ จันทา |
| 5 | 51706 | นายพิษณุ ศิริวงค์ |
| 6 | 51744 | นายรัชชานนท์ โคตรสูงเนิน |
| 7 | 51745 | นายรัชชานนท์ โทนุบล |
| 8 | 51758 | นายวิภพ ตุละรัต |
| 9 | 51798 | นายอนุศักดิ์ ตรีสุข |
| 10 | 51799 | นายอนุสิทธิ์ ลัคนาลิขิต |
| 11 | 51800 | นายอเนชา อ่อนน้อม |
| 12 | 52004 | นายจิรภัทร แสงทอง |
| 13 | 54063 | นายจักรกมล ทองมี |
| 14 | 54086 | นายนวพล ชูเนตร |
| 15 | 51857 | นางสาวณัฏฐธิดา พูลทรัพย์ |
| 16 | 51860 | นางสาวณัฐชา ยิ้มแย้ม |
| 17 | 51888 | นางสาวนภสร คุ้มกัน |
| 18 | 51909 | นางสาวปิ่นมณี แสงนิล |
| 19 | 51965 | นางสาววรัชญา วันวาน |
| 20 | 51966 | นางสาววรัทยา โททอง |
| 21 | 52005 | นางสาวอินทิรา ศรีพึ่งจั่น |
| 22 | 53518 | นางสาวทยิดา ษัฏเสน |
| 23 | 51575 | นายกษิดิ์เดช บรรทัดจันทร์ |
| 24 | 51576 | นายกษิติดนัย ไชยพูน |
| 25 | 51577 | นายกษิตินนท์ ไชยพูน |
| 26 | 51662 | นายธัชฐพัฒน์ บุญมีมา |
| 27 | 51742 | นายรพิพัฒน์ พันธุ์พิมาย |
| 28 | 51764 | นายศรัญ เหนี่ยงขำ |
| 29 | 51783 | นายสุกฤษฎิ์ แช่มช้อย |
| 30 | 54091 | นายปวรปรัชญ์ ธารีพุฒ |
| 31 | 54104 | นายภาสวิชญ์ สนเอี่ยม |
| 32 | 54108 | นายวชิรวิทย์ รอดสดใส |
