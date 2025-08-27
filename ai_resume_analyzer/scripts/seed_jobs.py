import csv, os
from app import create_app
from models import db, Job

app = create_app()
with app.app_context():
    path = os.path.join("data", "jobs_seed.csv")
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not Job.query.filter_by(title=row["title"]).first():
                db.session.add(Job(title=row["title"], description=row["description"], skills=row["skills"]))
        db.session.commit()
        print("Seeded jobs.")
