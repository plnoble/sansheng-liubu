#!/usr/bin/env python3
"""
三省六部 · 看板更新 CLI v2

用法:
  # 任务管理
  python3 scripts/kanban_update.py create <id> "<title>" <state> <org> <official> "<desc>"
  python3 scripts/kanban_update.py state <id> <state> "<说明>"
  python3 scripts/kanban_update.py flow <id> "<from>" "<to>" "<remark>"
  python3 scripts/kanban_update.py done <id> "<output>" "<summary>"
  python3 scripts/kanban_update.py progress <id> "<当前在做什么>" "<计划>"
  python3 scripts/kanban_update.py todo <id> <todo_id> "<title>" <status> [--detail "<详情>"]

  # 部门日志（尚书省派发任务时自动创建）
  python3 scripts/kanban_update.py log <id> <dept> "<完成情况>" "<产出结果>" "<后续建议>"

  # 查询
  python3 scripts/kanban_update.py list [--state <状态>] [--dept <部门>]
  python3 scripts/kanban_update.py view <id>
  python3 scripts/kanban_update.py stats

  # 刑部日报
  python3 scripts/kanban_update.py daily-report [--date <YYYY-MM-DD>]

示例:
  python3 scripts/kanban_update.py create JJC-20260327-001 "分析茅台走势" Zhongshu 中书省 中书令 "太子整理旨意"
  python3 scripts/kanban_update.py state JJC-20260327-001 Doing "中书省开始执行"
  python3 scripts/kanban_update.py flow JJC-20260327-001 "太子" "中书省" "📋 旨意传达"
  python3 scripts/kanban_update.py progress JJC-20260327-001 "正在分析方案" "分析方案🔄|起草|提交审议"
  python3 scripts/kanban_update.py todo JJC-20260327-001 1 "需求整理" completed --detail "产出：xxx"
  python3 scripts/kanban_update.py done JJC-20260327-001 "<产出>" "<摘要>"

  # 部门日志
  python3 scripts/kanban_update.py log JJC-20260327-001 户部 "分析了茅台近期走势" "买入信号不明显，建议观望" "明日再看季度报"

  # 查询
  python3 scripts/kanban_update.py list --state Doing
  python3 scripts/kanban_update.py view JJC-20260327-001
  python3 scripts/kanban_update.py stats

  # 生成刑部日报
  python3 scripts/kanban_update.py daily-report
"""

import json
import sys
import os
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def green(text): return f"{Colors.GREEN}{text}{Colors.ENDC}"
    @staticmethod
    def yellow(text): return f"{Colors.YELLOW}{text}{Colors.ENDC}"
    @staticmethod
    def red(text): return f"{Colors.RED}{text}{Colors.ENDC}"
    @staticmethod
    def cyan(text): return f"{Colors.CYAN}{text}{Colors.ENDC}"
    @staticmethod
    def bold(text): return f"{Colors.BOLD}{text}{Colors.ENDC}"

KANBAN_FILE = "data/kanban.json"
LOGS_DIR = "data/logs"


def load_kanban():
    """加载看板数据"""
    if os.path.exists(KANBAN_FILE):
        with open(KANBAN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"tasks": [], "flows": [], "todos": []}


