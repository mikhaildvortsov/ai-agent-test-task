"""Сделки amoCRM без задач или с просроченными задачами (тестовое задание CityCar).

Подставьте SUBDOMAIN и ACCESS_TOKEN. Код не запускался против реальной amoCRM:
логика find_problem_deals проверена на тестовых данных.
"""
import time

import requests

BASE = "https://SUBDOMAIN.amocrm.ru/api/v4"
HEADERS = {"Authorization": "Bearer ACCESS_TOKEN"}
CLOSED = {142, 143}  # системные статусы amoCRM: успешно / не реализовано


def fetch_all(path, key, params=None):
    """Постранично читает список из amoCRM. Ответ 204 = данных больше нет."""
    page, items = 1, []
    while True:
        r = requests.get(f"{BASE}/{path}", headers=HEADERS, timeout=30,
                         params={**(params or {}), "page": page, "limit": 250})
        if r.status_code == 204:
            return items
        r.raise_for_status()
        items += r.json()["_embedded"][key]
        page += 1
        time.sleep(0.15)  # лимит amoCRM: 7 запросов в секунду


def find_problem_deals(deals, tasks, now):
    by_deal = {}
    for t in tasks:
        by_deal.setdefault(t["entity_id"], []).append(t)
    result = []
    for d in deals:
        open_tasks = by_deal.get(d["id"], [])
        if not open_tasks:
            result.append({"deal_id": d["id"], "problem": "no_tasks"})
        elif any(t["complete_till"] < now for t in open_tasks):
            result.append({"deal_id": d["id"], "problem": "overdue_task"})
    return result


def deals_without_or_overdue_tasks():
    deals = [d for d in fetch_all("leads", "leads") if d["status_id"] not in CLOSED]
    tasks = fetch_all("tasks", "tasks",
                      {"filter[entity_type]": "leads", "filter[is_completed]": 0})
    return find_problem_deals(deals, tasks, int(time.time()))


if __name__ == "__main__":
    for item in deals_without_or_overdue_tasks():
        print(item)
