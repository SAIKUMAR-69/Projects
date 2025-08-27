import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
from werkzeug.utils import secure_filename

from models import db, Candidate, Job, Evaluation
from services.resume_parser import extract_text_from_upload
from services.scoring import keyword_score, normalize_score
from services.openai_client import generate_job_fit

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
        recent = Evaluation.query.order_by(desc(Evaluation.created_at)).limit(5).all()
        return render_template("index.html", jobs=jobs, recent=recent)

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
        resume_text = extract_text_from_upload(uploaded_path)

        # Get candidate name from form (default "Candidate")
        candidate_name = request.form.get("candidate_name", "Candidate")

        # Persist candidate
        candidate = Candidate(name=candidate_name, resume_text=resume_text, skills_text="")
        db.session.add(candidate)
        db.session.commit()

        job_title = job.title
        job_desc = job.description

        # Simple keyword scoring
        kw_score = keyword_score(resume_text, job_desc)
        norm = normalize_score(kw_score)

        # LLM-based analysis (optional)
        summary, recommendations = generate_job_fit(resume_text, job_title, job_desc)

        # Persist evaluation
        eval_obj = Evaluation(
            candidate_id=candidate.id,
            job_id=job.id,
            score=norm,
            summary=summary,
            recommendations=recommendations,
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
            summary=summary,
            recommendations=recommendations
        )

    @app.route("/clear_history", methods=["POST"])
    def clear_history():
        try:
            num_deleted = Evaluation.query.delete()
            db.session.commit()
            flash(f"Cleared {num_deleted} evaluation(s).", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error clearing history: {str(e)}", "error")
        return redirect(url_for("index"))

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    return app


# ✅ Create the app instance for Gunicorn/Railway to use
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
