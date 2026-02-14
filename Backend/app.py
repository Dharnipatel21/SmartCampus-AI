from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os, math
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'campus.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row) if row else None

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db(); c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reg_no TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            email TEXT, phone TEXT, department TEXT,
            year INTEGER, semester INTEGER, section TEXT,
            hostel TEXT,
            is_hosteler INTEGER DEFAULT 1,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
            email TEXT, department TEXT, designation TEXT,
            office_room TEXT, password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS faculty_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER, role_type TEXT,
            role_name TEXT, department TEXT
        );
        CREATE TABLE IF NOT EXISTS teacher_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER UNIQUE,
            current_status TEXT DEFAULT "In Office",
            location TEXT, available_from TEXT, available_to TEXT
        );
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, subject TEXT,
            total_classes INTEGER, attended_classes INTEGER, percentage REAL
        );
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, subject TEXT,
            internal_marks INTEGER, external_marks INTEGER,
            total_marks INTEGER, grade TEXT, credits INTEGER
        );
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, day TEXT, time_slot TEXT,
            subject TEXT, teacher_name TEXT, room TEXT
        );
        CREATE TABLE IF NOT EXISTS exam_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT, exam_date TEXT, time TEXT,
            hall TEXT, semester INTEGER, department TEXT
        );
        CREATE TABLE IF NOT EXISTS fees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, total_fee REAL, paid_amount REAL,
            pending_amount REAL, status TEXT, due_date TEXT
        );

        -- OUTPASS: 4-stage approval flow
        CREATE TABLE IF NOT EXISTS outpass_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, reason TEXT, destination TEXT,
            out_date TEXT, out_time TEXT,
            return_date TEXT, return_time TEXT,

            -- Stage tracking
            stage TEXT DEFAULT "Faculty Advisor",
            overall_status TEXT DEFAULT "Pending",

            -- Stage 1: Faculty Advisor
            faculty_status TEXT DEFAULT "Pending",
            faculty_approved_by TEXT,
            faculty_approved_at DATETIME,

            -- Stage 2: Hostel Coordinator
            hostel_coord_status TEXT DEFAULT "Waiting",
            hostel_coord_approved_by TEXT,
            hostel_coord_approved_at DATETIME,

            -- Stage 3: HOD
            hod_status TEXT DEFAULT "Waiting",
            hod_approved_by TEXT,
            hod_approved_at DATETIME,

            -- Stage 4: Hostel Warden
            warden_status TEXT DEFAULT "Waiting",
            warden_approved_by TEXT,
            warden_approved_at DATETIME,

            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS onduty_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, event_name TEXT, date TEXT,
            description TEXT, status TEXT DEFAULT "Pending",
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS helpdesk_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER, category TEXT, subject TEXT,
            description TEXT, status TEXT DEFAULT "Open",
            submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    if c.execute('SELECT COUNT(*) FROM students').fetchone()[0] == 0:
        c.executescript('''
            -- is_hosteler: 1=hosteler, 0=day scholar
            INSERT INTO students (reg_no,name,email,phone,department,year,semester,section,hostel,is_hosteler,password) VALUES
                ("RA2111003010001","Ravi Kumar","ravi@srmist.edu.in","9876543210","CSE",2,4,"A","Block A",1,"password123"),
                ("RA2111003010002","Priya Sharma","priya@srmist.edu.in","9876543211","CSE",2,4,"B","Block B",1,"password123"),
                ("RA2111003010003","Arjun Singh","arjun@srmist.edu.in","9876543212","ECE",3,5,"A","Day Scholar",0,"password123");

            INSERT INTO teachers (teacher_id,name,email,department,designation,office_room,password) VALUES
                ("T001","Dr. Rajesh Kumar","rajesh@srmist.edu.in","CSE","Head of Department","CSE-101","teacher123"),
                ("T002","Prof. Priya Sharma","psharm@srmist.edu.in","CSE","Professor","CSE-202","teacher123"),
                ("T003","Dr. Suresh Reddy","suresh@srmist.edu.in","CSE","Associate Professor","CSE-303","teacher123"),
                ("T004","Prof. Anita Desai","anita@srmist.edu.in","ECE","Professor","ECE-101","teacher123"),
                ("T005","Dr. Vikram Singh","vikram@srmist.edu.in","CSE","Professor","CSE-404","teacher123");

            INSERT INTO faculty_roles (teacher_id,role_type,role_name,department) VALUES
                (1,"HOD","Head of Department - CSE","CSE"),
                (2,"PLACEMENT","Placement Coordinator","CSE"),
                (3,"WARDEN","Hostel Warden - Block A","CSE"),
                (3,"HOSTEL_COORD","Hostel Coordinator","CSE"),
                (5,"HACKATHON","Hackathon Coordinator","CSE"),
                (2,"FACULTY_ADVISOR","Faculty Advisor","CSE");

            INSERT INTO teacher_status (teacher_id,current_status,location,available_from,available_to) VALUES
                (1,"In Office","CSE-101","09:00","17:00"),
                (2,"In Class","CSE-Lab 3","10:00","12:00"),
                (3,"Available","CSE-303","09:00","16:00"),
                (4,"In Meeting","ECE-101","11:00","13:00"),
                (5,"In Office","CSE-404","09:00","17:00");

            INSERT INTO attendance (student_id,subject,total_classes,attended_classes,percentage) VALUES
                (1,"Data Structures",40,35,87.5),
                (1,"Database Systems",38,28,73.7),
                (1,"Computer Networks",42,30,71.4),
                (1,"Operating Systems",40,36,90.0),
                (1,"Software Engineering",36,32,88.9);

            INSERT INTO marks (student_id,subject,internal_marks,external_marks,total_marks,grade,credits) VALUES
                (1,"Data Structures",19,76,95,"A+",4),
                (1,"Database Systems",17,68,85,"A",3),
                (1,"Computer Networks",18,72,90,"A+",3),
                (1,"Operating Systems",20,78,98,"A+",4),
                (1,"Software Engineering",16,65,81,"A",3);

            INSERT INTO timetable (student_id,day,time_slot,subject,teacher_name,room) VALUES
                (1,"MON","8.00-8.50","Engineering Graphics","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"MON","8.50-9.40","Engineering Graphics","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"MON","9.50-10.40","Engineering Graphics","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"MON","10.40-11.30","Chemistry","Prof. Priya Sharma","ADMIN 505"),
                (1,"MON","12.20-1.10","POE","Dr. Suresh Reddy","ADMIN 505"),
                (1,"TUE","8.00-8.50","CE","Prof. Anita Desai","ADMIN 505"),
                (1,"TUE","8.50-9.40","CLA","Dr. Vikram Singh","ADMIN 505"),
                (1,"TUE","9.50-10.40","Chemistry","Prof. Priya Sharma","ADMIN 505"),
                (1,"TUE","10.40-11.30","Chemistry","Prof. Priya Sharma","ADMIN 505"),
                (1,"TUE","12.20-1.10","PSP","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"TUE","1.10-2.00","PSP","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"WED","8.00-8.50","CLA","Dr. Vikram Singh","ADMIN 505"),
                (1,"WED","8.50-9.40","CB","Prof. Anita Desai","ADMIN 505"),
                (1,"WED","9.50-10.40","Chemistry","Prof. Priya Sharma","ADMIN 505"),
                (1,"WED","10.40-11.30","POE","Dr. Suresh Reddy","ADMIN 505"),
                (1,"WED","12.20-1.10","PPS","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"WED","1.10-2.00","EVS","Prof. Anita Desai","ADMIN 505"),
                (1,"THU","8.00-8.50","PPS","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"THU","8.50-9.40","CE","Prof. Anita Desai","ADMIN 505"),
                (1,"THU","9.50-10.40","PPS","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"THU","10.40-11.30","PPS","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"THU","12.20-1.10","CLA","Dr. Vikram Singh","ADMIN 505"),
                (1,"THU","1.10-2.00","EG","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"FRI","8.00-8.50","POE","Dr. Suresh Reddy","ADMIN 505"),
                (1,"FRI","8.50-9.40","PPS","Dr. Rajesh Kumar","ADMIN 505"),
                (1,"FRI","9.50-10.40","Chemistry","Prof. Priya Sharma","ADMIN 505"),
                (1,"FRI","10.40-11.30","CB","Prof. Anita Desai","ADMIN 505"),
                (1,"FRI","12.20-1.10","CE","Prof. Anita Desai","ADMIN 505"),
                (1,"FRI","1.10-2.00","CLA","Dr. Vikram Singh","ADMIN 505");

            INSERT INTO exam_schedule (subject,exam_date,time,hall,semester,department) VALUES
                ("Data Structures","2024-11-15","09:00 AM","Hall A",4,"CSE"),
                ("Database Systems","2024-11-17","09:00 AM","Hall B",4,"CSE"),
                ("Computer Networks","2024-11-19","09:00 AM","Hall A",4,"CSE"),
                ("Operating Systems","2024-11-21","02:00 PM","Hall C",4,"CSE"),
                ("Software Engineering","2024-11-23","09:00 AM","Hall B",4,"CSE");

            INSERT INTO fees (student_id,total_fee,paid_amount,pending_amount,status,due_date) VALUES
                (1,95000,70000,25000,"Partial","2024-11-30"),
                (2,95000,95000,0,"Paid","2024-11-30"),
                (3,95000,0,95000,"Pending","2024-11-30");
        ''')
    conn.commit(); conn.close()

    # Auto-import students and teachers from CSV if available
    _auto_import()
    print("Database ready!")


