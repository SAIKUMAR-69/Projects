import os
import re
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from models import db, Candidate, Job, Evaluation
from services.resume_parser import extract_text_from_upload
from services.scoring import keyword_score, normalize_score

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-secret"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            "sqlite:///" + os.path.join(app.instance_path, "resume_analyzer.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10 MB
    )

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.route("/", methods=["GET"])
    def index():
        jobs = Job.query.order_by(Job.title.asc()).all()
        return render_template("index.html", jobs=jobs)

    @app.route("/analyze", methods=["POST"])
    def analyze():
        job_id = request.form.get("job_id")
        if not job_id:
            flash("Please select a job.", "error")
            return redirect(url_for("index"))

        job = Job.query.get(int(job_id))

        # Handle file upload
        if "resume" not in request.files:
            flash("No resume file provided.", "error")
            return redirect(url_for("index"))
        file = request.files["resume"]
        if file.filename == "" or not allowed_file(file.filename):
            flash("Please upload a PDF, DOCX, or TXT resume.", "error")
            return redirect(url_for("index"))

        filename = secure_filename(file.filename)
        uploaded_path = os.path.join(
            "instance", f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
        )
        file.save(uploaded_path)

        # Extract text from resume
        resume_text = extract_text_from_upload(uploaded_path).lower()
        candidate_name = request.form.get("candidate_name", "Candidate")

        # Persist candidate
        candidate = Candidate(name=candidate_name, resume_text=resume_text, skills_text="")
        db.session.add(candidate)
        db.session.commit()

        job_title = job.title
        job_desc = job.description.lower()

        # Keyword scoring
        kw_score = keyword_score(resume_text, job_desc)
        norm = normalize_score(kw_score)

        # ---------- Extract keywords ----------
        words = re.findall(r'\b\w+\b', job_desc)
        stop_words = {"and", "or", "the", "a", "an", "to", "for", "with", "in", "on", "of"}
        keywords = [w for w in words if w not in stop_words]
        top_keywords = [k for k, _ in Counter(keywords).most_common(10)]

        matched_keywords = [kw for kw in top_keywords if kw in resume_text]
        if not matched_keywords:
            matched_keywords = top_keywords[:3]  # fallback

        kw_sample = ", ".join(matched_keywords)

        # ---------- Tailored templates based on keyword match count ----------
        match_count = len(matched_keywords)
        if match_count <= 3:
            summary_templates = [
                "This resume demonstrates some experience with {keywords}, showing potential to grow into the {job_title} role.",
                "Candidate has initial exposure to {keywords}. Focusing on these areas could strengthen fit for {job_title}."
            ]
            recommendation_templates = [
                "Consider gaining more hands-on experience with {keywords} to increase alignment with {job_title} requirements.",
                "Focus on improving proficiency in {keywords} to enhance candidacy for {job_title}."
            ]
        elif match_count <= 6:
            summary_templates = [
                "Shows solid experience in {keywords}, indicating good alignment with {job_title} responsibilities.",
                "Resume reflects meaningful work involving {keywords}, supporting suitability for {job_title}."
            ]
            recommendation_templates = [
                "Continue building expertise in {keywords} to further excel as a {job_title}.",
                "Enhancing skills with {keywords} can improve readiness for {job_title} tasks."
            ]
        else:
            summary_templates = [
                "Demonstrates strong expertise in {keywords}, making the candidate highly suitable for {job_title}.",
                "Resume highlights exceptional proficiency in {keywords}, aligning perfectly with {job_title} expectations."
            ]
            recommendation_templates = [
                "Maintain and expand experience with {keywords} to maximize impact as a {job_title}.",
                "Further application of {keywords} will continue to strengthen suitability for {job_title}."
            ]

        # Generate 100 varied summaries/recommendations using templates
        summaries = []
        recommendations = []
        for i in range(100):
            summary_template = summary_templates[i % len(summary_templates)]
            recommendation_template = recommendation_templates[i % len(recommendation_templates)]
            summaries.append(summary_template.format(keywords=kw_sample, job_title=job_title))
            recommendations.append(recommendation_template.format(keywords=kw_sample, job_title=job_title))

        # Deterministic selection: use min(match_count-1, 99)
        index = min(match_count - 1, 99)
        selected_summary = summaries[index]
        selected_recommendation = recommendations[index]

        # Highlight keywords in bold
        for kw in matched_keywords:
            selected_summary = re.sub(f"\\b({kw})\\b", r"<b>\1</b>", selected_summary, flags=re.IGNORECASE)
            selected_recommendation = re.sub(f"\\b({kw})\\b", r"<b>\1</b>", selected_recommendation, flags=re.IGNORECASE)

        # Persist evaluation
        eval_obj = Evaluation(
            candidate_id=candidate.id,
            job_id=job.id,
            score=norm,
            summary=selected_summary,
            recommendations=selected_recommendation,
            created_at=datetime.utcnow()
        )
        db.session.add(eval_obj)
        db.session.commit()

        return render_template(
            "results.html",
            candidate=candidate,
            job_title=job_title,
            job_desc=job_desc,
            score=norm,
            summary=selected_summary,
            recommendation=selected_recommendation
        )

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    return app


# Create app instance
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
