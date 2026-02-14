import sqlite3, os, csv

DB_PATH      = os.path.join(os.path.dirname(__file__), 'data', 'campus.db')
TEACHERS_CSV = os.path.join(os.path.dirname(__file__), 'teachers.csv')

def main():
    # ── Checks ────────────────────────────────────────────────────
    if not os.path.exists(DB_PATH):
        print("ERROR: campus.db not found!")
        print("Run 'python app.py' first to create the database, then run this script.")
        return

    if not os.path.exists(TEACHERS_CSV):
        print("ERROR: teachers.csv not found!")
        print("Put teachers.csv in the backend folder next to this script.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ── Make sure required tables exist ───────────────────────────
    c.executescript('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            department TEXT,
            designation TEXT,
            office_room TEXT,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS faculty_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            role_type TEXT,
            role_name TEXT,
            department TEXT
        );
        CREATE TABLE IF NOT EXISTS teacher_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER UNIQUE,
            current_status TEXT DEFAULT "Available",
            location TEXT,
            available_from TEXT,
            available_to TEXT
        );
    ''')
    conn.commit()

    added   = 0
    skipped = 0

    with open(TEACHERS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            tid = row['teacher_id'].strip()

            # Skip if already exists
            exists = c.execute(
                'SELECT id FROM teachers WHERE teacher_id=?', (tid,)
            ).fetchone()

            if exists:
                print(f"  Skipping {tid} — already exists")
                skipped += 1
                continue

            # ── Insert teacher ─────────────────────────────────────
            c.execute('''
                INSERT INTO teachers
                    (teacher_id, name, email, department, designation, office_room, password)
                VALUES (?,?,?,?,?,?,?)
            ''', (
                tid,
                row['name'].strip(),
                row['email'].strip(),
                row['department'].strip(),
                row['designation'].strip(),
                row['office_room'].strip(),
                row['password'].strip()
            ))
            teacher_db_id = c.lastrowid

            # ── Insert role ────────────────────────────────────────
            if row.get('role_type','').strip():
                c.execute('''
                    INSERT INTO faculty_roles (teacher_id, role_type, role_name, department)
                    VALUES (?,?,?,?)
                ''', (
                    teacher_db_id,
                    row['role_type'].strip(),
                    row['role_name'].strip(),
                    row['department'].strip()
                ))

            # ── Insert default status ──────────────────────────────
            c.execute('''
                INSERT OR IGNORE INTO teacher_status
                    (teacher_id, current_status, location, available_from, available_to)
                VALUES (?,?,?,?,?)
            ''', (
                teacher_db_id,
                'Available',
                row['office_room'].strip(),
                '9:00 AM',
                '5:00 PM'
            ))

            added += 1
            print(f"  ✅ Added: {tid} — {row['name']} ({row['role_name']})")

    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"  Import Complete!")
    print(f"  Added   : {added} teachers")
    print(f"  Skipped : {skipped} (already existed)")
    print(f"\n  All teacher passwords: teacher123")
    print(f"\n  Teacher IDs:")
    print(f"  T001 — Dr. Rajesh Kumar     (HOD)")
    print(f"  T002 — Prof. Priya Sharma   (Faculty Advisor)")
    print(f"  T003 — Dr. Suresh Reddy     (Hostel Warden)")
    print(f"  T004 — Prof. Anita Desai    (Faculty Advisor)")
    print(f"  T005 — Dr. Vikram Singh     (Hostel Coordinator)")
    print(f"  T006 — Dr. Meena Iyer       (Faculty Advisor)")
    print(f"  T007 — Prof. Karthik Nair   (Faculty Advisor)")
    print(f"  T008 — Dr. Lakshmi Pillai   (HOD - IT)")
    print(f"  T009 — Prof. Arun Menon     (Faculty Advisor)")
    print(f"  T010 — Dr. Sunita Rao       (Faculty Advisor)")
    print(f"{'='*50}")
    print(f"\nRestart app.py and login with any teacher ID!")

if __name__ == "__main__":
    main()