def _auto_import():
    """Auto-imports students.csv and teachers.csv, fills missing data for ALL students."""
    import csv as _csv, random as _r

    base         = os.path.dirname(__file__)
    students_csv = os.path.join(base, 'students.csv')
    teachers_csv = os.path.join(base, 'teachers.csv')

    SUBJECTS = {
        "CSE":  ["Data Structures","Database Systems","Computer Networks","Operating Systems","Software Engineering"],
        "ECE":  ["Circuit Theory","Digital Electronics","Signals & Systems","Microprocessors","Communication Systems"],
        "MECH": ["Engineering Mechanics","Thermodynamics","Fluid Mechanics","Manufacturing Processes","Machine Design"],
        "CIVIL":["Surveying","Structural Analysis","Concrete Technology","Geotechnical Engineering","Fluid Mechanics"],
        "EEE":  ["Circuit Analysis","Electrical Machines","Power Systems","Control Systems","Power Electronics"],
        "IT":   ["Web Technologies","Database Management","Computer Networks","Software Testing","Cloud Computing"],
        "AIDS": ["Machine Learning","Data Analytics","Deep Learning","Natural Language Processing","Computer Vision"],
        "CSBS": ["Business Analytics","Data Science","Blockchain","IoT","Cyber Security"],
    }
    GRADE_MARKS = {
        "A+": (22,80,25,100), "A":  (18,68,24,85),
        "B+": (16,56,22,75),  "B":  (14,45,20,65), "C": (12,35,18,55),
    }
    GRADES   = ["A+","A","B+","B","C"]
    DAYS     = ["MON","TUE","WED","THU","FRI"]
    SLOTS    = ["8.00-8.50","8.50-9.40","9.50-10.40","10.40-11.30","12.20-1.10","1.10-2.00"]
    TEACHERS = ["Dr. Rajesh Kumar","Prof. Priya Sharma","Dr. Suresh Reddy","Prof. Anita Desai","Dr. Vikram Singh"]

    conn = get_db()
    c    = conn.cursor()

    # ── Step 1: Insert any students from CSV not yet in DB ─────────────
    if os.path.exists(students_csv):
        with open(students_csv, newline='', encoding='utf-8') as f:
            for row in _csv.DictReader(f):
                reg = row['reg_no'].strip()
                if not c.execute('SELECT id FROM students WHERE reg_no=?',(reg,)).fetchone():
                    try:
                        c.execute(
                            'INSERT INTO students (reg_no,name,email,phone,department,year,semester,section,hostel,is_hosteler,password) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                            (reg, row['name'].strip(), row['email'].strip(), row['phone'].strip(),
                             row['department'].strip(), int(row['year']), int(row['semester']),
                             row['section'].strip(), row['hostel'].strip(),
                             int(row['is_hosteler']), row['password'].strip())
                        )
                    except Exception:
                        pass
        conn.commit()

    # ── Step 2: Fill missing attendance/marks/fees/timetable for ALL students ──
    all_students = c.execute('SELECT id, department FROM students').fetchall()
    filled = 0
    for (sid, dept) in all_students:
        dept     = dept or 'CSE'
        subjects = SUBJECTS.get(dept, SUBJECTS['CSE'])

        if c.execute('SELECT COUNT(*) FROM attendance WHERE student_id=?',(sid,)).fetchone()[0] == 0:
            for subj in subjects:
                total    = _r.choice([38,40,42,44])
                pct_val  = _r.choices([_r.uniform(60,74),_r.uniform(75,95)],weights=[25,75])[0]
                attended = max(0, min(int(pct_val/100*total), total))
                pct      = round(attended/total*100, 1)
                c.execute('INSERT INTO attendance (student_id,subject,total_classes,attended_classes,percentage) VALUES (?,?,?,?,?)',
                          (sid,subj,total,attended,pct))
            filled += 1

        if c.execute('SELECT COUNT(*) FROM marks WHERE student_id=?',(sid,)).fetchone()[0] == 0:
            for subj in subjects:
                grade = _r.choices(GRADES, weights=[20,30,25,15,10])[0]
                i_min,e_min,i_max,e_max = GRADE_MARKS[grade]
                internal = _r.randint(i_min, i_max)
                external = _r.randint(e_min, e_max)
                credits  = _r.choice([3,4])
                c.execute('INSERT INTO marks (student_id,subject,internal_marks,external_marks,total_marks,grade,credits) VALUES (?,?,?,?,?,?,?)',
                          (sid,subj,internal,external,internal+external,grade,credits))

        if c.execute('SELECT COUNT(*) FROM fees WHERE student_id=?',(sid,)).fetchone()[0] == 0:
            total_fee = _r.choice([85000,90000,95000,100000])
            paid      = _r.randint(0, total_fee)
            pending   = total_fee - paid
            status    = "Paid" if pending==0 else ("Partial" if paid>0 else "Pending")
            c.execute('INSERT INTO fees (student_id,total_fee,paid_amount,pending_amount,status,due_date) VALUES (?,?,?,?,?,?)',
                      (sid,total_fee,paid,pending,status,"2024-11-30"))

        if c.execute('SELECT COUNT(*) FROM timetable WHERE student_id=?',(sid,)).fetchone()[0] == 0:
            for day in DAYS:
                for slot in _r.sample(SLOTS, k=_r.randint(3,5)):
                    c.execute('INSERT INTO timetable (student_id,day,time_slot,subject,teacher_name,room) VALUES (?,?,?,?,?,?)',
                              (sid,day,slot,_r.choice(subjects),_r.choice(TEACHERS),
                               f"{dept}-{_r.randint(1,5)}0{_r.randint(1,9)}"))

    if filled > 0:
        print(f"  Filled data for {filled} students!")
    conn.commit()

    # ── Step 3: Import teachers from CSV ──────────────────────────────
    if os.path.exists(teachers_csv):
        added_t = 0
        with open(teachers_csv, newline='', encoding='utf-8') as f:
            for row in _csv.DictReader(f):
                tid = row['teacher_id'].strip()
                if c.execute('SELECT id FROM teachers WHERE teacher_id=?',(tid,)).fetchone():
                    continue
                c.execute('INSERT INTO teachers (teacher_id,name,email,department,designation,office_room,password) VALUES (?,?,?,?,?,?,?)',
                          (tid,row['name'].strip(),row['email'].strip(),row['department'].strip(),
                           row['designation'].strip(),row['office_room'].strip(),row['password'].strip()))
                db_id = c.lastrowid
                if row.get('role_type','').strip():
                    c.execute('INSERT INTO faculty_roles (teacher_id,role_type,role_name,department) VALUES (?,?,?,?)',
                              (db_id,row['role_type'].strip(),row['role_name'].strip(),row['department'].strip()))
                c.execute('INSERT OR IGNORE INTO teacher_status (teacher_id,current_status,location,available_from,available_to) VALUES (?,?,?,?,?)',
                          (db_id,"Available",row['office_room'].strip(),"9:00 AM","5:00 PM"))
                added_t += 1
        if added_t > 0:
            print(f"  Auto-imported {added_t} teachers!")
        conn.commit()

    conn.close()

# ─── ROOT ─────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return jsonify({"message":"SmartCampus AI Running!","status":"ok"})

# ─── STUDENT LOGIN ─────────────────────────────────────────────────────
@app.route('/api/student/login', methods=['POST'])
def student_login():
    d = request.json or {}
    conn = get_db()
    s = conn.execute('SELECT * FROM students WHERE reg_no=? AND password=?',
                     (d.get('reg_no','').strip(), d.get('password','').strip())).fetchone()
    conn.close()
    if s:
        s = dict(s)
        return jsonify({'success':True,'student':{
            'id':s['id'],'name':s['name'],'reg_no':s['reg_no'],
            'department':s['department'],'year':s['year'],
            'semester':s['semester'],'section':s['section'],
            'email':s['email'],'hostel':s['hostel'],
            'is_hosteler': s['is_hosteler']   # <-- sent to frontend
        }})
    return jsonify({'success':False,'message':'Invalid registration number or password'}), 401

