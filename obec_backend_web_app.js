/**
 * Google Apps Script Web App Backend for OBEC Home Visit Form
 * 
 * Instructions:
 * 1. Go to https://script.google.com
 * 2. Create a new project.
 * 3. Delete any default code, paste this code.
 * 4. Replace SPREADSHEET_ID below with your Google Sheet ID (or leave empty to create a new one automatically).
 * 5. Click "Deploy" -> "New deployment".
 * 6. Select Type: "Web app".
 * 7. Set:
 *    - Execute as: "Me" (your email)
 *    - Who has access: "Anyone" (so students can submit without logging in).
 * 8. Select `authorizeRequiredServices` in the function dropdown and click "Run" once.
 *    Approve the Google Sheets/Drive permissions when prompted.
 * 9. Click "Deploy", authorize the permissions, and copy the "Web app URL".
 * 10. Paste the copied Web app URL into the `visit_form.html` file (replacing "REPLACE_WITH_WEB_APP_URL" on line ~js).
 */

var SPREADSHEET_ID = "1gL_qBY5ksUruQ8ROdxgarlJuVKrV0hZKEfUs9x3RJPo"; // Linked to OBEC Home Visit Sheet

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    
    // 1. Initialize Sheet
    var ss;
    if (SPREADSHEET_ID) {
      ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    } else {
      ss = SpreadsheetApp.create("OBEC Home Visit Responses DB");
      SPREADSHEET_ID = ss.getId();
    }
    var sheet = ss.getSheets()[0];
    
    // 2. Handle File Uploads to Google Drive
    var houseImageUrl = "";
    var familyImageUrl = "";
    var folderName = "OBEC_Home_Visit_Photos";
    
    // Get or create folder
    var folders = DriveApp.getFoldersByName(folderName);
    var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);
    
    if (data.house_image_base64) {
      var houseFile = saveBase64File(data.house_image_base64, data.house_image_name || "house.jpg", folder);
      houseImageUrl = houseFile.getUrl();
      // Remove base64 data to keep sheet clean
      delete data.house_image_base64;
    }
    
    if (data.family_image_base64) {
      var familyFile = saveBase64File(data.family_image_base64, data.family_image_name || "family.jpg", folder);
      familyImageUrl = familyFile.getUrl();
      // Remove base64 data to keep sheet clean
      delete data.family_image_base64;
    }
    
    // Add file URLs and Timestamp to the data object
    data["timestamp"] = new Date().toISOString();
    data["house_image_url"] = houseImageUrl;
    data["family_image_url"] = familyImageUrl;
    
    // 3. Dynamically Map Fields to Columns (Self-Healing)
    var headers = [];
    if (sheet.getLastColumn() > 0) {
      headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    }
    
    // Add any new fields to the headers
    var newFieldsFound = false;
    for (var key in data) {
      if (headers.indexOf(key) === -1) {
        headers.push(key);
        newFieldsFound = true;
      }
    }
    
    // Rewrite headers if new columns are found
    if (newFieldsFound || sheet.getLastColumn() === 0) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    }
    
    // Prepare the row data matching the header columns
    var rowData = headers.map(function(header) {
      var val = data[header];
      if (Array.isArray(val)) {
        return val.join(", "); // Join checkboxes with commas
      }
      return val !== undefined ? val : "";
    });
    
    // Append the row
    sheet.appendRow(rowData);
    
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Data saved successfully",
      sheetId: SPREADSHEET_ID,
      houseUrl: houseImageUrl,
      familyUrl: familyImageUrl
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// Helper to save base64 string as file to Google Drive
function saveBase64File(base64Data, filename, folder) {
  var splitData = base64Data.split(",");
  var contentType = splitData[0].match(/:(.*?);/)[1];
  var rawData = Utilities.base64Decode(splitData[1]);
  var blob = Utilities.newBlob(rawData, contentType, filename);
  var file = folder.createFile(blob);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return file;
}

