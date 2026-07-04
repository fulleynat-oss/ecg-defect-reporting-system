
import os, csv, io
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key-before-hosting")

db_url = os.environ.get("DATABASE_URL")
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///" + os.path.join(BASE_DIR, "ecg_defects.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
db = SQLAlchemy(app)

STATIONS = ["Kuntenase","Akyawkrom 2","Bekwai 2","Akyawkrom 1","Abono","Bekwai 1","Piase","Abrankese","Sawuah","Esereso","Konongo","Ejisu","Other"]
SEVERITIES = ["Critical","High","Medium","Low"]
STATUSES = ["Open","In Progress","Awaiting Materials","Completed"]
EQUIPMENT = ["Circuit Breaker","Isolator","Cable End Isolator","Busbar Isolator","Earth Switch","Earthing System","Protection Relay","Control Panel","Indication Lamps","Trip Circuit","Closing Circuit","Battery Bank","Battery Charger/Rectifier","DC Supply System","Metering Equipment","SCADA/RTU","Communication Equipment","Cable Trench","Air Conditioner","Fire Extinguishers","Door/Lock","Window Blinds","Back Gate","Wash Basin/Drainage","Office Chairs","Other"]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="station")
    station = db.Column(db.String(120), nullable=True)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class Defect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    station = db.Column(db.String(120), nullable=False)
    feeder_area = db.Column(db.String(120), nullable=False)
    equipment = db.Column(db.String(120), nullable=False)
    defect = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(30), nullable=False)
    recommended_action = db.Column(db.Text)
    status = db.Column(db.String(50), default="Open")
    responsible_person = db.Column(db.String(120))
    target_date = db.Column(db.String(50))
    completed_date = db.Column(db.String(50))
    remarks = db.Column(db.Text)
    photo_filename = db.Column(db.String(255))

def seed_users():
    if User.query.count() == 0:
        users = [("boss","boss123","boss",None),("admin","admin123","admin",None),("kuntenase","station123","station","Kuntenase"),("bekwai","station123","station","Bekwai")]
        for username,pw,role,station in users:
            u = User(username=username, role=role, station=station)
            u.set_password(pw)
            db.session.add(u)
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_users()

def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user(): return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def boss_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        u = current_user()
        if not u or u.role not in ["boss","admin"]:
            flash("You do not have permission to view that page.","error")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip().lower()
        password = request.form.get("password","")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard" if user.role in ["boss","admin"] else "index"))
        flash("Invalid username or password.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/", methods=["GET","POST"])
@login_required
def index():
    u = current_user()
    if request.method == "POST":
        station = request.form.get("station","").strip()
        if u.role == "station" and u.station:
            station = u.station
        feeder_area = request.form.get("feeder_area","").strip()
        equipment = request.form.get("equipment","").strip()
        defect_text = request.form.get("defect","").strip()
        severity = request.form.get("severity","").strip()
        if not station or not feeder_area or not equipment or not defect_text or not severity:
            flash("Fill Station, Feeder/Area, Equipment, Defect and Severity.","error")
            return redirect(url_for("index"))
        photo_filename = None
        photo = request.files.get("photo")
        if photo and photo.filename:
            filename = secure_filename(photo.filename)
            photo_filename = datetime.utcnow().strftime("%Y%m%d%H%M%S%f") + "_" + filename
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            photo.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_filename))
        d = Defect(
            station=station, feeder_area=feeder_area, equipment=equipment, defect=defect_text,
            severity=severity, recommended_action=request.form.get("recommended_action","").strip(),
            status=request.form.get("status","Open").strip(), responsible_person=request.form.get("responsible_person","").strip(),
            target_date=request.form.get("target_date","").strip(), remarks=request.form.get("remarks","").strip(),
            photo_filename=photo_filename
        )
        db.session.add(d); db.session.commit()
        flash("Defect submitted successfully.","success")
        return redirect(url_for("index"))
    return render_template("form.html", user=u, stations=STATIONS, severities=SEVERITIES, statuses=STATUSES, equipment=EQUIPMENT)

@app.route("/dashboard")
@login_required
@boss_required
def dashboard():
    defects = Defect.query.order_by(Defect.created_at.desc()).all()
    severity_counts = {s:0 for s in SEVERITIES}
    status_counts = {s:0 for s in STATUSES}
    station_counts, equipment_counts = {}, {}
    for d in defects:
        severity_counts[d.severity] = severity_counts.get(d.severity,0)+1
        status_counts[d.status] = status_counts.get(d.status,0)+1
        station_counts[d.station] = station_counts.get(d.station,0)+1
        equipment_counts[d.equipment] = equipment_counts.get(d.equipment,0)+1
    return render_template("dashboard.html",
        total=len(defects), severity_counts=severity_counts, status_counts=status_counts,
        top_stations=sorted(station_counts.items(), key=lambda x:x[1], reverse=True)[:10],
        top_equipment=sorted(equipment_counts.items(), key=lambda x:x[1], reverse=True)[:10],
        recent=defects[:10])

@app.route("/records")
@login_required
@boss_required
def records():
    q = request.args.get("q","").strip()
    severity = request.args.get("severity","").strip()
    status = request.args.get("status","").strip()
    station = request.args.get("station","").strip()
    query = Defect.query
    if q:
        query = query.filter(db.or_(Defect.defect.ilike(f"%{q}%"), Defect.equipment.ilike(f"%{q}%"), Defect.feeder_area.ilike(f"%{q}%"), Defect.remarks.ilike(f"%{q}%")))
    if severity: query = query.filter_by(severity=severity)
    if status: query = query.filter_by(status=status)
    if station: query = query.filter(Defect.station.ilike(f"%{station}%"))
    return render_template("records.html", defects=query.order_by(Defect.created_at.desc()).all(), severities=SEVERITIES, statuses=STATUSES)

@app.route("/defect/<int:defect_id>/update", methods=["POST"])
@login_required
@boss_required
def update_defect(defect_id):
    d = Defect.query.get_or_404(defect_id)
    d.status = request.form.get("status", d.status)
    d.responsible_person = request.form.get("responsible_person", d.responsible_person)
    d.completed_date = request.form.get("completed_date", d.completed_date)
    d.remarks = request.form.get("remarks", d.remarks)
    db.session.commit()
    flash("Defect updated.","success")
    return redirect(url_for("records"))

@app.route("/export.csv")
@login_required
@boss_required
def export_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Date","Station","Feeder/Area","Equipment","Defect","Severity","Recommended Action","Status","Responsible Person","Target Date","Completed Date","Remarks","Photo"])
    for d in Defect.query.order_by(Defect.created_at.desc()).all():
        writer.writerow([d.id,d.created_at.strftime("%Y-%m-%d %H:%M"),d.station,d.feeder_area,d.equipment,d.defect,d.severity,d.recommended_action,d.status,d.responsible_person,d.target_date,d.completed_date,d.remarks,d.photo_filename or ""])
    mem = io.BytesIO(output.getvalue().encode("utf-8")); mem.seek(0)
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="ecg_defect_report.csv")

if __name__ == "__main__":
    app.run(debug=True)