# ─── TEACHER LOGIN ─────────────────────────────────────────────────────
@app.route('/api/teacher/login', methods=['POST'])
def teacher_login():
    d = request.json or {}
    conn    = get_db()
    teacher = conn.execute('SELECT * FROM teachers WHERE teacher_id=? AND password=?',
                           (d.get('teacher_id','').strip(), d.get('password','').strip())).fetchone()
    roles  = []
    status = None
    if teacher:
        roles  = [dict(r) for r in conn.execute('SELECT * FROM faculty_roles WHERE teacher_id=?',(teacher['id'],)).fetchall()]
        status = conn.execute('SELECT * FROM teacher_status WHERE teacher_id=?',(teacher['id'],)).fetchone()
    conn.close()
    if teacher:
        t = dict(teacher)
        return jsonify({'success':True,
            'teacher':{'id':t['id'],'teacher_id':t['teacher_id'],'name':t['name'],
                       'department':t['department'],'designation':t['designation'],
                       'office_room':t['office_room'],'email':t['email']},
            'roles':roles,'status':dict(status) if status else {}})
    return jsonify({'success':False,'message':'Invalid Teacher ID or password'}), 401

# ─── DASHBOARD SUMMARY (fees removed) ─────────────────────────────────
@app.route('/api/dashboard/summary/<int:student_id>')
def dashboard_summary(student_id):
    conn    = get_db()
    student = row_to_dict(conn.execute('SELECT * FROM students WHERE id=?',(student_id,)).fetchone())
    att     = [dict(r) for r in conn.execute('SELECT * FROM attendance WHERE student_id=?',(student_id,)).fetchall()]
    marks   = [dict(r) for r in conn.execute('SELECT * FROM marks WHERE student_id=?',(student_id,)).fetchall()]
    conn.close()
    if not student: return jsonify({'error':'Not found'}), 404
    gp   = {'A+':10,'A':9,'B+':8,'B':7,'C':6}
    tc   = sum(m['credits'] for m in marks)
    cgpa = round(sum(gp.get(m['grade'],7)*m['credits'] for m in marks)/tc,2) if tc else 0
    low  = [a for a in att if a['percentage'] < 75]
    return jsonify({'student':student,'total_subjects':len(att),'cgpa':cgpa,
                    'low_attendance_count':len(low),'low_attendance_subjects':low})
    # NOTE: fees intentionally removed from summary

# ─── ATTENDANCE ────────────────────────────────────────────────────────
@app.route('/api/attendance/<int:student_id>')
def get_attendance(student_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute('SELECT * FROM attendance WHERE student_id=?',(student_id,)).fetchall()]
    conn.close()
    for r in rows:
        T,A = r['total_classes'],r['attended_classes']
        r['classes_needed'] = max(0,int((0.75*T-A)/0.25)+1) if r['percentage']<75 else 0
    return jsonify(rows)

@app.route('/api/marks/<int:student_id>')
def get_marks(student_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute('SELECT * FROM marks WHERE student_id=?',(student_id,)).fetchall()]
    conn.close(); return jsonify(rows)

@app.route('/api/timetable/<int:student_id>')
def get_timetable(student_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute(
        'SELECT * FROM timetable WHERE student_id=? ORDER BY day,time_slot',(student_id,)).fetchall()]
    conn.close(); return jsonify(rows)

@app.route('/api/exam-schedule/<int:semester>')
def get_exam_schedule(semester):
    conn = get_db()
    rows = [dict(r) for r in conn.execute(
        'SELECT * FROM exam_schedule WHERE semester=? ORDER BY exam_date',(semester,)).fetchall()]
    conn.close(); return jsonify(rows)

@app.route('/api/fees/<int:student_id>')
def get_fees(student_id):
    conn = get_db()
    row  = row_to_dict(conn.execute('SELECT * FROM fees WHERE student_id=?',(student_id,)).fetchone())
    conn.close(); return jsonify(row or {})

# ─── OUTPASS — 4-STAGE FLOW ────────────────────────────────────────────
# Stage flow: Faculty Advisor → Hostel Coordinator → HOD → Warden
# Each stage can Approve (moves to next) or Reject (ends flow)

@app.route('/api/outpass/submit', methods=['POST'])
def submit_outpass():
    d = request.json or {}
    conn = get_db()
    # Check if student is hosteler
    student = row_to_dict(conn.execute('SELECT is_hosteler FROM students WHERE id=?',(d.get('student_id'),)).fetchone())
    if not student or not student.get('is_hosteler'):
        conn.close()
        return jsonify({'success':False,'message':'Non-hostelers cannot apply for outpass.'}), 400
    conn.execute('''INSERT INTO outpass_requests
        (student_id,reason,destination,out_date,out_time,return_date,return_time,
         stage,overall_status,faculty_status,hostel_coord_status,hod_status,warden_status)
        VALUES (?,?,?,?,?,?,?,"Faculty Advisor","Pending","Pending","Waiting","Waiting","Waiting")''',
        (d.get('student_id'),d.get('reason'),d.get('destination'),
         d.get('out_date'),d.get('out_time'),d.get('return_date'),d.get('return_time')))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'Outpass submitted! Waiting for Faculty Advisor approval.'})


@app.route('/api/outpass/student/<int:student_id>')
def get_student_outpasses(student_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute(
        'SELECT * FROM outpass_requests WHERE student_id=? ORDER BY submitted_at DESC',(student_id,)).fetchall()]
    conn.close()
    # Build a readable approval trail for each request
    for r in rows:
        trail = []
        if r['faculty_status'] == 'Approved':
            trail.append(f"✅ Faculty Advisor approved ({r['faculty_approved_by'] or 'Faculty'})")
        elif r['faculty_status'] == 'Rejected':
            trail.append(f"❌ Faculty Advisor rejected ({r['faculty_approved_by'] or 'Faculty'})")
        else:
            trail.append(f"⏳ Waiting for Faculty Advisor")

        if r['hostel_coord_status'] == 'Approved':
            trail.append(f"✅ Hostel Coordinator approved ({r['hostel_coord_approved_by'] or 'Coordinator'})")
        elif r['hostel_coord_status'] == 'Rejected':
            trail.append(f"❌ Hostel Coordinator rejected")
        elif r['hostel_coord_status'] == 'Waiting':
            trail.append(f"⏳ Waiting for Hostel Coordinator")

        if r['hod_status'] == 'Approved':
            trail.append(f"✅ HOD approved ({r['hod_approved_by'] or 'HOD'})")
        elif r['hod_status'] == 'Rejected':
            trail.append(f"❌ HOD rejected")
        elif r['hod_status'] == 'Waiting':
            trail.append(f"⏳ Waiting for HOD")

        if r['warden_status'] == 'Approved':
            trail.append(f"✅ Warden approved ({r['warden_approved_by'] or 'Warden'}) — FINAL APPROVED")
        elif r['warden_status'] == 'Rejected':
            trail.append(f"❌ Warden rejected")
        elif r['warden_status'] == 'Waiting':
            trail.append(f"⏳ Waiting for Warden")

        r['approval_trail'] = trail
        r['current_stage']  = r['stage']
    return jsonify(rows)


# Teacher sees outpass pending for their role + student attendance
@app.route('/api/teacher/outpass/pending')
def pending_outpass():
    conn = get_db()
    # Get all pending at each stage, joined with student attendance
    rows = [dict(r) for r in conn.execute('''
        SELECT o.*, s.name, s.reg_no, s.department, s.year, s.section
        FROM outpass_requests o JOIN students s ON o.student_id=s.id
        WHERE o.overall_status="Pending"
        ORDER BY o.submitted_at DESC
    ''').fetchall()]

    # Attach student attendance to each row so teacher can decide
    for r in rows:
        att = [dict(a) for a in conn.execute(
            'SELECT subject,percentage FROM attendance WHERE student_id=?',(r['student_id'],)).fetchall()]
        low = [a for a in att if a['percentage'] < 75]
        r['attendance_summary'] = att
        r['low_attendance']     = low
        r['can_approve']        = len(low) == 0  # suggestion only, teacher decides

    conn.close()
    return jsonify(rows)


def _approve_stage(oid, stage_col, next_stage_col, next_stage_name, approver_name, final=False):
    """Helper: advance one stage in the 4-stage outpass flow."""
    conn = get_db()
    if final:
        conn.execute(f'''UPDATE outpass_requests SET
            {stage_col}_status="Approved", {stage_col}_approved_by=?,
            {stage_col}_approved_at=CURRENT_TIMESTAMP,
            overall_status="Approved", stage="Completed"
            WHERE id=?''', (approver_name, oid))
    else:
        conn.execute(f'''UPDATE outpass_requests SET
            {stage_col}_status="Approved", {stage_col}_approved_by=?,
            {stage_col}_approved_at=CURRENT_TIMESTAMP,
            {next_stage_col}_status="Pending",
            stage=?
            WHERE id=?''', (approver_name, next_stage_name, oid))
    conn.commit(); conn.close()


def _reject_stage(oid, stage_col, approver_name):
    conn = get_db()
    conn.execute(f'''UPDATE outpass_requests SET
        {stage_col}_status="Rejected", {stage_col}_approved_by=?,
        {stage_col}_approved_at=CURRENT_TIMESTAMP,
        overall_status="Rejected"
        WHERE id=?''', (approver_name, oid))
    conn.commit(); conn.close()


