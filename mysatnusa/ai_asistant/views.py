import json
import requests
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

API_KEY = "AIzaSyBotKjgCQ-qnnnuW9O8RlrRHBPKN4k88AI"  # ganti sama punyamu
@csrf_exempt
def gemini_chat_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "Hanya menerima POST request"}, status=405)

    try:
        data = json.loads(request.body)
        user_input = data.get("user_input", "").strip()

        if not user_input:
            return JsonResponse({"error": "user_input kosong"}, status=400)

        # Ambil data knowledge base
        response = requests.get("http://127.0.0.1:8000/api/master/get_knowledge_data", headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})

        if response.status_code != 200:
            return JsonResponse({"error": "Gagal ambil data knowledge base"}, status=500)

        kb_json = response.json()
        internal_json_str = json.dumps(kb_json.get("data", {}), indent=2)

        dot_ai_prompt = f"""
            Nama kamu adalah Dot AI, asisten cerdas berbasis AI yang dibuat khusus untuk membantu dan mewakili *Department of Transformation* (DoT). 
            Tugas kamu adalah menjawab pertanyaan pengguna yang ditujukan kepada DoT. 
            Kamu bertindak sebagai perwakilan resmi yang memberikan informasi yang jelas, akurat, dan relevan tentang departemen ini. 
            Tugas kamu adalah menjawab pertanyaan pengguna berdasarkan:


            1. Pengetahuan umum yang kamu ketahui.
            2. Informasi internal perusahaan dalam format JSON (terlampir di bawah).

            Kamu harus menentukan apakah pertanyaan ini termasuk:
            - 🧩 Pertanyaan **internal** (tentang proyek, teknologi yang digunakan, karyawan, posisi kerja, dll), atau
            - 🌍 Pertanyaan **umum** (misal definisi AI, sejarah React, manfaat cloud computing, dll)

            ### Tugas penting kamu:
            - Jika pertanyaan internal → gunakan data internal JSON.
            - Jika pertanyaan umum → gunakan pengetahuan umum kamu.
            - ❌ Jangan pernah menyebut atau menampilkan `project_id`.
            - ❌ Jangan menyebutkan bahwa kamu "Dot AI" **kecuali ditanya langsung** (contoh: "siapa kamu?").
            - Jawaban harus relevan, jelas, dan sesuai konteks.

            ### Indikator pertanyaan internal:
            Perhatikan kata seperti:
            - “siapa saja yang terlibat”, “teknologi yang dipakai”, “kapan proyek dimulai”, “posisi pekerjaan”, “status internship”
            - Nama teknologi dalam project (contoh: PyTorch, Keras, Scikit-learn)
            - Role seperti UI/UX, Mobile Developer, Front End Developer

            ### Contoh pertanyaan internal:
            - "Siapa yang terlibat di proyek?"
            - "Teknologi apa saja yang digunakan?"
            - "Ada posisi kerja apa yang tersedia?" 

            ### Contoh pertanyaan umum:
            - "Apa itu machine learning?"
            - "Kenapa React banyak dipakai frontend?"
            - "Bedanya AI dan IoT apa?"

            ---

            📂 Data internal (dalam format JSON):

            ```json
            {internal_json_str}
        
            Dan ini pertanyaan dari pengguna: {user_input}.
        """

        gemini_response = requests.post(
            f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": dot_ai_prompt}]}]
            }
        )

        print("Status Code:", gemini_response.status_code)
        print("Response Text:", gemini_response.text)

        if gemini_response.status_code != 200:
            return JsonResponse({
                "error": "Gagal generate jawaban dari Gemini",
                "detail": gemini_response.text
            }, status=500)

        reply = gemini_response.json()

        if "candidates" not in reply or not reply["candidates"]:
            return JsonResponse({
                "error": "Tidak ada respons dari Gemini",
                "raw_response": reply
            }, status=500)

        try:
            output_text = reply['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return JsonResponse({
                "error": "Struktur response tidak sesuai",
                "detail": str(e),
                "raw_response": reply
            }, status=500)

        return JsonResponse({"response": output_text})
    except Exception as e:
        traceback.print_exc()
        log_exception(request, e)
        return JsonResponse({"error": str(e)}, status=500)