// Run this once from the Apps Script editor after deploying/updating code.
// It forces Google to ask for the Spreadsheet and Drive permissions used by submissions.
function authorizeRequiredServices() {
  var runnerEmail = getRunnerEmail_();
  var ss;

  try {
    ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  } catch (error) {
    throw new Error(
      "เปิด Google Sheet ไม่ได้: บัญชีที่กำลังรัน Apps Script ยังไม่มีสิทธิ์เข้าถึงชีตนี้\n" +
      "บัญชีที่รันอยู่: " + runnerEmail + "\n" +
      "Sheet ID: " + SPREADSHEET_ID + "\n\n" +
      "วิธีแก้: เปิด Google Sheet นี้ แล้วกด Share ให้บัญชีด้านบนเป็น Editor จากนั้นกลับมากด Run ฟังก์ชัน authorizeRequiredServices อีกครั้ง\n" +
      "รายละเอียดจาก Google: " + error.message
    );
  }

  var folderName = "OBEC_Home_Visit_Photos";
  var folder;

  try {
    var folders = DriveApp.getFoldersByName(folderName);
    folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);
  } catch (error) {
    throw new Error(
      "เข้าถึง Google Drive ไม่ได้: กรุณากดอนุญาตสิทธิ์ Google Drive ให้ Apps Script\n" +
      "บัญชีที่รันอยู่: " + runnerEmail + "\n" +
      "รายละเอียดจาก Google: " + error.message
    );
  }
  
  return {
    status: "success",
    runnerEmail: runnerEmail,
    spreadsheetName: ss.getName(),
    folderName: folder.getName()
  };
}

function getRunnerEmail_() {
  try {
    return Session.getEffectiveUser().getEmail() || Session.getActiveUser().getEmail() || "(ไม่สามารถอ่านอีเมลบัญชีที่รันได้)";
  } catch (error) {
    return "(ไม่สามารถอ่านอีเมลบัญชีที่รันได้)";
  }
}

// Serve the visit_form.html page on GET request
function doGet(e) {
  var html = HtmlService.createTemplateFromFile('visit_form');
  return html.evaluate()
    .setTitle('บันทึกการเยี่ยมบ้าน สพฐ. - โรงเรียนสุรศักดิ์มนตรี')
    .setSandboxMode(HtmlService.SandboxMode.IFRAME)
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// Expose function directly for HTML frontend via google.script.run
function saveFormData(data) {
  try {
    var ss;
    if (SPREADSHEET_ID) {
      ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    } else {
      ss = SpreadsheetApp.getActiveSpreadsheet() || SpreadsheetApp.create("OBEC Home Visit Responses DB");
      SPREADSHEET_ID = ss.getId();
    }
    var sheet = ss.getSheets()[0];
    
    var houseImageUrl = "";
    var familyImageUrl = "";
    var folderName = "OBEC_Home_Visit_Photos";
    
    var folders = DriveApp.getFoldersByName(folderName);
    var folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(folderName);
    
    if (data.house_image_base64) {
      var houseFile = saveBase64File(data.house_image_base64, data.house_image_name || "house.jpg", folder);
      houseImageUrl = houseFile.getUrl();
      delete data.house_image_base64;
    }
    
    if (data.family_image_base64) {
      var familyFile = saveBase64File(data.family_image_base64, data.family_image_name || "family.jpg", folder);
      familyImageUrl = familyFile.getUrl();
      delete data.family_image_base64;
    }
    
    data["timestamp"] = new Date().toISOString();
    data["house_image_url"] = houseImageUrl;
    data["family_image_url"] = familyImageUrl;
    
    var headers = [];
    if (sheet.getLastColumn() > 0) {
      headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    }
    
    var newFieldsFound = false;
    for (var key in data) {
      if (headers.indexOf(key) === -1) {
        headers.push(key);
        newFieldsFound = true;
      }
    }
    
    if (newFieldsFound || sheet.getLastColumn() === 0) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    }
    
    var rowData = headers.map(function(header) {
      var val = data[header];
      if (Array.isArray(val)) {
        return val.join(", ");
      }
      return val !== undefined ? val : "";
    });
    
    sheet.appendRow(rowData);
    
    return {
      status: "success",
      message: "Data saved successfully",
      sheetId: SPREADSHEET_ID,
      houseUrl: houseImageUrl,
      familyUrl: familyImageUrl
    };
    
  } catch (error) {
    return {
      status: "error",
      message: error.toString()
    };
  }
}