def save_kanban(data):
    """保存看板数据"""
    os.makedirs(os.path.dirname(KANBAN_FILE) if os.path.dirname(KANBAN_FILE) else ".", exist_ok=True)
    with open(KANBAN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_task(data, task_id):
    """获取任务"""
    for task in data["tasks"]:
        if task["id"] == task_id:
            return task
    return None


def get_task_flows(data, task_id):
    """获取任务的流程记录"""
    return [f for f in data["flows"] if f["id"] == task_id]


def get_task_todos(data, task_id):
    """获取任务的子任务"""
    return [t for t in data["todos"] if t["task_id"] == task_id]


def cmd_create(task_id, title, state, org, official, desc=""):
    """创建新任务"""
    data = load_kanban()

    for task in data["tasks"]:
        if task["id"] == task_id:
            print(f"{Colors.yellow('⚠️ 任务')} {task_id} {Colors.yellow('已存在，更新中...')}")
            task["title"] = title
            task["state"] = state
            task["org"] = org
            task["official"] = official
            task["desc"] = desc
            task["updated_at"] = datetime.now().isoformat()
            save_kanban(data)
            print(f"{Colors.green('✅ 任务已更新:')} {task_id}")
            return

    task = {
        "id": task_id,
        "title": title,
        "state": state,
        "org": org,
        "official": official,
        "desc": desc,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "progress": "",
        "plan": ""
    }
    data["tasks"].append(task)
    save_kanban(data)
    print(f"{Colors.green('✅ 任务已创建:')} {task_id}")
    print(f"   标题: {title}")
    print(f"   状态: {state}")
    print(f"   部门: {org} / {official}")


def cmd_state(task_id, state, desc=""):
    """更新任务状态"""
    data = load_kanban()

    task = get_task(data, task_id)
    if task:
        task["state"] = state
        if desc:
            task["desc"] = desc
        task["updated_at"] = datetime.now().isoformat()
        save_kanban(data)
        print(f"{Colors.green('✅ 状态已更新:')} {task_id} -> {Colors.cyan(state)}")
        return

    print(f"{Colors.red('❌ 任务不存在:')} {task_id}")


def cmd_flow(task_id, from_node, to_node, remark=""):
    """记录流程节点"""
    data = load_kanban()

    flow = {
        "id": task_id,
        "from": from_node,
        "to": to_node,
        "remark": remark,
        "created_at": datetime.now().isoformat()
    }
    data["flows"].append(flow)
    save_kanban(data)

    arrow = f"{Colors.cyan(from_node)} -> {Colors.cyan(to_node)}"
    print(f"{Colors.green('✅ 流程已记录:')} {arrow}")
    if remark:
        print(f"   {Colors.yellow(remark)}")


def cmd_done(task_id, output="", summary=""):
    """标记任务完成"""
    data = load_kanban()

    task = get_task(data, task_id)
    if task:
        task["state"] = "Done"
        task["output"] = output
        task["summary"] = summary
        task["updated_at"] = datetime.now().isoformat()
        save_kanban(data)
        print(f"{Colors.green('✅ 任务已完成:')} {task_id}")
        if summary:
            print(f"   摘要: {summary}")
        return

    print(f"{Colors.red('❌ 任务不存在:')} {task_id}")


def cmd_progress(task_id, current, plan=""):
    """更新任务进度"""
    data = load_kanban()

    task = get_task(data, task_id)
    if task:
        task["progress"] = current
        task["plan"] = plan
        task["updated_at"] = datetime.now().isoformat()
        save_kanban(data)
        print(f"{Colors.green('✅ 进度已更新:')} {task_id}")
        print(f"   {Colors.bold('当前:')} {current}")
        if plan:
            print(f"   {Colors.bold('计划:')} {plan}")
        return

    print(f"{Colors.red('❌ 任务不存在:')} {task_id}")


def cmd_todo(task_id, todo_id, title, status, detail=""):
    """更新子任务"""
    data = load_kanban()

    task = get_task(data, task_id)
    if not task:
        print(f"{Colors.red('❌ 任务不存在:')} {task_id}")
        return

    # 查找或创建子任务
    todo_found = False
    for todo in data["todos"]:
        if todo["task_id"] == task_id and str(todo["todo_id"]) == str(todo_id):
            todo["title"] = title
            todo["status"] = status
            if detail:
                todo["detail"] = detail
            todo["updated_at"] = datetime.now().isoformat()
            todo_found = True
            break

    if not todo_found:
        todo = {
            "task_id": task_id,
            "todo_id": int(todo_id),
            "title": title,
            "status": status,
            "detail": detail,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        data["todos"].append(todo)

    save_kanban(data)

    status_icon = "✅" if status == "completed" else "🔄" if status == "doing" else "⬜"
    print(f"{Colors.green('✅ 子任务已更新:')} {task_id} #{todo_id} {status_icon} {title}")


def cmd_log(task_id, dept, completion, result, suggestion=""):
    """记录部门工作日志"""
    os.makedirs(LOGS_DIR, exist_ok=True)

    log_file = os.path.join(LOGS_DIR, f"{dept}.json")
    logs = []

    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)

    log_entry = {
        "task_id": task_id,
        "dept": dept,
        "completion": completion,
        "result": result,
        "suggestion": suggestion,
        "created_at": datetime.now().isoformat()
    }
    logs.append(log_entry)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f"{Colors.green('✅ 日志已记录:')} [{dept}] {task_id}")
    print(f"   完成情况: {completion}")
    print(f"   产出结果: {result}")
    if suggestion:
        print(f"   后续建议: {suggestion}")


