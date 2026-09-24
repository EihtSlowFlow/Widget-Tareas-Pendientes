#!/usr/bin/env python3
import sys
import json
import os
from models.enums import TaskStatus
from storage.database import Database
from services.task_service import TaskService
from services.filter_service import group_by_status

def main():
    db = Database()
    service = TaskService(db)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--cycle':
        task_id = int(sys.argv[2])
        service.cycle_task_status(task_id)
        
    grouped = service.get_grouped_tasks()
    subject_map = service.get_subject_names_map()
    
    result = []
    
    # We want to output in a specific order for the widget:
    # 1. In progress
    # 2. Not started
    # 3. Completed (only recent ones if possible, but let's just output all for now or limit)
    
    for status in [TaskStatus.IN_PROGRESS, TaskStatus.NOT_STARTED, TaskStatus.COMPLETED]:
        tasks = grouped.get(status, [])
        # Limit completed tasks to 3
        if status == TaskStatus.COMPLETED:
            tasks = tasks[:3]
            
        for t in tasks:
            result.append({
                "id": t.id,
                "title": t.title,
                "subject": subject_map.get(t.subject_id, "Unknown"),
                "status": status.value,
                "status_label": status.label,
                "icon": status.icon,
                "due": t.due_label if not t.is_completed else ""
            })
            
    print(json.dumps(result))
    db.close()

if __name__ == '__main__':
    main()
