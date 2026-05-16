from flask import Flask, request, jsonify, render_template
from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch, PyPDF2, docx

app = Flask(__name__)
tokenizer = AutoTokenizer.from_pretrained("savasy/bert-base-turkish-squad")
model = AutoModelForQuestionAnswering.from_pretrained("savasy/bert-base-turkish-squad")

def read_file(file):
    name = file.filename.lower()
    if name.endswith(".txt"):
        return file.read().decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(file)
        return " ".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        return " ".join(p.text for p in docx.Document(file).paragraphs)
    return ""

def answer_question(question, context):
    inputs = tokenizer(question, context, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    start = outputs.start_logits.argmax()
    end = outputs.end_logits.argmax() + 1
    answer = tokenizer.decode(inputs["input_ids"][0][start:end], skip_special_tokens=True)
    score = torch.softmax(outputs.start_logits, dim=1).max().item()
    return answer, score

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    context = read_file(request.files["file"])
    question = request.form["question"]
    answer, score = answer_question(question, context)
    if score < 0.1 or not answer.strip():
        return jsonify({"answer": "Dosyada alakalı bir cevap bulunamadı."})
    return jsonify({"answer": answer, "score": round(score, 2)})

if __name__ == "__main__":
    app.run(debug=True)