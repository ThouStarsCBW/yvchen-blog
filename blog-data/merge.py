import datetime
import glob
import json
import os
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_NAME = sys.argv[1] if len(sys.argv) > 1 else 'articles.jsonl'
PREFIX = sys.argv[2] if len(sys.argv) > 2 else '_incoming'
DATA = os.path.join(BASE, DATA_NAME)
CATS = {'生活', '技术', '随笔', '读书', '职场', '美食', '旅行', '影音'}


def load(path):
    if not os.path.exists(path):
        return []
    items = []
    with open(path, encoding='utf-8') as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f'{os.path.basename(path)} 第 {lineno} 行不是合法 JSON: {e}')
    return items


def validate(items):
    errs = []
    for it in items:
        idx = it.get('index')
        title = it.get('title', '')
        content = it.get('content', '')
        if it.get('category') not in CATS:
            errs.append(f'{idx}: 分类非法 {it.get("category")}')
        if not 15 <= len(title) <= 30:
            errs.append(f'{idx}: 标题长度 {len(title)} 不合法')
        if not 300 <= len(content) <= 520:
            errs.append(f'{idx}: 正文长度 {len(content)} 不合法')
        if content.count('\n') < 1:
            errs.append(f'{idx}: 段落数不足 2 段')
        try:
            datetime.date.fromisoformat(it.get('created_at', ''))
        except ValueError:
            errs.append(f'{idx}: 日期格式非法')
    return errs


def main():
    files = sorted(glob.glob(os.path.join(BASE, PREFIX + '*.jsonl')))
    if not files:
        print('NO_INCOMING')
        return

    existing = load(DATA)
    incoming = []
    for path in files:
        incoming.extend(load(path))
    if not incoming:
        print('INCOMING_EMPTY')
        return

    errs = validate(incoming)
    titles = {x['title'] for x in existing}
    contents = {x['content'] for x in existing}
    last_index = existing[-1]['index'] if existing else 0
    last_date = existing[-1]['created_at'] if existing else ''
    for it in incoming:
        if it['title'] in titles:
            errs.append(f"{it['index']}: 标题重复 {it['title']}")
        titles.add(it['title'])
        if it['content'] in contents:
            errs.append(f"{it['index']}: 正文重复")
        contents.add(it['content'])
        if it['index'] != last_index + 1:
            errs.append(f"{it['index']}: index 不连续，应为 {last_index + 1}")
        if last_date and it['created_at'] < last_date:
            errs.append(f"{it['index']}: 日期回退 {it['created_at']} < {last_date}")
        last_index = it['index']
        last_date = it['created_at']

    if errs:
        print('VALIDATE_FAILED')
        for e in errs:
            print(' ', e)
        sys.exit(1)

    with open(DATA, 'a', encoding='utf-8', newline='\n') as f:
        for it in incoming:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')
    for path in files:
        os.remove(path)

    all_items = existing + incoming
    total_chars = sum(len(x['title']) + len(x['content']) for x in all_items)
    print('APPENDED', len(incoming))
    print('TOTAL', len(all_items), 'LAST_INDEX', all_items[-1]['index'], 'CHARS', total_chars)
    print('CATS', dict(Counter(x['category'] for x in all_items)))


if __name__ == '__main__':
    main()