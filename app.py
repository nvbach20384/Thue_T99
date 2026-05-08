import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import traceback

app = Flask(__name__)

API_KEY_DOCS_CACHE = {}
INPUTS_DIR = os.path.join(os.path.dirname(__file__), 'inputs')

SYSTEM_PROMPT = "Bạn là trợ lý ảo TT99_Q&A, chuyên gia giải đáp về Thông tư 99/2025/BTC. Bạn BẮT BUỘC dựa vào nội dung các file PDF được cung cấp để trả lời câu hỏi. Khi trả lời, hãy trích dẫn chính xác số trang hoặc mục trong tài liệu. Nếu tài liệu không đề cập, hãy lịch sự thông báo cho người dùng."

@app.route('/')
def index():
    files = []
    if os.path.exists(INPUTS_DIR):
        for filename in os.listdir(INPUTS_DIR):
            if filename.lower().endswith('.pdf'):
                files.append(filename)
    return render_template('index.html', pdf_files=files)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    api_key = data.get('api_key')

    if not message or not api_key:
        return jsonify({'error': 'Thiếu tin nhắn hoặc API Key'}), 400

    try:
        print(f"--- Start processing message ---")
        genai.configure(api_key=api_key)
        
        # Caching logic
        if api_key not in API_KEY_DOCS_CACHE:
            print("Uploading docs to Google AI...")
            uploaded_docs = []
            if os.path.exists(INPUTS_DIR):
                for filename in os.listdir(INPUTS_DIR):
                    if filename.lower().endswith('.pdf'):
                        file_path = os.path.join(INPUTS_DIR, filename)
                        print(f"Uploading: {filename}")
                        uploaded_file = genai.upload_file(path=file_path)
                        uploaded_docs.append(uploaded_file)
            API_KEY_DOCS_CACHE[api_key] = uploaded_docs
            print("Upload complete.")

        uploaded_docs = API_KEY_DOCS_CACHE[api_key]
        
        # Auto-detect best model
        try:
            print("Detecting available models...")
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            print(f"Available models: {available_models}")
            
            if 'models/gemini-1.5-flash' in available_models:
                model_name = 'gemini-1.5-flash'
            elif 'models/gemini-1.5-flash-latest' in available_models:
                model_name = 'gemini-1.5-flash-latest'
            elif 'models/gemini-1.5-pro' in available_models:
                model_name = 'gemini-1.5-pro'
            elif available_models:
                model_name = available_models[0].replace('models/', '')
            else:
                model_name = 'gemini-1.5-flash' # Fallback
        except Exception as e:
            print(f"Error listing models: {str(e)}")
            model_name = 'gemini-1.5-flash' # Fallback

        print(f"Using model: {model_name}")
        model = genai.GenerativeModel(model_name=model_name, system_instruction=SYSTEM_PROMPT)
        
        contents = uploaded_docs + [message]
        response = model.generate_content(contents)
        
        print("Received response from AI.")
        return jsonify({'reply': response.text})

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return jsonify({'error': 'Google AI đang bận (Quá tải yêu cầu). Vui lòng đợi 1 phút rồi thử lại.'}), 429
        traceback.print_exc()
        return jsonify({'error': f'Lỗi hệ thống AI: {error_msg}'}), 500



if __name__ == '__main__':
    # Tắt reloader vì nó gây lỗi lặp lại trên môi trường Windows này
    app.run(host='0.0.0.0', port=5000, debug=False)
