#!/usr/bin/env python3
"""
Standalone script to fix the students_student PK migration.
Connects directly to MySQL (bypasses Django to avoid lock issues).

Current DB state:
- students_student: NO primary key, broken nullable `id` column, matricule is UNIQUE KEY
- Related tables: student_id is still VARCHAR(50), FK constraints to matricule were dropped
  by partial migration, but indexes remain
"""
import pymysql

conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='672279946',
    database='ysem_project',
    autocommit=True,
    connect_timeout=30,
    read_timeout=120,
    write_timeout=120,
)
cursor = conn.cursor()

def exe(sql, label=""):
    print(f"  -> {label or sql[:80]}...")
    cursor.execute(sql)
    print(f"     OK")

def safe_drop_fk(table, constraint):
    """Drop FK only if it exists."""
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        AND CONSTRAINT_NAME = %s AND CONSTRAINT_TYPE = 'FOREIGN KEY'
    """, (table, constraint))
    if cursor.fetchone()[0] > 0:
        exe(f"ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint}`",
            f"Drop FK {constraint} on {table}")
    else:
        print(f"  -> FK {constraint} on {table} already dropped, skipping")

def safe_drop_index(table, index):
    """Drop index only if it exists."""
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND INDEX_NAME = %s
    """, (table, index))
    if cursor.fetchone()[0] > 0:
        exe(f"ALTER TABLE `{table}` DROP INDEX `{index}`",
            f"Drop index {index} on {table}")
    else:
        print(f"  -> Index {index} on {table} already dropped, skipping")

def col_exists(table, column):
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s
    """, (table, column))
    return cursor.fetchone()[0] > 0

def has_pk(table):
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND CONSTRAINT_TYPE = 'PRIMARY KEY'
    """, (table,))
    return cursor.fetchone()[0] > 0

print("=" * 60)
print("STEP 1: Fix students_student table")
print("=" * 60)

# Drop FKs from related tables (if they still exist)
safe_drop_fk('students_studentlevel', 'students_studentleve_student_id_deb00ed7_fk_students_')
safe_drop_fk('payments_payment', 'payments_payment_student_id_b5fab56a_fk_students_')
safe_drop_fk('Teaching_evaluation', 'Teaching_evaluation_student_id_f1f618cf_fk_students_')

# Drop the unique-together index on studentlevel if it exists
safe_drop_index('students_studentlevel', 'students_studentlevel_student_id_level_id_acad_94570ecb_uniq')

# Drop broken id column if it exists
if col_exists('students_student', 'id'):
    exe("ALTER TABLE students_student DROP COLUMN id", "Drop broken id column")

# Now add proper id as auto-increment PK
if not has_pk('students_student'):
    exe("ALTER TABLE students_student ADD COLUMN `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST",
        "Add id auto-increment PK")
    # Ensure matricule unique index exists
    safe_drop_index('students_student', 'students_student_matricule_4d892746_uniq')
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'students_student'
        AND INDEX_NAME = 'students_student_matricule_uniq'
    """)
    if cursor.fetchone()[0] == 0:
        exe("ALTER TABLE students_student ADD UNIQUE INDEX `students_student_matricule_uniq` (`matricule`)",
            "Add unique index on matricule")

print("\n" + "=" * 60)
print("STEP 2: Migrate student_id columns from VARCHAR to BIGINT")
print("=" * 60)

for table, idx_name in [
    ('students_studentlevel', 'students_studentlevel_student_id_idx'),
    ('payments_payment', 'payments_payment_student_id_idx'),
    ('Teaching_evaluation', 'Teaching_evaluation_student_id_idx'),
]:
    print(f"\n--- {table} ---")
    # Drop old indexes on student_id
    safe_drop_index(table, f'{idx_name.replace("_idx","")}_b5fab56a_fk_students_' if 'payment' in table else '')

    if not col_exists(table, 'student_id_new'):
        if col_exists(table, 'student_id'):
            cursor.execute(f"SELECT DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME='student_id'", (table,))
            dtype = cursor.fetchone()[0]
            if dtype == 'varchar':
                exe(f"ALTER TABLE `{table}` ADD COLUMN `student_id_new` BIGINT NULL", f"Add student_id_new")
                exe(f"UPDATE `{table}` t INNER JOIN students_student s ON t.student_id = s.matricule SET t.student_id_new = s.id", f"Populate student_id_new")
                # Drop old indexes on student_id
                cursor.execute("SELECT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME='student_id' GROUP BY INDEX_NAME", (table,))
                for (idx,) in cursor.fetchall():
                    safe_drop_index(table, idx)
                exe(f"ALTER TABLE `{table}` DROP COLUMN `student_id`", f"Drop old student_id")
                exe(f"ALTER TABLE `{table}` CHANGE `student_id_new` `student_id` BIGINT NOT NULL", f"Rename student_id_new -> student_id")
            else:
                print(f"  -> student_id is already {dtype}, skipping conversion")
        else:
            print(f"  -> student_id column missing, something unexpected")
    else:
        print(f"  -> student_id_new already exists, completing rename")
        if col_exists(table, 'student_id'):
            cursor.execute("SELECT INDEX_NAME FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND COLUMN_NAME='student_id' GROUP BY INDEX_NAME", (table,))
            for (idx,) in cursor.fetchall():
                safe_drop_index(table, idx)
            exe(f"ALTER TABLE `{table}` DROP COLUMN `student_id`", f"Drop old student_id")
        exe(f"ALTER TABLE `{table}` CHANGE `student_id_new` `student_id` BIGINT NOT NULL", f"Rename")

    # Add FK + index
    cursor.execute("SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=%s AND CONSTRAINT_TYPE='FOREIGN KEY' AND CONSTRAINT_NAME LIKE '%%student_id_fk%%'", (table,))
    if cursor.fetchone()[0] == 0:
        fk_name = table.replace('students_studentlevel','students_studentleve') + '_student_id_fk_students_'
        if table == 'students_studentlevel':
            fk_name = 'students_studentleve_student_id_fk_students_'
        exe(f"ALTER TABLE `{table}` ADD CONSTRAINT `{fk_name}` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`) ON DELETE CASCADE", f"Add FK")
    exe(f"ALTER TABLE `{table}` ADD INDEX `{idx_name}` (`student_id`)" if not cursor.execute(f"SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND INDEX_NAME='{idx_name}'") or cursor.fetchone()[0] == 0 else "SELECT 1", f"Add index on student_id")

# Re-add unique_together on studentlevel
cursor.execute("SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='students_studentlevel' AND INDEX_NAME='students_studentlevel_student_level_year_uniq'")
if cursor.fetchone()[0] == 0:
    exe("ALTER TABLE students_studentlevel ADD UNIQUE INDEX `students_studentlevel_student_level_year_uniq` (`student_id`, `level_id`, `academic_year_id`)", "Add unique_together")

print("\n" + "=" * 60)
print("ALL DONE! Now run: python manage.py migrate students 0015 --fake")
print("=" * 60)

cursor.close()
conn.close()