# Stage 1: Faculty Advisor
@app.route('/api/teacher/outpass/faculty/approve/<int:oid>', methods=['POST'])
def faculty_approve_outpass(oid):
    d = request.json or {}
    _approve_stage(oid,'faculty','hostel_coord','Hostel Coordinator',d.get('teacher_name','Faculty'))
    return jsonify({'success':True,'message':'Approved! Moved to Hostel Coordinator.'})

@app.route('/api/teacher/outpass/faculty/reject/<int:oid>', methods=['POST'])
def faculty_reject_outpass(oid):
    d = request.json or {}
    _reject_stage(oid,'faculty',d.get('teacher_name','Faculty'))
    return jsonify({'success':True,'message':'Outpass rejected at Faculty Advisor stage.'})


# Stage 2: Hostel Coordinator
@app.route('/api/teacher/outpass/hostel/approve/<int:oid>', methods=['POST'])
def hostel_approve_outpass(oid):
    d = request.json or {}
    _approve_stage(oid,'hostel_coord','hod','HOD',d.get('teacher_name','Hostel Coordinator'))
    return jsonify({'success':True,'message':'Approved! Moved to HOD.'})

@app.route('/api/teacher/outpass/hostel/reject/<int:oid>', methods=['POST'])
def hostel_reject_outpass(oid):
    d = request.json or {}
    _reject_stage(oid,'hostel_coord',d.get('teacher_name','Hostel Coordinator'))
    return jsonify({'success':True,'message':'Outpass rejected at Hostel Coordinator stage.'})


# Stage 3: HOD
@app.route('/api/teacher/outpass/hod/approve/<int:oid>', methods=['POST'])
def hod_approve_outpass(oid):
    d = request.json or {}
    _approve_stage(oid,'hod','warden','Hostel Warden',d.get('teacher_name','HOD'))
    return jsonify({'success':True,'message':'Approved! Moved to Hostel Warden.'})

@app.route('/api/teacher/outpass/hod/reject/<int:oid>', methods=['POST'])
def hod_reject_outpass(oid):
    d = request.json or {}
    _reject_stage(oid,'hod',d.get('teacher_name','HOD'))
    return jsonify({'success':True,'message':'Outpass rejected at HOD stage.'})


# Stage 4: Warden (Final)
@app.route('/api/teacher/outpass/warden/approve/<int:oid>', methods=['POST'])
def warden_approve_outpass(oid):
    d = request.json or {}
    _approve_stage(oid,'warden',None,None,d.get('teacher_name','Warden'),final=True)
    return jsonify({'success':True,'message':'FINAL APPROVED by Warden! Outpass granted.'})

@app.route('/api/teacher/outpass/warden/reject/<int:oid>', methods=['POST'])
def warden_reject_outpass(oid):
    d = request.json or {}
    _reject_stage(oid,'warden',d.get('teacher_name','Warden'))
    return jsonify({'success':True,'message':'Outpass rejected at Warden stage.'})


# Legacy approve/reject (kept for backward compat)
@app.route('/api/teacher/outpass/approve/<int:oid>', methods=['POST'])
def approve_outpass(oid):
    d = request.json or {}
    _approve_stage(oid,'faculty','hostel_coord','Hostel Coordinator',d.get('teacher_name','Faculty'))
    return jsonify({'success':True})

@app.route('/api/teacher/outpass/reject/<int:oid>', methods=['POST'])
def reject_outpass(oid):
    d = request.json or {}
    _reject_stage(oid,'faculty',d.get('teacher_name','Faculty'))
    return jsonify({'success':True})


# ─── ON-DUTY ───────────────────────────────────────────────────────────
@app.route('/api/onduty/submit', methods=['POST'])
def submit_onduty():
    d = request.json or {}
    conn = get_db()
    conn.execute('INSERT INTO onduty_requests (student_id,event_name,date,description) VALUES (?,?,?,?)',
                 (d.get('student_id'),d.get('event_name'),d.get('date'),d.get('description','')))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'On-Duty request submitted!'})

@app.route('/api/onduty/student/<int:student_id>')
def get_student_onduty(student_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute(
        'SELECT * FROM onduty_requests WHERE student_id=? ORDER BY submitted_at DESC',(student_id,)).fetchall()]
    conn.close(); return jsonify(rows)

@app.route('/api/teacher/onduty/pending')
def pending_onduty():
    conn = get_db()
    rows = [dict(r) for r in conn.execute('''
        SELECT o.*,s.name,s.reg_no FROM onduty_requests o
        JOIN students s ON o.student_id=s.id
        WHERE o.status="Pending" ORDER BY o.submitted_at DESC
    ''').fetchall()]
    conn.close(); return jsonify(rows)

@app.route('/api/teacher/onduty/approve/<int:oid>', methods=['POST'])
def approve_onduty(oid):
    conn = get_db()
    conn.execute('UPDATE onduty_requests SET status="Approved" WHERE id=?',(oid,))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'On-Duty approved!'})

# ─── HELP DESK ─────────────────────────────────────────────────────────
@app.route('/api/helpdesk/submit', methods=['POST'])
def submit_ticket():
    d = request.json or {}
    conn = get_db()
    conn.execute('INSERT INTO helpdesk_tickets (student_id,category,subject,description) VALUES (?,?,?,?)',
                 (d.get('student_id'),d.get('category'),d.get('subject'),d.get('description')))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'Ticket raised successfully!'})

@app.route('/api/helpdesk/student/<int:student_id>')
def get_student_tickets(student_id):
    conn = get_db()
    rows = [dict(r) for r in conn.execute(
        'SELECT * FROM helpdesk_tickets WHERE student_id=? ORDER BY submitted_at DESC',(student_id,)).fetchall()]
    conn.close(); return jsonify(rows)

@app.route('/api/teacher/helpdesk/all')
def all_tickets():
    conn = get_db()
    rows = [dict(r) for r in conn.execute('''
        SELECT h.*,s.name,s.reg_no FROM helpdesk_tickets h
        JOIN students s ON h.student_id=s.id ORDER BY h.submitted_at DESC
    ''').fetchall()]
    conn.close(); return jsonify(rows)

# ─── TEACHER STATUS ────────────────────────────────────────────────────
@app.route('/api/teacher/status/update', methods=['POST'])
def update_teacher_status():
    d = request.json or {}
    conn = get_db()
    conn.execute('''INSERT INTO teacher_status (teacher_id,current_status,location,available_from,available_to)
        VALUES (?,?,?,?,?) ON CONFLICT(teacher_id) DO UPDATE SET
        current_status=excluded.current_status, location=excluded.location,
        available_from=excluded.available_from, available_to=excluded.available_to''',
        (d.get('teacher_id'),d.get('status','In Office'),d.get('location',''),
         d.get('available_from',''),d.get('available_to','')))
    conn.commit(); conn.close()
    return jsonify({'success':True,'message':'Status updated!'})

@app.route('/api/teacher/find/<teacher_name>')
def find_teacher(teacher_name):
    conn     = get_db()
    teachers = [dict(r) for r in conn.execute(
        "SELECT * FROM teachers WHERE LOWER(name) LIKE ?",(f'%{teacher_name.lower()}%',)).fetchall()]
    result = []
    for t in teachers:
        st    = row_to_dict(conn.execute('SELECT * FROM teacher_status WHERE teacher_id=?',(t['id'],)).fetchone())
        roles = [dict(r) for r in conn.execute('SELECT * FROM faculty_roles WHERE teacher_id=?',(t['id'],)).fetchall()]
        result.append({**t,'status':st or {},'roles':roles})
    conn.close(); return jsonify(result)

@app.route('/api/faculty/roles')
def all_faculty_roles():
    conn = get_db()
    rows = [dict(r) for r in conn.execute('''
        SELECT fr.*,t.name,t.department,t.office_room,
               ts.current_status,ts.location,ts.available_from,ts.available_to
        FROM faculty_roles fr JOIN teachers t ON fr.teacher_id=t.id
        LEFT JOIN teacher_status ts ON t.id=ts.teacher_id
    ''').fetchall()]
    conn.close(); return jsonify(rows)

# ─── CHATBOT — FULLY UPGRADED ──────────────────────────────────────────


