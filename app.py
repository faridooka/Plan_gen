from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
import tempfile
import os
from docx import Document
import openai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

app = Flask(__name__)

# ❗️CORS — тек нақты сайтқа рұқсат
CORS(app, origins=["https://cliledu.kz"])

# ✅ OpenAI клиенті (openai>=1.0.0 үшін)
from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 🔧 Промпт құрастыру: тек Информатика пәні үшін
def build_prompt(topic, grade, language_level, bloom_level):
    return f"""
You are a CLIL lesson planner for school teachers in Kazakhstan.

Create a full CLIL-based lesson plan for the subject "Informatics" on the topic "{topic}" for Grade {grade} students.
The learners' English level is {language_level}, and the cognitive focus should be based on Bloom's level: {bloom_level}.

The lesson plan must be structured as a 2-column table:
Column 1 — Section Name (e.g., Objectives, Assessment, Language Focus, etc.)
Column 2 — Content for each section (described in clear paragraphs)

Sections to include:
- Title of lesson
- Grade level
- Learning objectives (content + language)
- Assessment criteria
- Subject vocabulary (EN + KZ)
- Bloom’s level
- 4Cs focus (Content, Communication, Cognition, Culture)
- Pre-knowledge
- Lesson stages (Beginning – Middle – End)
- Differentiation
- Values
- ICT used
- Resources (include specific useful websites, tools, programs, and platforms with names and links that teachers can visit directly to use in class)

Output format must be a clean textual table with each row representing a section.
"""

@app.route("/generate_lessonplan", methods=["POST"])
@cross_origin(origins="https://cliledu.kz")
def generate_lessonplan():
    data = request.json
    topic = data.get("topic", "")
    grade = data.get("grade", "")
    language_level = data.get("language_level", "")
    bloom_level = data.get("bloom_level", "")

    prompt = build_prompt(topic, grade, language_level, bloom_level)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a CLIL methodology expert generating professional lesson plans."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    result = response.choices[0].message.content
    return jsonify({"lesson_plan": result})


@app.route("/download_lessonplan_docx", methods=["POST"])
@cross_origin(origins="https://cliledu.kz")
def download_lessonplan_docx():
    data = request.json
    content = data.get("lesson_plan", "")
    doc = Document()
    doc.add_heading("CLIL Lesson Plan", level=1)
    for line in content.split('\n'):
        doc.add_paragraph(line)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(temp_file.name)
    return send_file(temp_file.name, as_attachment=True, download_name="lesson_plan.docx")


@app.route("/download_lessonplan_pdf", methods=["POST"])
@cross_origin(origins="https://cliledu.kz")
def download_lessonplan_pdf():
    data = request.json
    content = data.get("lesson_plan", "")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=letter)
    width, height = letter
    y = height - 50

    c.setFont("Helvetica", 12)
    lines = content.split("\n")
    text_obj = c.beginText(50, y)
    text_obj.setFont("Helvetica", 12)

    max_chars = 100
    for line in lines:
        wrapped = [line[i:i+max_chars] for i in range(0, len(line), max_chars)]
        for part in wrapped:
            text_obj.textLine(part)
            y -= 15
            if y < 50:
                c.drawText(text_obj)
                c.showPage()
                y = height - 50
                text_obj = c.beginText(50, y)
                text_obj.setFont("Helvetica", 12)

    c.drawText(text_obj)
    c.save()
    return send_file(temp_file.name, as_attachment=True, download_name="lesson_plan.pdf")


if __name__ == "__main__":
    app.run(debug=True)
