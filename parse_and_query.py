import sqlite3, re

# Read extracted text
with open('D:/aistock/gaokao/extracted_text.txt', 'r', encoding='utf-8') as f:
    lines = [l.strip() for l in f if l.strip()]

# Skip header lines and page headers (lines that contain Chinese header text)
data_lines = []
for line in lines:
    # Skip header lines
    if '院校代码' in line or '广东省' in line or '专业组代码' in line:
        continue
    # Skip page number lines like "第 1 页 共 67 页"
    if re.match(r'^第\s*\d+\s*页', line):
        continue
    # Skip the footer "广东省教育考试院"
    if '教育考试院' in line:
        continue
    data_lines.append(line)

# Each record is 7 lines
records = []
for i in range(0, len(data_lines) - 6, 7):
    chunk = data_lines[i:i+7]
    if len(chunk) < 7:
        break
    try:
        school_code = chunk[0]
        school_name = chunk[1]
        major_group = chunk[2]
        plan_count = int(chunk[3])
        actual_count = int(chunk[4])
        min_score = int(chunk[5])
        min_rank = int(chunk[6])
        records.append({
            'school_code': school_code,
            'school_name': school_name,
            'major_group': major_group,
            'plan_count': plan_count,
            'actual_count': actual_count,
            'min_score': min_score,
            'min_rank': min_rank
        })
    except (ValueError, IndexError) as e:
        print(f"Parse error at line {i}: {chunk[:3]}... - {e}")
        continue

print(f"Total records parsed: {len(records)}")
print(f"First 3: {records[:3]}")
print(f"Last 3: {records[-3:]}")

# Store in SQLite
conn = sqlite3.connect('D:/aistock/gaokao/gaokao.db')
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
    c.execute('''
        INSERT INTO tou_dang (school_code, school_name, major_group, plan_count, actual_count, min_score, min_rank)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (r['school_code'], r['school_name'], r['major_group'],
          r['plan_count'], r['actual_count'], r['min_score'], r['min_rank']))

conn.commit()
print(f"\nInserted {len(records)} records into SQLite.")

# Query: 广东开头学校 + 最低位次在200000~240000
print("\n" + "="*80)
print("查询：学校名称以'广东'开头 AND 最低排位在 200000~240000 之间")
print("="*80)
query = '''
    SELECT school_code, school_name, major_group, plan_count, actual_count, min_score, min_rank
    FROM tou_dang
    WHERE school_name LIKE '广东%'
      AND min_rank BETWEEN 200000 AND 240000
    ORDER BY min_rank ASC
'''
c.execute(query)
results = c.fetchall()

col_widths = [12, 30, 14, 8, 8, 12, 14]
header = ['院校代码', '院校名称', '专业组代码', '计划数', '投档人数', '最低分', '最低排位']
header_line = ' | '.join(h.ljust(w) for h, w in zip(header, col_widths))
print(header_line)
print('-' * len(header_line))

for row in results:
    formatted = ' | '.join(str(v).ljust(w) for v, w in zip(row, col_widths))
    print(formatted)

print(f"\n共 {len(results)} 条记录")

c.close()
conn.close()
