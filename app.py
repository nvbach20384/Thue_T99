import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

API_KEY_DOCS_CACHE = {}
INPUTS_DIR = os.path.join(os.path.dirname(__file__), 'inputs')

SYSTEM_PROMPT = "Bạn là chuyên gia tư vấn dựa trên tài liệu. BẮT BUỘC đọc nội dung các file PDF đính kèm để trả lời. Trích dẫn rõ nguồn. Nếu không có thông tin, trả lời: Theo tài liệu cung cấp, tôi không tìm thấy thông tin này."

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    api_key = data.get('api_key')

    if not message or not api_key:
        return jsonify({'error': 'Thiếu tin nhắn hoặc API Key'}), 400

    try:
        genai.configure(api_key=api_key)
        
        # Caching logic
        if api_key not in API_KEY_DOCS_CACHE:
            uploaded_docs = []
            if os.path.exists(INPUTS_DIR):
                for filename in os.listdir(INPUTS_DIR):
                    if filename.lower().endswith('.pdf'):
                        file_path = os.path.join(INPUTS_DIR, filename)
                        uploaded_file = genai.upload_file(path=file_path)
                        uploaded_docs.append(uploaded_file)
            API_KEY_DOCS_CACHE[api_key] = uploaded_docs

        uploaded_docs = API_KEY_DOCS_CACHE[api_key]
        
        model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
        
        contents = uploaded_docs + [message]
        response = model.generate_content(contents)
        
        return jsonify({'reply': response.text})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'Đã có lỗi xảy ra từ máy chủ. Vui lòng kiểm tra lại API Key.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