def cmd_list(state_filter=None, dept_filter=None):
    """列出任务"""
    data = load_kanban()

    tasks = data["tasks"]
    if state_filter:
        tasks = [t for t in tasks if t.get("state") == state_filter]

    if not tasks:
        print(f"{Colors.yellow('📭 没有找到任务')}")
        return

    # 按状态分组
    by_state = defaultdict(list)
    for task in tasks:
        by_state[task["state"]].append(task)

    for state, state_tasks in sorted(by_state.items(), key=lambda x: x[0]):
        state_color = Colors.green if state == "Done" else Colors.yellow if state == "Doing" else Colors.cyan
        print(f"\n{state_color(f'【{state}】')} ({len(state_tasks)}个任务)")

        for task in sorted(state_tasks, key=lambda x: x["id"]):
            updated = task["updated_at"][:10] if "updated_at" in task else "N/A"
            print(f"  {Colors.bold(task['id'])} {task['title'][:30]}")
            print(f"    部门: {task['org']} | 更新: {updated}")


def cmd_view(task_id):
    """查看任务详情"""
    data = load_kanban()

    task = get_task(data, task_id)
    if not task:
        print(f"{Colors.red('❌ 任务不存在:')} {task_id}")
        return

    print(f"\n{Colors.bold('='*50)}")
    print(f"{Colors.bold('任务ID:')} {task['id']}")
    print(f"{Colors.bold('标题:')} {task['title']}")
    print(f"{Colors.bold('状态:')} {Colors.cyan(task['state'])}")
    print(f"{Colors.bold('部门:')} {task['org']} / {task.get('official', 'N/A')}")
    print(f"{Colors.bold('创建:')} {task.get('created_at', 'N/A')[:19]}")
    print(f"{Colors.bold('更新:')} {task.get('updated_at', 'N/A')[:19]}")

    if task.get("desc"):
        print(f"{Colors.bold('描述:')} {task['desc']}")

    if task.get("progress"):
        print(f"{Colors.bold('当前进度:')} {task['progress']}")

    if task.get("plan"):
        print(f"{Colors.bold('计划:')} {task['plan']}")

    # 流程记录
    flows = get_task_flows(data, task_id)
    if flows:
        print(f"\n{Colors.bold('流程记录:')}")
        for flow in flows:
            created = flow["created_at"][:19]
            print(f"  {created} | {Colors.cyan(flow['from'])} -> {Colors.cyan(flow['to'])}")
            if flow.get("remark"):
                print(f"         {flow['remark']}")

    # 子任务
    todos = get_task_todos(data, task_id)
    if todos:
        print(f"\n{Colors.bold('子任务:')}")
        for todo in sorted(todos, key=lambda x: x["todo_id"]):
            status_icon = "✅" if todo["status"] == "completed" else "🔄" if todo["status"] == "doing" else "⬜"
            print(f"  {status_icon} #{todo['todo_id']} {todo['title']}")
            if todo.get("detail"):
                print(f"       {todo['detail'][:50]}...")

    print(f"{Colors.bold('='*50)}\n")


