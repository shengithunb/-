"""
广东省2025年高考投档数据查询工具

使用方法：
  1. 将本 exe 与 gaokao_2025_wuli.db、gaokao_2025_lishi.db 放在同一文件夹
  2. 双击运行 exe
  3. 选科目 → 输入排位范围 → 查看/导出结果

数据来源：广东省教育考试院官方投档表
"""

import sqlite3, os, sys, csv

# 数据库文件映射
DB_FILES = {
    "1": ("物理类", "gaokao_2025_wuli.db"),
    "2": ("历史类", "gaokao_2025_lishi.db"),
}


def get_base_dir():
    """获取 exe/脚本所在目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def connect_db(label, filename):
    path = os.path.join(get_base_dir(), filename)
    if not os.path.exists(path):
        print(f"  ❌ 找不到 {filename}，请确认文件在同目录下")
        return None
    conn = sqlite3.connect(path)
    total = conn.execute("SELECT COUNT(*) FROM tou_dang").fetchone()[0]
    rank_min, rank_max = conn.execute(
        "SELECT MIN(min_rank), MAX(min_rank) FROM tou_dang"
    ).fetchone()
    print(f"  ✅ {label}：共 {total} 条记录，排位范围 {rank_min:,} ~ {rank_max:,}")
    return conn


def query_by_rank(conn, r_min, r_max):
    c = conn.cursor()
    c.execute("""
        SELECT school_name, major_group, plan_count, min_score, min_rank
        FROM tou_dang
        WHERE min_rank BETWEEN ? AND ?
        ORDER BY min_rank ASC
    """, (r_min, r_max))
    return c.fetchall()


def print_table(rows, limit=20):
    if not rows:
        return
    print(f"\n{'院校名称':<30} {'专业组':<10} {'计划数':<6} {'最低分':<8} {'最低排位':<10}")
    print("-" * 70)
    for r in rows[:limit]:
        print(f"{r[0]:<30} {r[1]:<10} {r[2]:<6} {r[3]:<8} {r[4]:<10}")
    if len(rows) > limit:
        print(f"... 还有 {len(rows) - limit} 条")


def export_csv(rows, filename):
    path = os.path.join(get_base_dir(), filename)
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['院校名称', '专业组代码', '计划数', '最低分', '最低排位'])
        writer.writerows(rows)
    print(f"  ✅ 已导出到 {filename}")


def main():
    print("=" * 50)
    print("   广东省2025年高考投档数据查询工具")
    print("=" * 50)

    base = get_base_dir()
    print(f"\n📂 工作目录: {base}\n")

    # 检查数据库并连接
    conns = {}
    for key, (label, fname) in DB_FILES.items():
        conn = connect_db(label, fname)
        if conn:
            conns[key] = conn

    if not conns:
        print("\n❌ 未找到任何数据库文件，请将本程序与 .db 文件放在同一目录")
        input("\n按回车键退出...")
        return

    # 选择科目
    while True:
        print("\n📌 请选择科目：")
        for key, (label, _) in DB_FILES.items():
            status = " ✅" if key in conns else " ❌(文件缺失)"
            print(f"  {key}. {label}{status}")
        choice = input("  输入数字 (1 或 2): ").strip()
        if choice in conns:
            break
        print("  ⚠️ 请选择有效的选项")

    label = DB_FILES[choice][0]
    conn = conns[choice]

    # 输入排位范围
    print(f"\n📊 当前科目: {label}")
    print("提示：输入负数查询全部数据")
    try:
        r_min = int(input("  最低排位 (如 180000): ").strip())
        r_max = int(input("  最高排位 (如 250000): ").strip())
    except ValueError:
        print("  ❌ 请输入有效数字")
        conn.close()
        return

    if r_min < 0 or r_max < 0:
        r_min, r_max = 0, 9999999

    rows = query_by_rank(conn, r_min, r_max)
    print(f"\n✅ {label} 排位 {r_min:,} ~ {r_max:,}：共 {len(rows)} 条记录")

    if rows:
        print_table(rows)
        ans = input(f"\n💾 导出全部 {len(rows)} 条到 CSV？(y/n): ").strip().lower()
        if ans == 'y':
            fname = f"{label}_排位_{r_min}_{r_max}.csv"
            export_csv(rows, fname)

    # 关闭所有连接
    for c in conns.values():
        c.close()

    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