def build_full_student_context(student_id):
    """Pull ALL student data from DB and format it as a readable context string."""
    conn = get_db()
    try:
        student = row_to_dict(conn.execute('SELECT * FROM students WHERE id=?',(student_id,)).fetchone())
        att     = [dict(r) for r in conn.execute('SELECT * FROM attendance WHERE student_id=?',(student_id,)).fetchall()]
        marks   = [dict(r) for r in conn.execute('SELECT * FROM marks WHERE student_id=?',(student_id,)).fetchall()]
        fees    = row_to_dict(conn.execute('SELECT * FROM fees WHERE student_id=?',(student_id,)).fetchone())
        tt      = [dict(r) for r in conn.execute('SELECT * FROM timetable WHERE student_id=? ORDER BY day,time_slot',(student_id,)).fetchall()]
        exams   = [dict(r) for r in conn.execute('SELECT * FROM exam_schedule WHERE semester=?',(student.get('semester',4),)).fetchall()]
        outpass = [dict(r) for r in conn.execute('SELECT * FROM outpass_requests WHERE student_id=? ORDER BY submitted_at DESC LIMIT 5',(student_id,)).fetchall()]
        teachers = [dict(r) for r in conn.execute('''
            SELECT t.name,t.designation,t.office_room,ts.current_status,ts.location,
                   ts.available_from,ts.available_to,fr.role_name
            FROM teachers t
            LEFT JOIN teacher_status ts ON t.id=ts.teacher_id
            LEFT JOIN faculty_roles fr ON t.id=fr.teacher_id
        ''').fetchall()]
    finally:
        conn.close()

    if not student:
        return ""

    # ── Calculate CGPA ──────────────────────────────────────────────
    gp = {'A+':10,'A':9,'B+':8,'B':7,'C':6}
    tc = sum(m['credits'] for m in marks)
    cgpa = round(sum(gp.get(m['grade'],7)*m['credits'] for m in marks)/tc,2) if tc else 0

    # ── Build context string ─────────────────────────────────────────
    ctx = f"""
=== STUDENT PROFILE ===
Name       : {student['name']}
Reg No     : {student['reg_no']}
Department : {student['department']}
Year/Sem   : Year {student['year']}, Semester {student['semester']}
Section    : {student['section']}
Hostel     : {student['hostel']} ({'Hosteler' if student.get('is_hosteler') else 'Day Scholar'})
CGPA       : {cgpa}

=== ATTENDANCE (out of 100%) ===
"""
    low_subjects = []
    for a in att:
        T,A,pct = a['total_classes'],a['attended_classes'],a['percentage']
        needed = max(0,int((0.75*T-A)/0.25)+1) if pct<75 else 0
        status = "⚠️ BELOW 75%" if pct<75 else "✅ Safe"
        ctx += f"  {a['subject']}: {pct}% ({A}/{T} classes) {status}"
        if needed: ctx += f" — needs {needed} more classes"
        ctx += "\n"
        if pct<75: low_subjects.append(a['subject'])

    if low_subjects:
        ctx += f"\n  *** DETENTION RISK in: {', '.join(low_subjects)} ***\n"

    ctx += "\n=== MARKS & GRADES ===\n"
    for m in marks:
        ctx += f"  {m['subject']}: {m['total_marks']}/100, Grade {m['grade']}, {m['credits']} credits\n"
    ctx += f"  Overall CGPA: {cgpa}\n"

    if fees:
        ctx += f"""
=== FEES ===
  Total: Rs.{fees['total_fee']:,.0f}
  Paid : Rs.{fees['paid_amount']:,.0f}
  Due  : Rs.{fees['pending_amount']:,.0f}
  Status: {fees['status']} | Due date: {fees['due_date']}
"""

    if tt:
        ctx += "\n=== TODAY'S TIMETABLE (sample) ===\n"
        for t in tt[:6]:
            ctx += f"  {t['day']} {t['time_slot']}: {t['subject']} ({t['teacher_name']}) Room {t['room']}\n"

    if exams:
        ctx += "\n=== UPCOMING EXAMS ===\n"
        for e in exams[:5]:
            ctx += f"  {e['subject']}: {e['exam_date']} at {e['time']}, Hall {e['hall']}\n"

    if outpass:
        ctx += "\n=== RECENT OUTPASS REQUESTS ===\n"
        for o in outpass[:3]:
            ctx += f"  {o['reason']} → {o['destination']} | Status: {o['overall_status']} | Stage: {o['stage']}\n"

    # Deduplicate teachers
    seen = set()
    ctx += "\n=== FACULTY / TEACHERS ===\n"
    for t in teachers:
        if t['name'] not in seen:
            seen.add(t['name'])
            loc = t['location'] or t['office_room'] or 'Unknown'
            ctx += f"  {t['name']} ({t['designation'] or ''}) — {t['current_status'] or 'Unknown'} at {loc}"
            if t['role_name']: ctx += f" [{t['role_name']}]"
            ctx += "\n"

    return ctx


