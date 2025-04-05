import streamlit as st
import requests
import base64
import os
import csv
from io import StringIO

CSV_URL = "https://docs.google.com/spreadsheets/d/15Los4GBwCHjiOm9TL-e3UwD7rnZ73rlzzcJo4EpOs24/gviz/tq?tqx=out:csv"

def get_api_url_from_csv():
    response = requests.get(CSV_URL)
    if response.status_code == 200:
        csv_data = response.text
        reader = csv.reader(StringIO(csv_data))
        next(reader)  # Bỏ qua tiêu đề
        return next(reader)[0]  # Lấy ô A2
    else:
        st.error("❌ Không thể lấy API_URL từ Google Sheets.")
        st.stop()

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def perform_ocr(img_path, mode="text"):
    try:
        api_endpoint = "/ocr" 
        API_URL = get_api_url_from_csv() + api_endpoint

        if os.path.isfile(img_path):
            img_base64 = encode_image_to_base64(img_path)
            data = {"image_base64": img_base64, "mode": mode}
        else:
            data = {"image_url": img_path,  "mode": mode}

        response = requests.post(API_URL, json=data)

        if response.status_code == 200:
            return response.json().get("response_message")
        else:
            st.error(f"❌ Lỗi API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"⚠️ Lỗi xử lý ảnh: {e}")
        return None


st.title("🧠 OCR App sử dụng API")
option = st.radio("Chọn nguồn ảnh:", ["📂 Ảnh từ máy tính", "🌐 Ảnh từ URL"])

task_option = st.selectbox("📌 Chọn loại trích xuất:", ["🔤 Trích xuất văn bản", "🧾 Trích xuất hóa đơn"])
ocr_mode = "bill" if "hóa đơn" in task_option else "text"

if option == "📂 Ảnh từ máy tính":
    uploaded_file = st.file_uploader("Chọn ảnh", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        with open("temp_img.jpg", "wb") as f:
            f.write(uploaded_file.read())
        st.image("temp_img.jpg", caption="Ảnh đã tải lên", use_column_width=True)
        if st.button("🔍 Thực hiện OCR"):
            result = perform_ocr("temp_img.jpg", mode=ocr_mode)
            if result:
                st.success("✅ Kết quả OCR:")
                st.text(result)

elif option == "🌐 Ảnh từ URL":
    img_url = st.text_input("Nhập URL ảnh")
    if img_url:
        st.image(img_url, caption="Ảnh từ URL", use_column_width=True)
        if st.button("🔍 Thực hiện OCR"):
            result = perform_ocr(img_url, mode=ocr_mode)
            if result:
                st.success("✅ Kết quả OCR:")
                st.text(result)
