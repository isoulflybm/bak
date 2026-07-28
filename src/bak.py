#!/usr/bin/env python3
"""
bak — утилита для создания резервных .bak копий файлов.

Использование:
    bak [опции] файл1 [файл2 ...]

Опции:
    -r, --recursive    Рекурсивный обход директорий
    -n, --dry-run      Показать, что будет сделано, без реальных изменений
    -h, --help         Показать справку

Примеры:
    bak file.txt                    # file.txt -> file.txt.bak
    bak *.txt                       # все .txt файлы -> .bak копии
    bak file.txt.bak                # восстановить file.txt из file.txt.bak
    bak -r /path/to/dir             # рекурсивно для всех файлов в директории
    bak -r "dir/**/*.py"            # рекурсивно по шаблону

Логика переименования:
    - Если file.bak не существует — создаётся file.bak
    - Если file.bak существует — переименовывается в file.bak-ДДММГГ
    - Если и такой есть — в file.bak-ДДММГГ-ЧЧММСС

Логика восстановления:
    - Если передан file.txt.bak (или file.txt.bak-ДДММГГ или file.txt.bak-ДДММГГ-ЧЧММСС):
      - Текущий file.txt сохраняется как новая backup копия (со сдвигом старых)
      - file.txt восстанавливается из backup
"""

import argparse
import glob
import os
import re
import shutil
import sys
from datetime import datetime


def is_backup_file(filepath: str) -> tuple[bool, str]:
    """
    Проверяет, является ли файл backup копией.
    Возвращает (True/False, оригинальный_путь).
    
    Распознаёт форматы:
    - file.txt.bak
    - file.txt.bak-ДДММГГ
    - file.txt.bak-ДДММГГ-ЧЧММСС
    """
    patterns = [
        r'^(.+)\.bak-\d{6}-\d{6}$',  # .bak-ДДММГГ-ЧЧММСС
        r'^(.+)\.bak-\d{6}$',        # .bak-ДДММГГ
        r'^(.+)\.bak$',              # .bak
    ]
    
    for pattern in patterns:
        match = re.match(pattern, filepath)
        if match:
            return True, match.group(1)
    
    return False, filepath


def get_rotated_name(bak_path: str) -> str:
    """
    Генерирует имя для ротации существующего .bak-файла.
    Формат: .bak-ДДММГГ, а если занято — .bak-ДДММГГ-ЧЧММСС.
    """
    now = datetime.now()
    date_str = now.strftime("%d%m%y")
    time_str = now.strftime("%H%M%S")

    # Пробуем .bak-ДДММГГ
    candidate = f"{bak_path}-{date_str}"
    if not os.path.exists(candidate):
        return candidate

    # Если занято — добавляем время
    candidate = f"{bak_path}-{date_str}-{time_str}"
    return candidate


def restore_file(backup_path: str, dry_run: bool = False) -> str:
    """
    Восстанавливает оригинальный файл из backup копии.
    Текущий оригинальный файл (если существует) сохраняется как новая backup.
    """
    is_backup, original_path = is_backup_file(backup_path)
    
    if not is_backup:
        return f"⚠  '{backup_path}' не является backup файлом"
    
    if not os.path.isfile(backup_path):
        return f"⚠  Backup файл не найден: {backup_path}"
    
    msg = ""
    
    # Если оригинальный файл существует, сохраняем его как backup
    if os.path.isfile(original_path):
        bak_path = original_path + ".bak"
        if os.path.exists(bak_path):
            rotated_name = get_rotated_name(bak_path)
            if dry_run:
                msg += f"[dry-run] mv {bak_path} -> {rotated_name}\n"
            else:
                shutil.move(bak_path, rotated_name)
                msg += f"↻  {bak_path} -> {rotated_name}\n"
        
        if dry_run:
            msg += f"[dry-run] cp {original_path} -> {bak_path}\n"
        else:
            shutil.copy2(original_path, bak_path)
            msg += f"💾 Текущий {original_path} сохранён -> {bak_path}\n"
    
    # Восстанавливаем оригинальный файл из backup
    if dry_run:
        msg += f"[dry-run] cp {backup_path} -> {original_path}"
    else:
        shutil.copy2(backup_path, original_path)
        msg += f"✔  Восстановлено: {backup_path} -> {original_path}"
    
    return msg


def bak_file(filepath: str, dry_run: bool = False) -> str:
    """
    Создаёт .bak-копию одного файла или восстанавливает из backup.
    Возвращает строку с описанием выполненного действия.
    """
    is_backup, original_path = is_backup_file(filepath)
    
    # Если это backup файл — восстанавливаем
    if is_backup:
        return restore_file(filepath, dry_run=dry_run)
    
    # Иначе создаём backup копию
    if not os.path.isfile(filepath):
        return f"⚠  Пропущено (не файл): {filepath}"

    bak_path = filepath + ".bak"

    if os.path.exists(bak_path):
        rotated_name = get_rotated_name(bak_path)
        if dry_run:
            return f"[dry-run] mv {bak_path} -> {rotated_name}; cp {filepath} -> {bak_path}"
        shutil.move(bak_path, rotated_name)
        msg = f"↻  {bak_path} -> {rotated_name}\n"
    else:
        msg = ""

    if dry_run:
        return msg + f"[dry-run] cp {filepath} -> {bak_path}"

    shutil.copy2(filepath, bak_path)
    msg += f"✔  {filepath} -> {bak_path}"
    return msg


def collect_files(args, recursive: bool) -> list:
    """
    Собирает список файлов по переданным аргументам с учётом шаблонов и рекурсии.
    """
    files = []
    for arg in args:
        # Проверяем, является ли аргумент шаблоном (содержит wildcards)
        if any(ch in arg for ch in "*?["):
            matched = glob.glob(arg, recursive=recursive)
            if not matched:
                print(f"⚠  Шаблон не дал совпадений: {arg}", file=sys.stderr)
            files.extend(matched)
        elif os.path.isdir(arg) and recursive:
            for root, _, filenames in os.walk(arg):
                for fn in filenames:
                    files.append(os.path.join(root, fn))
        elif os.path.isfile(arg):
            files.append(arg)
        elif os.path.isdir(arg) and not recursive:
            print(f"⚠  '{arg}' — директория. Используйте -r для рекурсивного обхода.", file=sys.stderr)
        else:
            print(f"⚠  Файл не найден: {arg}", file=sys.stderr)

    # Убираем дубликаты, сохраняя порядок
    seen = set()
    unique = []
    for f in files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def main():
    parser = argparse.ArgumentParser(
        prog="bak",
        description="Создание резервных .bak копий файлов или восстановление из них",
        add_help=False,
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Файлы или backup копии для обработки",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Рекурсивный обход директорий",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Показать, что будет сделано, без реальных изменений",
    )
    parser.add_argument(
        "-h", "--help",
        action="help",
        help="Показать эту справку",
    )

    args = parser.parse_args()
    files = collect_files(args.files, recursive=args.recursive)

    if not files:
        print("Нет файлов для обработки.", file=sys.stderr)
        sys.exit(1)

    count = 0
    for f in files:
        msg = bak_file(f, dry_run=args.dry_run)
        print(msg)
        count += 1

    if args.dry_run:
        print(f"\n[dry-run] Всего файлов: {count}")
    else:
        print(f"\nГотово. Обработано файлов: {count}")


if __name__ == "__main__":
    main()
