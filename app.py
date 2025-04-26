import streamlit as st
import requests
import base64
import os
import csv
from io import StringIO
from pdf2image import convert_from_bytes
from PIL import Image

# === Google Sheets chứa API URL ===
CSV_URL = "https://docs.google.com/spreadsheets/d/15Los4GBwCHjiOm9TL-e3UwD7rnZ73rlzzcJo4EpOs24/gviz/tq?tqx=out:csv"

def get_api_url_from_csv():
    response = requests.get(CSV_URL)
    if response.status_code == 200:
        csv_data = response.text
        reader = csv.reader(StringIO(csv_data))
        next(reader)  # Bỏ qua header
        return next(reader)[0]  # Lấy ô A2
    else:
        st.error("❌ Không thể lấy API_URL từ Google Sheets.")
        st.stop()

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

def encode_pil_to_base64(pil_image):
    buffered = StringIO()
    pil_image.save("temp.jpg", format="JPEG")
    with open("temp.jpg", "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def perform_ocr(image_input, mode="text", is_pil=False):
    try:
        api_endpoint = "/ocr" 
        API_URL = get_api_url_from_csv() + api_endpoint

        if is_pil:
            img_base64 = encode_pil_to_base64(image_input)
            data = {"image_base64": img_base64, "mode": mode}
        elif os.path.isfile(image_input):
            img_base64 = encode_image_to_base64(image_input)
            data = {"image_base64": img_base64, "mode": mode}
        else:
            data = {"image_url": image_input,  "mode": mode}

        response = requests.post(API_URL, json=data)

        if response.status_code == 200:
            return response.json().get("response_message")
        else:
            st.error(f"❌ Lỗi API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"⚠️ Lỗi xử lý ảnh: {e}")
        return None

# === Giao diện Streamlit ===
st.title("🧠 OCR VietNamese Images & PDF")
option = st.radio("Chọn nguồn ảnh:", ["📂 Từ máy tính", "🌐 Từ URL"])

task_option = st.selectbox("📌 Chọn loại trích xuất:", ["🔤 Trích xuất văn bản", "🧾 Trích xuất hóa đơn"])
ocr_mode = "bill" if "hóa đơn" in task_option else "text"

# === Ảnh từ máy tính ===
if option == "📂 Từ máy tính":
    uploaded_file = st.file_uploader("Chọn ảnh hoặc PDF", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file is not None:
        file_ext = uploaded_file.name.lower().split('.')[-1]

        if file_ext == "pdf":
            images = convert_from_bytes(uploaded_file.read(), dpi=200)
            st.write(f"📄 Phát hiện {len(images)} trang từ PDF.")

            for i, image in enumerate(images):
                st.image(image, caption=f"Trang {i+1}", use_column_width=True)

                if st.button(f"🔍 OCR Trang {i+1}", key=f"ocr_btn_{i}"):
                    result = perform_ocr(image, mode=ocr_mode, is_pil=True)
                    if result:
                        st.success(f"✅ Kết quả OCR - Trang {i+1}:")
                        st.text(result)
        else:
            with open("temp_img.jpg", "wb") as f:
                f.write(uploaded_file.read())
            st.image("temp_img.jpg", caption="Ảnh đã tải lên", use_column_width=True)

            if st.button("🔍 Thực hiện OCR"):
                result = perform_ocr("temp_img.jpg", mode=ocr_mode)
                if result:
                    st.success("✅ Kết quả OCR:")
                    st.text(result)

# === Ảnh từ URL ===
elif option == "🌐 Từ URL":
    img_url = st.text_input("📎 Dán URL ảnh vào đây")
    if img_url:
        st.image(img_url, caption="Ảnh từ URL", use_column_width=True)
        if st.button("🔍 Thực hiện OCR"):
            result = perform_ocr(img_url, mode=ocr_mode)
            if result:
                st.success("✅ Kết quả OCR:")
                st.text(result)
