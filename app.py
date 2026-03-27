from flask import Flask, request, abort
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

# ================= CONFIG =================
LINE_ACCESS_TOKEN = 'P6Cei0JqgcS28dWbEWF65EHRKVaFx6svZTpEd3mbsaZBadkr9hxLHYSlEqi+p+ppnuM8qtoVeoagTBcKR2MMxKwtQgxLj65vpkTE8La/R63REldbEfUl4n+a+9UA7sP0TdGOsM/TWaIdSS35e0QLjQdB04t89/1O/w1cDnyilFU='
LINE_SECRET = '55c21c5623dca22db72b81942c2e689b'
SHEET_ID = '1uuY2Avi_l0Fp5qr2O-1y0-Vyx9i8I9EEOJE0-leEnDg'
CRED_FILE = 'cred.json'
# ==========================================

app = Flask(__name__)

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# ================= GOOGLE SHEET =================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

cred_json = os.environ.get("GOOGLE_CRED_JSON")
creds_dict = json.loads(cred_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# ================= SEARCH FUNCTION =================
def search_sheet(keyword):
    keyword = keyword.lower().strip()
    keyword = keyword.replace("-", "").replace(" ", "")

    data = sheet.get_all_records()
    results = []

    for row in data:
        plate = str(row['Vehicle_Plate']).lower().replace("-", "").replace(" ", "")

        if (
            keyword in str(row['SIM_Number']).lower() or
            keyword in str(row['Serial']).lower() or
            keyword in plate or
            keyword in str(row['Company_Name']).lower()
        ):
            results.append(row)

    if results:
        reply = ""
        for r in results[:5]:
            reply += (
                f"━━━━━━━━━━━━━━\n"
                f"📱 ข้อมูล SIM\n"
                f"━━━━━━━━━━━━━━\n"
                f"🔹 เบอร์: {r['SIM_Number']}\n"
                f"🧾 Serial: {r['Serial']}\n"
                f"📦 ประเภท: {r['Types']}\n"
                f"🗓️ เปิดใช้: {r['Activation_Date']}\n\n"
                f"📶 สถานะ: {r['SIM_Status']}\n"
                f"⏱️ วันที่สถานะ: {r['SIM_Status_Date']}\n"
                f"🚘 ทะเบียน: {r['Vehicle_Plate']}\n"
                f"🏢 บริษัท: {r['Company_Name']}\n"
                f"━━━━━━━━━━━━━━\n\n"
                
            )
    else:
        reply = "❌ ไม่พบข้อมูล"

    return reply

# ================= LINE WEBHOOK =================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(e)
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # 🧠 แยก keyword จากข้อความ
    if user_text.startswith("ค้นหา"):
        keyword = user_text.replace("ค้นหา", "").strip()
        reply = search_sheet(keyword)

    else:
        reply = (
            "พิมพ์คำว่า:\n"
            "🔎 ค้นหา <ข้อมูล>\n\n"
            "ตัวอย่าง:\n"
            "ค้นหา 70-0773\n"
            "ค้นหา 6694"
        )

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# ================= RUN =================
if __name__ == "__main__":
    app.run(port=5000)
