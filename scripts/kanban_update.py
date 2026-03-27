#!/usr/bin/env python3
"""
三省六部 · 看板更新 CLI

用法:
  python3 kanban_update.py create <id> "<title>" <state> <org> <official> "<desc>"
  python3 kanban_update.py state <id> <state> "<说明>"
  python3 kanban_update.py flow <id> "<from>" "<to>" "<remark>"
  python3 kanban_update.py done <id> "<output>" "<summary>"
  python3 kanban_update.py progress <id> "<当前在做什么>" "<计划>"
  python3 kanban_update.py todo <id> <todo_id> "<title>" <status> [--detail "<详情>"]

示例:
  python3 scripts/kanban_update.py create JJC-20260327-001 "分析茅台走势" Zhongshu 中书省 中书令 "太子整理旨意"
  python3 scripts/kanban_update.py state JJC-20260327-001 Doing "中书省开始执行"
  python3 scripts/kanban_update.py flow JJC-20260327-001 "太子" "中书省" "📋 旨意传达"
  python3 scripts/kanban_update.py done JJC-20260327-001 "<产出>" "<摘要>"
  python3 scripts/kanban_update.py progress JJC-20260327-001 "正在分析方案" "分析方案🔄|起草|提交审议"
  python3 scripts/kanban_update.py todo JJC-20260327-001 1 "需求整理" completed --detail "产出：xxx"
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

KANBAN_FILE = "data/kanban.json"


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


def cmd_create(task_id, title, state, org, official, desc=""):
    """创建新任务"""
    data = load_kanban()

    # 检查是否已存在
    for task in data["tasks"]:
        if task["id"] == task_id:
            print(f"⚠️ 任务 {task_id} 已存在，更新中...")
            task["title"] = title
            task["state"] = state
            task["org"] = org
            task["official"] = official
            task["updated_at"] = datetime.now().isoformat()
            save_kanban(data)
            print(f"✅ 任务已更新: {task_id}")
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
    print(f"✅ 任务已创建: {task_id}")


def cmd_state(task_id, state, desc=""):
    """更新任务状态"""
    data = load_kanban()

    for task in data["tasks"]:
        if task["id"] == task_id:
            task["state"] = state
            if desc:
                task["desc"] = desc
            task["updated_at"] = datetime.now().isoformat()
            save_kanban(data)
            print(f"✅ 状态已更新: {task_id} -> {state}")
            return

    print(f"❌ 任务不存在: {task_id}")


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
    print(f"✅ 流程已记录: {from_node} -> {to_node} [{remark}]")


def cmd_done(task_id, output="", summary=""):
    """标记任务完成"""
    data = load_kanban()

    for task in data["tasks"]:
        if task["id"] == task_id:
            task["state"] = "Done"
            task["output"] = output
            task["summary"] = summary
            task["updated_at"] = datetime.now().isoformat()
            save_kanban(data)
            print(f"✅ 任务已完成: {task_id}")
            return

    print(f"❌ 任务不存在: {task_id}")


def cmd_progress(task_id, current, plan=""):
    """更新任务进度"""
    data = load_kanban()

    for task in data["tasks"]:
        if task["id"] == task_id:
            task["progress"] = current
            task["plan"] = plan
            task["updated_at"] = datetime.now().isoformat()
            save_kanban(data)
            print(f"✅ 进度已更新: {task_id}")
            print(f"   当前: {current}")
            if plan:
                print(f"   计划: {plan}")
            return

    print(f"❌ 任务不存在: {task_id}")


def cmd_todo(task_id, todo_id, title, status, detail=""):
    """更新子任务"""
    data = load_kanban()

    # 确保任务的todos列表存在
    task_found = False
    for task in data["tasks"]:
        if task["id"] == task_id:
            task_found = True
            if "todos" not in task:
                task["todos"] = []
            break

    if not task_found:
        print(f"❌ 任务不存在: {task_id}")
        return

    # 查找或创建子任务
    todo_found = False
    for todo in data["todos"]:
        if todo["task_id"] == task_id and todo["todo_id"] == todo_id:
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
            "todo_id": todo_id,
            "title": title,
            "status": status,
            "detail": detail,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        data["todos"].append(todo)

    save_kanban(data)
    print(f"✅ 子任务已更新: {task_id} #{todo_id} -> {status}")


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

    else:
        print(f"❌ 未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
