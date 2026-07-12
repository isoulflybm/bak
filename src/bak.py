#!/usr/bin/env python3
"""
bak — утилита для создания резервных .bak копий файлов.

Использование:
    bak [опции] файл1 [файл2 ...]

Опции:
    -r, --recursive    Рекурсивный обход директорий
    -h, --help         Показать справку

Примеры:
    bak file.txt                    # file.txt -> file.txt.bak
    bak *.txt                       # все .txt файлы -> .bak копии
    bak -r /path/to/dir             # рекурсивно для всех файлов в директории
    bak -r "dir/**/*.py"            # рекурсивно по шаблону

Логика переименования:
    - Если file.bak не существует — создаётся file.bak
    - Если file.bak существует — переименовывается в file.bak-ДДММГГ
    - Если и такой есть — в file.bak-ДДММГГ-ЧЧММСС
"""

import argparse
import glob
import os
import shutil
import sys
from datetime import datetime


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


def bak_file(filepath: str, dry_run: bool = False) -> str:
    """
    Создаёт .bak-копию одного файла.
    Возвращает строку с описанием выполненного действия.
    """
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
        description="Создание резервных .bak копий файлов",
        add_help=False,
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Файлы или шаблоны для резервного копирования",
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