def cmd_stats():
    """显示统计信息"""
    data = load_kanban()

    total = len(data["tasks"])
    by_state = defaultdict(int)
    by_dept = defaultdict(int)

    for task in data["tasks"]:
        by_state[task["state"]] += 1
        by_dept[task["org"]] += 1

    print(f"\n{Colors.bold('📊 三省六部 · 看板统计')}")
    print(f"{'='*40}")

    print(f"{Colors.bold('任务总数:')} {total}")
    print(f"\n{Colors.bold('按状态:')}")
    for state, count in sorted(by_state.items()):
        pct = (count / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5)
        color = Colors.green if state == "Done" else Colors.yellow if state == "Doing" else Colors.cyan
        print(f"  {color(state):12} {count:3} ({pct:5.1f}%) {bar}")

    print(f"\n{Colors.bold('按部门:')}")
    for dept, count in sorted(by_dept.items(), key=lambda x: -x[1]):
        pct = (count / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {Colors.cyan(dept):12} {count:3} ({pct:5.1f}%) {bar}")

    print(f"{'='*40}\n")


def cmd_daily_report(target_date=None):
    """生成刑部日报"""
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    print(f"\n{Colors.bold('📋 刑部日报 ·')} {target_date}")
    print(f"{'='*50}")

    # 加载所有部门的日志
    logs_by_dept = defaultdict(list)
    os.makedirs(LOGS_DIR, exist_ok=True)

    for log_file in os.listdir(LOGS_DIR):
        if not log_file.endswith(".json"):
            continue
        dept = log_file[:-5]  # 去掉 .json
        with open(os.path.join(LOGS_DIR, log_file), "r", encoding="utf-8") as f:
            logs = json.load(f)
            # 过滤当天日志
            dept_logs = [l for l in logs if l.get("created_at", "").startswith(target_date)]
            if dept_logs:
                logs_by_dept[dept] = dept_logs

    # 加载当天任务
    data = load_kanban()
    tasks_today = []
    for task in data["tasks"]:
        created = task.get("created_at", "")
        if created.startswith(target_date):
            tasks_today.append(task)

    # 按部门汇总
    all_normal = True
    for dept in ["户部", "礼部", "兵部", "工部", "刑部"]:
        dept_logs = logs_by_dept.get(dept, [])
        dept_tasks = [t for t in tasks_today if t.get("org") == dept]

        if dept_logs or dept_tasks:
            status = Colors.green("✓") + " 正常"
            all_normal = False
        else:
            status = Colors.yellow("○") + " 无任务"

        print(f"\n{Colors.bold(dept)} {status}")
        if dept_logs:
            for log in dept_logs:
                print(f"  - {log.get('completion', '')}")
                print(f"    产出: {log.get('result', '')}")
                if log.get('suggestion'):
                    print(f"    建议: {log.get('suggestion')}")
        elif dept_tasks:
            for t in dept_tasks:
                print(f"  - {t['title']} ({t['state']})")

    # 统计
    total_tasks = len(tasks_today)
    total_logs = sum(len(logs) for logs in logs_by_dept.values())
    done_tasks = len([t for t in tasks_today if t.get("state") == "Done"])

    print(f"\n{Colors.bold('统计:')}")
    print(f"  新建任务: {total_tasks}")
    print(f"  完成任务: {done_tasks}")
    print(f"  工作日志: {total_logs}")

    print(f"\n{'='*50}")

    if all_normal:
        print(f"\n{Colors.green('【无事发生，奏报皇上】')}\n")
    else:
        print(f"\n{Colors.yellow('【有待皇上批阅之事】')}\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "create":
        if len(sys.argv) < 7:
            print("❌ 用法: create <id> <title> <state> <org> <official> <desc>")
            sys.exit(1)
        cmd_create(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7] if len(sys.argv) > 7 else "")

    elif cmd == "state":
        if len(sys.argv) < 4:
            print("❌ 用法: state <id> <state> <desc>")
            sys.exit(1)
        desc = sys.argv[4] if len(sys.argv) > 4 else ""
        cmd_state(sys.argv[2], sys.argv[3], desc)

    elif cmd == "flow":
        if len(sys.argv) < 5:
            print("❌ 用法: flow <id> <from> <to> <remark>")
            sys.exit(1)
        remark = sys.argv[5] if len(sys.argv) > 5 else ""
        cmd_flow(sys.argv[2], sys.argv[3], sys.argv[4], remark)

    elif cmd == "done":
        if len(sys.argv) < 3:
            print("❌ 用法: done <id> <output> <summary>")
            sys.exit(1)
        output = sys.argv[3] if len(sys.argv) > 3 else ""
        summary = sys.argv[4] if len(sys.argv) > 4 else ""
        cmd_done(sys.argv[2], output, summary)

    elif cmd == "progress":
        if len(sys.argv) < 4:
            print("❌ 用法: progress <id> <current> <plan>")
            sys.exit(1)
        plan = sys.argv[4] if len(sys.argv) > 4 else ""
        cmd_progress(sys.argv[2], sys.argv[3], plan)

    elif cmd == "todo":
        if len(sys.argv) < 5:
            print("❌ 用法: todo <id> <todo_id> <title> <status> [--detail <详情>]")
            sys.exit(1)
        detail = ""
        for i, arg in enumerate(sys.argv):
            if arg == "--detail" and i + 1 < len(sys.argv):
                detail = sys.argv[i + 1]
                break
        cmd_todo(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], detail)

    elif cmd == "log":
        if len(sys.argv) < 5:
            print("❌ 用法: log <id> <dept> <completion> <result> [suggestion]")
            sys.exit(1)
        suggestion = sys.argv[6] if len(sys.argv) > 6 else ""
        cmd_log(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], suggestion)

    elif cmd == "list":
        state_filter = None
        dept_filter = None
        for i, arg in enumerate(sys.argv):
            if arg == "--state" and i + 1 < len(sys.argv):
                state_filter = sys.argv[i + 1]
            if arg == "--dept" and i + 1 < len(sys.argv):
                dept_filter = sys.argv[i + 1]
        cmd_list(state_filter, dept_filter)

    elif cmd == "view":
        if len(sys.argv) < 3:
            print("❌ 用法: view <id>")
            sys.exit(1)
        cmd_view(sys.argv[2])

    elif cmd == "stats":
        cmd_stats()

    elif cmd == "daily-report":
        target_date = None
        for i, arg in enumerate(sys.argv):
            if arg == "--date" and i + 1 < len(sys.argv):
                target_date = sys.argv[i + 1]
        cmd_daily_report(target_date)

    else:
        print(f"{Colors.red('❌ 未知命令:')} {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
