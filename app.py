import streamlit as st
import requests
import base64
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
import csv

CSV_URL = "https://docs.google.com/spreadsheets/d/15Los4GBwCHjiOm9TL-e3UwD7rnZ73rlzzcJo4EpOs24/gviz/tq?tqx=out:csv"

def get_api_url_from_csv():
    response = requests.get(CSV_URL)
    if response.status_code == 200:
        csv_data = response.text
        reader = csv.reader(csv_data.splitlines())
        next(reader)
        return next(reader)[0]
    else:
        st.error("❌ Không thể lấy API_URL từ Google Sheets.")
        st.stop()

def encode_image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def perform_ocr(image, mode="text"):
    try:
        api_endpoint = "/ocr"
        API_URL = get_api_url_from_csv() + api_endpoint
        img_base64 = encode_image_to_base64(image)
        data = {"image_base64": img_base64, "mode": mode}

        response = requests.post(API_URL, json=data)
        if response.status_code == 200:
            return response.json().get("response_message")
        else:
            st.error(f"❌ Lỗi API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"⚠️ Lỗi xử lý ảnh: {e}")
        return None

def pdf_to_images(pdf_bytes):
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page in doc:
        pix = page.get_pixmap(dpi=200)
        img = Image.open(BytesIO(pix.tobytes()))
        images.append(img)
    return images

# Giao diện
st.title("🧠 OCR VietNamese Images / PDFs")

option = st.radio("Chọn nguồn:", ["📂 Ảnh / PDF từ máy tính", "🌐 Ảnh từ URL"])
task_option = st.selectbox("📌 Loại trích xuất:", ["🔤 Trích xuất văn bản", "🧾 Trích xuất hóa đơn"])
ocr_mode = "bill" if "hóa đơn" in task_option else "text"

if option == "📂 Ảnh / PDF từ máy tính":
    uploaded_file = st.file_uploader("Chọn ảnh hoặc PDF", type=["png", "jpg", "jpeg", "pdf"])
    if uploaded_file:
        file_ext = uploaded_file.name.lower().split('.')[-1]
        if file_ext == "pdf":
            images = pdf_to_images(uploaded_file.read())
            for i, image in enumerate(images):
                st.image(image, caption=f"Trang {i+1}", use_column_width=True)
            if st.button(f"🔍 OCR Trang {i+1}", key=i):
                for i,image in enumerate(images): 
                    result = perform_ocr(image, mode=ocr_mode)
                    if result:
                        st.success(f"✅ Kết quả trang {i+1}:")
                        st.text(result)
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Ảnh đã tải", use_column_width=True)
            if st.button("🔍 Thực hiện OCR"):
                result = perform_ocr(image, mode=ocr_mode)
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
