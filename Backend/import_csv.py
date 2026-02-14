import sqlite3, os, csv, random

DB_PATH  = os.path.join(os.path.dirname(__file__), 'data', 'campus.db')
CSV_PATH = os.path.join(os.path.dirname(__file__), 'students.csv')

SUBJECTS_BY_DEPT = {
    "CSE":  ["Data Structures","Database Systems","Computer Networks","Operating Systems","Software Engineering"],
    "ECE":  ["Circuit Theory","Digital Electronics","Signals & Systems","Microprocessors","Communication Systems"],
    "MECH": ["Engineering Mechanics","Thermodynamics","Fluid Mechanics","Manufacturing Processes","Machine Design"],
    "CIVIL":["Surveying","Structural Analysis","Concrete Technology","Geotechnical Engineering","Fluid Mechanics"],
    "EEE":  ["Circuit Analysis","Electrical Machines","Power Systems","Control Systems","Power Electronics"],
    "IT":   ["Web Technologies","Database Management","Computer Networks","Software Testing","Cloud Computing"],
    "AIDS": ["Machine Learning","Data Analytics","Deep Learning","Natural Language Processing","Computer Vision"],
    "CSBS": ["Business Analytics","Data Science","Blockchain","IoT","Cyber Security"]
}
GRADES      = ["A+","A","B+","B","C"]
GRADE_MARKS = {
    "A+": (22, 80, 25, 100),   # (internal_min, external_min, internal_max, external_max)
    "A":  (18, 68, 24,  85),
    "B+": (16, 56, 22,  75),
    "B":  (14, 45, 20,  65),
    "C":  (12, 35, 18,  55),
}
DAYS        = ["MON","TUE","WED","THU","FRI"]
SLOTS       = ["8.00-8.50","8.50-9.40","9.50-10.40","10.40-11.30","12.20-1.10","1.10-2.00"]
TEACHERS    = ["Dr. Rajesh Kumar","Prof. Priya Sharma","Dr. Suresh Reddy",
               "Prof. Anita Desai","Dr. Vikram Singh"]

def main():
    if not os.path.exists(DB_PATH):
        print("ERROR: campus.db not found. Run app.py first!")
        return
    if not os.path.exists(CSV_PATH):
        print("ERROR: students.csv not found. Put it in the backend folder!")
        return

    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        added = 0
        skipped = 0

        for row in reader:
            reg_no = row['reg_no'].strip()

            # Skip if already exists
            exists = c.execute('SELECT id FROM students WHERE reg_no=?', (reg_no,)).fetchone()
            if exists:
                print(f"  Skipping {reg_no} — already exists")
                skipped += 1
                continue

            # Insert student
            c.execute('''INSERT INTO students
                (reg_no,name,email,phone,department,year,semester,section,hostel,is_hosteler,password)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (
                reg_no,
                row['name'].strip(),
                row['email'].strip(),
                row['phone'].strip(),
                row['department'].strip(),
                int(row['year']),
                int(row['semester']),
                row['section'].strip(),
                row['hostel'].strip(),
                int(row['is_hosteler']),
                row['password'].strip()
            ))
            student_id = c.lastrowid
            dept       = row['department'].strip()
            subjects   = SUBJECTS_BY_DEPT.get(dept, SUBJECTS_BY_DEPT["CSE"])

            # Attendance
            for subj in subjects:
                total    = random.choice([38,40,42,44])
                pct_val  = random.choices(
                    [random.uniform(60,74), random.uniform(75,95)],
                    weights=[25,75])[0]
                attended = max(0, min(int(pct_val/100*total), total))
                pct      = round(attended/total*100, 1)
                c.execute('INSERT INTO attendance (student_id,subject,total_classes,attended_classes,percentage) VALUES (?,?,?,?,?)',
                          (student_id, subj, total, attended, pct))

            # Marks
            for subj in subjects:
                grade = random.choices(GRADES, weights=[20,30,25,15,10])[0]
                i_min, e_min, i_max, e_max = GRADE_MARKS[grade]
                internal = random.randint(i_min, i_max)
                external = random.randint(e_min, e_max)
                credits  = random.choice([3,4])
                c.execute('INSERT INTO marks (student_id,subject,internal_marks,external_marks,total_marks,grade,credits) VALUES (?,?,?,?,?,?,?)',
                          (student_id, subj, internal, external, internal+external, grade, credits))

            # Timetable
            for day in DAYS:
                for slot in random.sample(SLOTS, k=random.randint(3,5)):
                    c.execute('INSERT INTO timetable (student_id,day,time_slot,subject,teacher_name,room) VALUES (?,?,?,?,?,?)',
                              (student_id, day, slot,
                               random.choice(subjects),
                               random.choice(TEACHERS),
                               f"{dept}-{random.randint(1,5)}0{random.randint(1,9)}"))

            # Fees
            total_fee = random.choice([85000,90000,95000,100000])
            paid      = random.randint(0, total_fee)
            pending   = total_fee - paid
            status    = "Paid" if pending==0 else ("Partial" if paid>0 else "Pending")
            c.execute('INSERT INTO fees (student_id,total_fee,paid_amount,pending_amount,status,due_date) VALUES (?,?,?,?,?,?)',
                      (student_id, total_fee, paid, pending, status, "2024-11-30"))

            added += 1
            print(f"  ✅ Added: {reg_no} — {row['name']}")

        conn.commit()
        conn.close()

        print(f"\n{'='*45}")
        print(f"  Import Complete!")
        print(f"  Added   : {added} students")
        print(f"  Skipped : {skipped} (already existed)")
        print(f"  All passwords: password123")
        print(f"{'='*45}")
        print(f"\nRestart app.py and test any student login!")

if __name__ == "__main__":
    main()