SYSTEM_PROMPT = """You are SmartCampus AI, an intelligent assistant for SRM University students.

You have access to the student's COMPLETE real-time data including their attendance, 
marks, fees, timetable, exam schedule, outpass history, and faculty information.

CAMPUS RULES YOU KNOW:
- Minimum attendance: 75% in every subject. Below = DETAINED (cannot write exams)
- Outpass approval: 4 stages → Faculty Advisor → Hostel Coordinator → HOD → Hostel Warden
- Hall ticket: Available 1 week before exams. Mandatory to carry on exam day.
- Grading: A+=10, A=9, B+=8, B=7, C=6 grade points
- Fees must be paid before due date. Fee receipt needed for exam registration.
- Hostel mess: Breakfast 7-9AM, Lunch 12-2PM, Dinner 7-9PM
- On-duty attendance: Approved events count as present

HOW TO RESPOND:
- Answer ANY question the student asks — even if phrased unusually or informally
- Use the student's ACTUAL DATA to give personalised answers
- If they ask "am I safe?" → check their attendance numbers
- If they ask "how am I doing?" → analyse their CGPA and attendance
- If they ask about a teacher → give their location and status
- Be friendly, clear, and specific. Use numbers from their data.
- Keep answers under 5-6 sentences unless a detailed breakdown is needed.
- If asked in Tamil or Hindi, respond in that language.
"""

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    data       = request.json or {}
    message    = data.get('message','').strip()
    student_id = data.get('student_id')
    history    = data.get('history', [])   # multi-turn conversation history

    if not message:
        return jsonify({'response': 'Please type a message.'})

    api_key = os.getenv('OPENAI_API_KEY','').strip()


    # DEBUG — remove after fixing
    print(f'[CHATBOT DEBUG] api_key found: {bool(api_key)}, starts: {api_key[:15] if api_key else "EMPTY"}')
    print(f'[CHATBOT DEBUG] message: {message[:40]}')

    # OpenAI GPT PATH (real AI)
    if api_key and api_key != 'your-key-here':
        print("  -> Trying OpenAI GPT...")
        try:
            import urllib.request as _ureq
            import urllib.error   as _uerr
            import json as _json

            context = build_full_student_context(student_id) if student_id else ""
            system  = SYSTEM_PROMPT
            if context:
                system += f"\n\n=== CURRENT STUDENT DATA ===\n{context}"

            messages = [{"role": "system", "content": system}]
            for h in history[-6:]:
                if h.get('role') in ('user', 'assistant'):
                    messages.append({'role': h['role'], 'content': h['content']})
            messages.append({'role': 'user', 'content': message})

            payload = _json.dumps({
                "model":       "gpt-3.5-turbo",
                "messages":    messages,
                "max_tokens":  500,
                "temperature": 0.7
            }).encode('utf-8')

            req = _ureq.Request(
                "https://api.openai.com/v1/chat/completions",
                data    = payload,
                headers = {
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
            )

            # Catch HTTP errors explicitly so we can read OpenAI's error message
            try:
                with _ureq.urlopen(req, timeout=20) as r:
                    resp = _json.loads(r.read().decode())
            except _uerr.HTTPError as http_err:
                err_body = http_err.read().decode()
                print(f"[OPENAI HTTP {http_err.code}]: {err_body[:300]}")
                raise Exception(f"OpenAI HTTP {http_err.code}: {err_body[:200]}")

            reply = resp['choices'][0]['message']['content']
            print(f"  -> GPT replied OK ({len(reply)} chars)")
            return jsonify({'response': reply, 'source': 'openai_gpt'})

        except Exception as e:
            import traceback
            print(f"[OPENAI ERROR] {type(e).__name__}: {e}")
            print(traceback.format_exc())
            # Fall through to smart fallback below

    # ── SMART RULE-BASED FALLBACK (no API key) ──────────────────────

    msg = message.lower()

    # Attendance — many ways to ask
    att_words = ['attendance','bunked','bunk','absent','75','detention','detained',
                 'how many class','safe','present','miss','missing','classes needed',
                 'will i pass','can i bunk','skip']
    if any(w in msg for w in att_words):
        if student_id:
            conn = get_db()
            att  = [dict(r) for r in conn.execute('SELECT * FROM attendance WHERE student_id=?',(student_id,)).fetchall()]
            conn.close()
            low  = [a for a in att if a['percentage'] < 75]
            safe = [a for a in att if a['percentage'] >= 75]
            if low:
                lines = [f"⚠️ You have {len(low)} subject(s) below 75%:"]
                for a in low:
                    T,A = a['total_classes'],a['attended_classes']
                    needed = max(0,int((0.75*T-A)/0.25)+1)
                    lines.append(f"• {a['subject']}: {a['percentage']:.1f}% — attend {needed} more classes")
                lines.append(f"✅ {len(safe)} subject(s) are safe.")
                return jsonify({'response':'\n'.join(lines), 'source':'rule'})
            return jsonify({'response':f"✅ All {len(att)} subjects are above 75%! You are completely safe from detention.", 'source':'rule'})
        return jsonify({'response':'Minimum attendance required is 75% in every subject. Below 75% means you cannot write the exam.', 'source':'rule'})

    # Marks / CGPA — many ways to ask
    marks_words = ['marks','grade','cgpa','gpa','score','result','perform','rank',
                   'how am i doing','doing well','subject','internal','external']
    if any(w in msg for w in marks_words):
        if student_id:
            conn  = get_db()
            marks = [dict(r) for r in conn.execute('SELECT * FROM marks WHERE student_id=?',(student_id,)).fetchall()]
            conn.close()
            if marks:
                gp = {'A+':10,'A':9,'B+':8,'B':7,'C':6}
                tc   = sum(m['credits'] for m in marks)
                cgpa = round(sum(gp.get(m['grade'],7)*m['credits'] for m in marks)/tc,2) if tc else 0
                best = max(marks,key=lambda x:x['total_marks'])
                weak = min(marks,key=lambda x:x['total_marks'])
                lines = [f"📊 Your CGPA: {cgpa}"]
                for m in marks:
                    lines.append(f"• {m['subject']}: {m['total_marks']}/100 ({m['grade']})")
                lines.append(f"🏆 Best: {best['subject']} | 📉 Needs work: {weak['subject']}")
                return jsonify({'response':'\n'.join(lines), 'source':'rule'})
        return jsonify({'response':'Your marks and CGPA are shown in the Marks & Grades tab.', 'source':'rule'})

    # Outpass
    if any(w in msg for w in ['outpass','outing','go out','leave','permission','exit']):
        return jsonify({'response':'🚪 Outpass needs 4 approvals:\n1. Faculty Advisor\n2. Hostel Coordinator\n3. HOD\n4. Hostel Warden\nApply in the Outpass tab. All 4 must approve before you can leave.', 'source':'rule'})

    # Fees
    if any(w in msg for w in ['fee','money','pay','payment','due','pending','arrear']):
        if student_id:
            conn = get_db()
            fees = row_to_dict(conn.execute('SELECT * FROM fees WHERE student_id=?',(student_id,)).fetchone())
            conn.close()
            if fees:
                return jsonify({'response':f"💰 Fee Status: {fees['status']}\nTotal: ₹{fees['total_fee']:,.0f} | Paid: ₹{fees['paid_amount']:,.0f} | Pending: ₹{fees['pending_amount']:,.0f}\nDue date: {fees['due_date']}", 'source':'rule'})
        return jsonify({'response':'Your fee details are in the Fee Status tab. Pay before due date to avoid penalty.', 'source':'rule'})

    # Exam
    if any(w in msg for w in ['exam','test','hall ticket','schedule','when is']):
        if student_id:
            conn  = get_db()
            std   = row_to_dict(conn.execute('SELECT semester FROM students WHERE id=?',(student_id,)).fetchone())
            exams = [dict(r) for r in conn.execute('SELECT * FROM exam_schedule WHERE semester=? ORDER BY exam_date',(std['semester'],)).fetchall()] if std else []
            conn.close()
            if exams:
                lines = ["📅 Your exam schedule:"]
                for e in exams:
                    lines.append(f"• {e['subject']}: {e['exam_date']} at {e['time']}, {e['hall']}")
                return jsonify({'response':'\n'.join(lines), 'source':'rule'})
        return jsonify({'response':'Exam schedule is in the Exams tab. Carry ID card + hall ticket on exam day.', 'source':'rule'})

    # Teacher finder — "where is X", "find X", "locate X"
    find_words = ['where is','find','locate','room of','office of','sir','mam','professor','doctor','dr.','prof.']
    if any(w in msg for w in find_words):
        # Extract name — remove trigger words
        name_q = msg
        for w in ['where is','find','locate','room of','office of',' sir',' mam']:
            name_q = name_q.replace(w,'')
        name_q = name_q.strip().strip('?').strip()
        if len(name_q) > 2:
            conn = get_db()
            t = conn.execute(
                "SELECT t.*,ts.current_status,ts.location,ts.available_from,ts.available_to "
                "FROM teachers t LEFT JOIN teacher_status ts ON t.id=ts.teacher_id "
                "WHERE LOWER(t.name) LIKE ?",(f'%{name_q}%',)).fetchone()
            conn.close()
            if t:
                t = dict(t)
                return jsonify({'response':f"📍 {t['name']} ({t['designation']})\nStatus: {t['current_status'] or 'Unknown'}\nLocation: {t['location'] or t['office_room']}\nAvailable: {t['available_from'] or 'N/A'} – {t['available_to'] or 'N/A'}", 'source':'rule'})

    # HOD
    if any(w in msg for w in ['hod','head of department','department head']):
        conn = get_db()
        hod  = conn.execute('''SELECT t.name,t.department,t.office_room,ts.current_status,ts.location
            FROM faculty_roles fr JOIN teachers t ON fr.teacher_id=t.id
            LEFT JOIN teacher_status ts ON t.id=ts.teacher_id
            WHERE fr.role_type="HOD" LIMIT 1''').fetchone()
        conn.close()
        if hod:
            return jsonify({'response':f"👨‍🏫 HOD of {hod['department']}: {hod['name']}\nOffice: {hod['office_room']}\nStatus: {hod['current_status'] or 'Unknown'}", 'source':'rule'})

    # Hostel / Warden
    if any(w in msg for w in ['hostel','warden','mess','room','accommodation','block']):
        return jsonify({'response':'🏠 For hostel issues, raise a ticket in Help Desk → Category: Hostel. The warden will respond.', 'source':'rule'})

    # Timetable
    if any(w in msg for w in ['timetable','time table','class','today','tomorrow','schedule']):
        return jsonify({'response':'📅 Your class timetable is in the Timetable tab with all subjects, timings and rooms.', 'source':'rule'})

    # Greetings
    if any(w in msg for w in ['hello','hi','hey','good morning','good evening','what can','help me']):
        return jsonify({'response':"👋 Hi! I'm SmartCampus AI. Ask me anything about:\n• Attendance & detention risk\n• Marks & CGPA\n• Outpass rules\n• Exam schedule\n• Fees\n• Finding a teacher\n• Study tips", 'source':'rule'})

    # Default — honest response
    return jsonify({'response':"I didn't quite understand that. Try asking like:\n• 'Am I safe from detention?'\n• 'What is my CGPA?'\n• 'Where is Dr. Rajesh?'\n• 'When is my exam?'\n• 'How do I apply for outpass?'", 'source':'rule'})




RESOURCE_DB = {
    "Data Structures": [
        {"title":"Arrays & Linked Lists from Scratch","type":"YouTube","channel":"Abdul Bari","difficulty":"Beginner","url_query":"Abdul Bari data structures arrays linked lists","tags":["basics","arrays","linked list"],"vector":[1,0,0,0,1]},
        {"title":"Trees and Graphs — Complete Guide","type":"YouTube","channel":"Abdul Bari","difficulty":"Intermediate","url_query":"Abdul Bari trees graphs data structures","tags":["trees","graphs","dfs","bfs"],"vector":[0,1,0,0,1]},
        {"title":"LeetCode — Easy Array Problems","type":"Practice","channel":"LeetCode","difficulty":"Beginner","url_query":"leetcode easy array problems","tags":["practice","arrays","coding"],"vector":[1,0,0,1,0]},
        {"title":"Dynamic Programming Full Course","type":"YouTube","channel":"Striver","difficulty":"Advanced","url_query":"Striver dynamic programming full course","tags":["dp","advanced","interview"],"vector":[0,0,1,1,0]},
        {"title":"GeeksForGeeks — DSA Self Paced","type":"Article","channel":"GeeksForGeeks","difficulty":"Intermediate","url_query":"geeksforgeeks data structures self paced","tags":["all topics","notes","practice"],"vector":[0,1,1,1,1]},
    ],
    "Database Systems": [
        {"title":"SQL Full Course for Beginners","type":"YouTube","channel":"Programming with Mosh","difficulty":"Beginner","url_query":"Programming with Mosh SQL full course","tags":["sql","basics","queries"],"vector":[1,0,0,1,0]},
        {"title":"Database Normalization Explained","type":"YouTube","channel":"Caleb Curry","difficulty":"Intermediate","url_query":"Caleb Curry database normalization 1NF 2NF 3NF","tags":["normalization","1NF","2NF","3NF"],"vector":[0,1,0,0,1]},
        {"title":"ER Diagram — Entity Relationship","type":"YouTube","channel":"Lucidchart","difficulty":"Beginner","url_query":"ER diagram entity relationship tutorial","tags":["ER diagram","design"],"vector":[1,0,0,0,1]},
        {"title":"SQLZoo — Interactive SQL Practice","type":"Practice","channel":"SQLZoo","difficulty":"Beginner","url_query":"sqlzoo interactive sql practice","tags":["practice","sql","queries"],"vector":[1,1,0,1,0]},
        {"title":"Transactions & ACID Properties","type":"YouTube","channel":"Neso Academy","difficulty":"Advanced","url_query":"Neso Academy ACID transactions database","tags":["transactions","ACID","concurrency"],"vector":[0,0,1,0,1]},
    ],
    "Computer Networks": [
        {"title":"Computer Networks Full Course","type":"YouTube","channel":"Gate Smashers","difficulty":"Beginner","url_query":"Gate Smashers computer networks full course","tags":["OSI","basics","protocols"],"vector":[1,0,0,0,1]},
        {"title":"OSI Model — All 7 Layers","type":"YouTube","channel":"PowerCert","difficulty":"Beginner","url_query":"PowerCert OSI model 7 layers explained","tags":["OSI","layers","theory"],"vector":[1,0,0,0,1]},
        {"title":"TCP/IP and Subnetting","type":"YouTube","channel":"Professor Messer","difficulty":"Intermediate","url_query":"Professor Messer TCP IP subnetting","tags":["TCP","IP","subnetting"],"vector":[0,1,0,1,0]},
        {"title":"Cisco Packet Tracer — Practice Labs","type":"Practice","channel":"Cisco","difficulty":"Intermediate","url_query":"Cisco Packet Tracer networking labs practice","tags":["lab","practical","routing"],"vector":[0,1,0,1,0]},
        {"title":"Network Security Fundamentals","type":"YouTube","channel":"NetworkChuck","difficulty":"Advanced","url_query":"NetworkChuck network security fundamentals","tags":["security","firewall","advanced"],"vector":[0,0,1,1,0]},
    ],
    "Operating Systems": [
        {"title":"OS Full Course — Process & Threads","type":"YouTube","channel":"Gate Smashers","difficulty":"Beginner","url_query":"Gate Smashers operating system full course","tags":["process","threads","basics"],"vector":[1,0,0,0,1]},
        {"title":"CPU Scheduling Algorithms","type":"YouTube","channel":"Neso Academy","difficulty":"Intermediate","url_query":"Neso Academy CPU scheduling FCFS SJF RR","tags":["scheduling","FCFS","SJF","round robin"],"vector":[0,1,0,0,1]},
        {"title":"Memory Management & Paging","type":"YouTube","channel":"Neso Academy","difficulty":"Intermediate","url_query":"Neso Academy memory management paging segmentation","tags":["memory","paging","virtual memory"],"vector":[0,1,0,0,1]},
        {"title":"Deadlock — Detection & Prevention","type":"YouTube","channel":"Abdul Bari","difficulty":"Advanced","url_query":"Abdul Bari deadlock detection prevention avoidance","tags":["deadlock","Banker's algorithm"],"vector":[0,0,1,0,1]},
        {"title":"OS Interview Questions — Practice","type":"Article","channel":"InterviewBit","difficulty":"Intermediate","url_query":"operating system interview questions interviewbit","tags":["interview","practice","all topics"],"vector":[0,1,1,1,0]},
    ],
    "Software Engineering": [
        {"title":"SDLC Models Explained","type":"YouTube","channel":"Simplilearn","difficulty":"Beginner","url_query":"Simplilearn SDLC software development life cycle models","tags":["SDLC","waterfall","agile"],"vector":[1,0,0,0,1]},
        {"title":"UML Diagrams Full Tutorial","type":"YouTube","channel":"Lucidchart","difficulty":"Intermediate","url_query":"UML diagrams tutorial use case class sequence","tags":["UML","diagrams","design"],"vector":[0,1,0,0,1]},
        {"title":"Agile & Scrum in 10 Minutes","type":"YouTube","channel":"Atlassian","difficulty":"Beginner","url_query":"Atlassian agile scrum methodology explained","tags":["agile","scrum","project management"],"vector":[1,0,0,1,0]},
        {"title":"Design Patterns — Gang of Four","type":"YouTube","channel":"Christopher Okhravi","difficulty":"Advanced","url_query":"Christopher Okhravi design patterns tutorial","tags":["design patterns","OOP","advanced"],"vector":[0,0,1,0,1]},
        {"title":"Software Testing — Types & Methods","type":"YouTube","channel":"SDET","difficulty":"Intermediate","url_query":"software testing types unit integration system","tags":["testing","QA","unit test"],"vector":[0,1,0,1,0]},
    ],
    "Machine Learning": [
        {"title":"ML Full Course — Andrew Ng","type":"YouTube","channel":"Stanford/Coursera","difficulty":"Intermediate","url_query":"Andrew Ng machine learning full course Stanford","tags":["fundamentals","regression","neural networks"],"vector":[0,1,0,0,1]},
        {"title":"Scikit-Learn Crash Course","type":"YouTube","channel":"Sentdex","difficulty":"Beginner","url_query":"scikit-learn machine learning python tutorial Sentdex","tags":["python","sklearn","practical"],"vector":[1,0,0,1,0]},
        {"title":"Kaggle — Intro to ML","type":"Practice","channel":"Kaggle","difficulty":"Beginner","url_query":"Kaggle intro to machine learning course","tags":["practice","datasets","competition"],"vector":[1,0,0,1,0]},
        {"title":"Neural Networks from Scratch","type":"YouTube","channel":"3Blue1Brown","difficulty":"Advanced","url_query":"3Blue1Brown neural networks deep learning","tags":["neural networks","backprop","math"],"vector":[0,0,1,0,1]},
        {"title":"Feature Engineering Guide","type":"Article","channel":"Towards Data Science","difficulty":"Intermediate","url_query":"feature engineering guide machine learning medium","tags":["features","preprocessing","EDA"],"vector":[0,1,0,1,0]},
    ],
    "Circuit Theory": [
        {"title":"Basic Circuit Analysis","type":"YouTube","channel":"The Organic Chemistry Tutor","difficulty":"Beginner","url_query":"circuit analysis KVL KCL Ohm's law tutorial","tags":["KVL","KCL","basics"],"vector":[1,0,0,0,1]},
        {"title":"AC Circuits — Phasors & Impedance","type":"YouTube","channel":"Michel van Biezen","difficulty":"Intermediate","url_query":"AC circuits phasors impedance tutorial","tags":["AC","phasors","impedance"],"vector":[0,1,0,0,1]},
        {"title":"Circuit Simulation — Falstad","type":"Practice","channel":"Falstad","difficulty":"Beginner","url_query":"Falstad circuit simulator online practice","tags":["simulation","practical","lab"],"vector":[1,0,0,1,0]},
    ],
    "Engineering Mechanics": [
        {"title":"Engineering Mechanics Full Course","type":"YouTube","channel":"MKS Tutorials","difficulty":"Beginner","url_query":"MKS tutorials engineering mechanics statics","tags":["statics","forces","basics"],"vector":[1,0,0,0,1]},
        {"title":"Free Body Diagrams Explained","type":"YouTube","channel":"The Organic Chemistry Tutor","difficulty":"Beginner","url_query":"free body diagram tutorial engineering mechanics","tags":["FBD","forces","equilibrium"],"vector":[1,0,0,1,0]},
    ],
}

# Default resources for subjects not in DB
DEFAULT_RESOURCES = [
    {"title":"Search on YouTube for your subject","type":"YouTube","channel":"Various","difficulty":"Beginner","url_query":"","tags":["general"],"vector":[1,1,0,0,1]},
    {"title":"GeeksForGeeks — All Topics","type":"Article","channel":"GeeksForGeeks","difficulty":"Intermediate","url_query":"geeksforgeeks","tags":["general","notes"],"vector":[0,1,1,0,1]},
    {"title":"NPTEL Video Lectures","type":"YouTube","channel":"NPTEL","difficulty":"Intermediate","url_query":"NPTEL lecture","tags":["IIT","lecture","theory"],"vector":[0,1,0,0,1]},
]


def cosine_similarity(vec_a, vec_b):
    """
    Cosine Similarity = (A · B) / (|A| × |B|)
    Measures the angle between two vectors.
    Score of 1.0 = identical, 0.0 = completely different.
    This is the core ML algorithm used for recommendations.
    """
    dot_product  = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a  = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b  = math.sqrt(sum(b * b for b in vec_b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return round(dot_product / (magnitude_a * magnitude_b), 4)


def student_to_vector(marks, attendance_pct):
    """
    Convert student's performance into a 5-dimensional feature vector:
    [beginner_need, intermediate_need, advanced_ready, practical_need, theory_need]

    Logic:
    - Low marks (< 60) → needs beginner + theory content
    - Medium marks (60-75) → needs intermediate + practical
    - High marks (> 75) → ready for advanced content
    - Low attendance → needs more practical/hands-on resources
    """
    score = marks / 100.0
    att   = attendance_pct / 100.0

    beginner     = round(max(0, 1 - score * 1.5), 2)          # high when marks low
    intermediate = round(1 - abs(score - 0.65) * 2, 2)        # peaks at ~65%
    intermediate = max(0, intermediate)
    advanced     = round(max(0, score * 1.3 - 0.7), 2)        # high when marks good
    practical    = round(max(0, 1 - att * 1.2), 2)            # high when attendance low
    theory       = round(min(1, (1 - score) + (1 - att) * 0.3), 2)  # needs theory

    return [beginner, intermediate, advanced, practical, theory]


@app.route('/api/ai/recommendations/<int:student_id>')
def get_recommendations(student_id):
    """
  
    conn = get_db()
    marks  = [dict(r) for r in conn.execute(
        'SELECT * FROM marks WHERE student_id=?', (student_id,)).fetchall()]
    att    = [dict(r) for r in conn.execute(
        'SELECT * FROM attendance WHERE student_id=?', (student_id,)).fetchall()]

    # Collaborative filtering: find peers with same weak subjects
    all_marks = [dict(r) for r in conn.execute(
        'SELECT * FROM marks WHERE student_id != ?', (student_id,)).fetchall()]
    conn.close()

    if not marks:
        return jsonify({'error': 'No marks data found'}), 404

    att_map = {a['subject']: a['percentage'] for a in att}
    gp      = {'A+': 10, 'A': 9, 'B+': 8, 'B': 7, 'C': 6}

    # ── Step 1: Identify weak subjects (sorted by priority) ─────────────
    subject_scores = []
    for m in marks:
        att_pct  = att_map.get(m['subject'], 80)
        gp_score = gp.get(m['grade'], 7)
        # Priority score — higher = needs more help
        priority = round((100 - m['total_marks']) * 0.6 + (10 - gp_score) * 4, 1)
        subject_scores.append({
            'subject'    : m['subject'],
            'marks'      : m['total_marks'],
            'grade'      : m['grade'],
            'attendance' : att_pct,
            'priority'   : priority,
            'needs_help' : m['total_marks'] < 75 or m['grade'] in ['B', 'C']
        })

    subject_scores.sort(key=lambda x: x['priority'], reverse=True)

    # ── Step 2: Content-Based Filtering with Cosine Similarity ──────────
    recommendations = []

    for subj_data in subject_scores[:5]:   # top 5 subjects by priority
        subject     = subj_data['subject']
        student_vec = student_to_vector(subj_data['marks'], subj_data['attendance'])
        resources   = RESOURCE_DB.get(subject, DEFAULT_RESOURCES)

        # Compute cosine similarity for each resource
        scored_resources = []
        for res in resources:
            sim   = cosine_similarity(student_vec, res['vector'])
            level = 'Perfect Match' if sim >= 0.8 else 'Good Match' if sim >= 0.5 else 'Suggested'
            scored_resources.append({
                **res,
                'similarity_score' : sim,
                'match_level'      : level,
                'youtube_url'      : f"https://www.youtube.com/results?search_query={res['url_query'].replace(' ', '+')}" if res['type'] == 'YouTube' else None,
                'search_url'       : f"https://www.google.com/search?q={res['url_query'].replace(' ', '+')}"
            })

        # Sort by cosine similarity — highest first
        scored_resources.sort(key=lambda x: x['similarity_score'], reverse=True)

        recommendations.append({
            'subject'         : subject,
            'marks'           : subj_data['marks'],
            'grade'           : subj_data['grade'],
            'attendance'      : subj_data['attendance'],
            'priority_score'  : subj_data['priority'],
            'needs_help'      : subj_data['needs_help'],
            'student_vector'  : student_vec,   # show the ML vector to user
            'top_resources'   : scored_resources[:3],   # top 3 by cosine sim
            'all_resources'   : scored_resources
        })

    # ── Step 3: Collaborative Filtering ─────────────────────────────────
    # Find other students who had the same weak subjects and see what worked
    weak_subjects    = [s['subject'] for s in subject_scores if s['needs_help']]
    peer_suggestions = []

    if all_marks and weak_subjects:
        # Group other students' marks by subject
        peer_weak = {}
        for m in all_marks:
            if m['subject'] in weak_subjects and m['grade'] in ['B', 'C']:
                subj = m['subject']
                if subj not in peer_weak:
                    peer_weak[subj] = 0
                peer_weak[subj] += 1

        # Subjects that many peers also struggle with → validated weak area
        for subj, count in sorted(peer_weak.items(), key=lambda x: x[1], reverse=True)[:3]:
            peer_suggestions.append({
                'subject'       : subj,
                'peers_count'   : count,
                'message'       : f"{count} other students also struggled with {subj}. You are not alone — focus here!"
            })

    # ── Step 4: Overall recommendation summary ──────────────────────────
    total_subjects = len(marks)
    weak_count     = len([s for s in subject_scores if s['needs_help']])
    avg_marks      = round(sum(m['marks'] for m in subject_scores) / len(subject_scores), 1)

    # Which type of resources to prioritize
    if avg_marks < 55:
        strategy = "Start with beginner YouTube videos. Understand basics before anything else."
        focus    = "Theory & Fundamentals"
    elif avg_marks < 70:
        strategy = "Mix of theory + practice. Do notes first, then solve problems."
        focus    = "Concept Clarity + Practice"
    else:
        strategy = "You are doing well! Focus on advanced topics and interview prep."
        focus    = "Advanced Topics + Interview Prep"

    return jsonify({
        'student_id'           : student_id,
        'total_subjects'       : total_subjects,
        'weak_subjects_count'  : weak_count,
        'average_marks'        : avg_marks,
        'learning_strategy'    : strategy,
        'focus_area'           : focus,
        'recommendations'      : recommendations,
        'peer_insights'        : peer_suggestions,
        'ml_technique'         : 'Content-Based Filtering (Cosine Similarity) + Collaborative Filtering',
        'vector_dimensions'    : ['beginner_need','intermediate_need','advanced_ready','practical_need','theory_need']
    })

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("  SmartCampus AI Backend v3")
    print("  URL: http://localhost:5000")
    print("  Student: RA2111003010001 / password123")
    print("  Teacher: T001 / teacher123")
    print("="*50+"\n")
    app.run(debug=True, port=5000)


# ═══════════════════════════════════════════════════════════════
# AI FEATURE 1 — ATTENDANCE PREDICTOR
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("  SmartCampus AI Backend v3")
    print("  URL: http://localhost:5000")
    print("  Student: RA2111003010001 / password123")
    print("  Teacher: T001 / teacher123")
    print("="*50+"\n")
    app.run(debug=True, port=5000)


# ═══════════════════════════════════════════════════════════════
# AI FEATURE 1 — ATTENDANCE PREDICTOR
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    init_db()
    print("\n" + "="*50)
    print("  SmartCampus AI Backend v3")
    print("  URL: http://localhost:5000")
    print("  Student: RA2111003010001 / password123")
    print("  Teacher: T001 / teacher123")
    print("="*50+"\n")
    app.run(debug=True, port=5000)


# ═══════════════════════════════════════════════════════════════
# AI FEATURE 1 — ATTENDANCE PREDICTOR
# ═══════════════════════════════════════════════════════════════
@app.route('/api/ai/outpass-risk', methods=['POST'])
def outpass_risk_checker():
    d=request.json or {}
    reason=d.get('reason','').lower()
    destination=d.get('destination','').lower()
    out_time=d.get('out_time','12:00')
    student_id=d.get('student_id')
    risk=0; flags=[]; positives=[]
    try: hour=int(out_time.split(':')[0])
    except: hour=12
    if hour<6: risk+=4; flags.append('Very early hours before 6 AM')
    elif hour>=21: risk+=3; flags.append('Late night request after 9 PM — warden approval required')
    else: positives.append('Request during safe hours (6 AM – 9 PM)')
    medical=['hospital','doctor','clinic','medical','emergency','dentist','health','pharmacy']
    academic=['library','project','internship','seminar','workshop','conference','lab']
    family=['family','home','parents','wedding','function','festival']
    vague=['outing','fun','shopping','movie','mall','party','roam']
    if any(w in reason+destination for w in medical): positives.append('Medical reason — valid and important'); risk-=1
    elif any(w in reason for w in academic): positives.append('Academic reason — supports studies')
    elif any(w in reason for w in family): positives.append('Family reason — personal but valid')
    elif any(w in reason for w in vague): risk+=2; flags.append('Reason appears non-essential (leisure)')
    else: risk+=1; flags.append('Reason is vague — more details needed')
    if student_id:
        conn=get_db()
        att=[dict(r) for r in conn.execute('SELECT percentage FROM attendance WHERE student_id=?',(student_id,)).fetchall()]
        conn.close()
        low=[a for a in att if a['percentage']<75]
        if len(low)>=3: risk+=3; flags.append(f'{len(low)} subjects below 75% — leaving will worsen attendance')
        elif len(low)>=1: risk+=1; flags.append(f'{len(low)} subject(s) below 75%')
        else: positives.append('Student has good attendance in all subjects')
    risk=max(0,min(risk,10))
    if risk<=2: decision='AUTO-APPROVE'; dc='green'; rec='LOW RISK — Recommend approval. Valid reason and safe timing.'
    elif risk<=5: decision='REVIEW'; dc='orange'; rec='MODERATE RISK — Manual review recommended before approving.'
    else: decision='FLAG'; dc='red'; rec='HIGH RISK — Flag this request. Multiple concerns detected.'
    return jsonify({'decision':decision,'decision_color':dc,'risk_score':risk,'risk_level':'Low' if risk<=2 else 'Moderate' if risk<=5 else 'High','recommendation':rec,'positive_factors':positives,'risk_factors':flags})
