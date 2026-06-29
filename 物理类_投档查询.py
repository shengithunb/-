"""
广东省2025年高考物理类投档数据查询工具
1. 从PDF提取数据存入SQLite
2. 查询排位180000~250000的院校
"""

import fitz, sqlite3, re, os

# ===== 修改这里为你的实际文件路径 =====
PDF_PATH = r"广东省2025年本科普通类（物理）投档情况.pdf"
# ====================================

DB_PATH = os.path.splitext(PDF_PATH)[0] + ".db"
RESULT_FILE = "物理类_排位18万_25万.csv"


def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for page in doc:
        for line in page.get_text().split('\n'):
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def parse_records(lines):
    data_lines = []
    for line in lines:
        if any(kw in line for kw in ['院校代码', '广东省', '专业组代码', '教育考试院']):
            continue
        if re.match(r'^第\s*\d+\s*页', line):
            continue
        data_lines.append(line)

    records = []
    for i in range(0, len(data_lines) - 6, 7):
        chunk = data_lines[i:i+7]
        if len(chunk) < 7:
            break
        try:
            records.append({
                'school_code': chunk[0],
                'school_name': chunk[1],
                'major_group': chunk[2],
                'plan_count': int(chunk[3]),
                'actual_count': int(chunk[4]),
                'min_score': int(chunk[5]),
                'min_rank': int(chunk[6])
            })
        except (ValueError, IndexError):
            pass
    return records


def store_to_db(records, db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tou_dang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_code TEXT,
            school_name TEXT,
            major_group TEXT,
            plan_count INTEGER,
            actual_count INTEGER,
            min_score INTEGER,
            min_rank INTEGER
        )
    ''')
    c.execute('DELETE FROM tou_dang')
    for r in records:
        c.execute('''INSERT INTO tou_dang
            (school_code, school_name, major_group, plan_count, actual_count, min_score, min_rank)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (r['school_code'], r['school_name'], r['major_group'],
             r['plan_count'], r['actual_count'], r['min_score'], r['min_rank']))
    conn.commit()
    total = c.execute('SELECT COUNT(*) FROM tou_dang').fetchone()[0]
    conn.close()
    return total


def export_query(db_path, output_file):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT school_name, major_group, plan_count, min_score, min_rank
        FROM tou_dang
        WHERE min_rank BETWEEN 180000 AND 250000
        ORDER BY min_rank ASC
    ''')
    rows = c.fetchall()
    with open(output_file, 'w', encoding='utf-8-sig') as f:
        f.write('院校名称,专业组代码,计划数,最低分,最低排位\n')
        for r in rows:
            f.write(','.join(str(x) for x in r) + '\n')
    conn.close()
    return rows


if __name__ == '__main__':
    if not os.path.exists(PDF_PATH):
        print(f"错误：找不到PDF文件 {PDF_PATH}")
        print(f"请将PDF文件和本脚本放在同一目录，或修改 PDF_PATH 变量")
        exit(1)

    print(f"正在从PDF提取数据...")
    lines = extract_text(PDF_PATH)
    records = parse_records(lines)
    total = store_to_db(records, DB_PATH)
    print(f"已存入 {total} 条记录到 {DB_PATH}")

    rows = export_query(DB_PATH, RESULT_FILE)
    print(f"排位180000~250000共 {len(rows)} 条记录，已导出到 {RESULT_FILE}")

    input("\n按回车键退出...")
