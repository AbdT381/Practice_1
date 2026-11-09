'''!/usr/bin/env python3 '''
"""Эмулятор shell с VFS (Вариант №1, этапы 1-3)."""

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass, field


@dataclass
class VFSNode:
    path: str
    is_dir: bool
    content: str = ""
    children: dict = field(default_factory=dict)


class VFS:
    """Виртуальная файловая система в памяти."""

    def __init__(self, name: str = "VFS"):
        self.name = name
        self.root = VFSNode("/", True)
        self.cwd = "/"

    @classmethod
    def default(cls) -> "VFS":
        vfs = cls("default")
        vfs._add("/", True, "")
        vfs._add("/home", True, "")
        vfs._add("/home/user", True, "")
        vfs._add("/home/user/file.txt", False, "Hello, VFS!")
        return vfs

    @classmethod
    def from_csv(cls, path: str, name: str = "VFS") -> "VFS":
        vfs = cls(name)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                if len(row) < 2:
                    raise ValueError(f"Некорректная строка CSV: {row}")
                p, typ = row[0], row[1]
                content = row[2] if len(row) > 2 else ""
                if content.startswith("base64:"):
                    import base64
                    content = base64.b64decode(content[7:]).decode("utf-8", errors="replace")
                vfs._add(p, typ == "dir", content)
        return vfs

    def _add(self, path: str, is_dir: bool, content: str):
        parts = [p for p in path.split("/") if p]
        node = self.root
        for part in parts:
            if part not in node.children:
                node.children[part] = VFSNode(part, True)
            node = node.children[part]
        node.is_dir = is_dir
        node.content = content

    def _resolve(self, path: str) -> str:
        if not path:
            return self.cwd
        if path.startswith("/"):
            base = path
        else:
            base = os.path.normpath(os.path.join(self.cwd, path))
        # нормализация
        return "/" + "/".join(p for p in base.split("/") if p)

    def _get_node(self, path: str) -> VFSNode | None:
        if path == "/":
            return self.root
        node = self.root
        for part in [p for p in path.split("/") if p]:
            if not node.is_dir or part not in node.children:
                return None
            node = node.children[part]
        return node

    def list_dir(self, path: str) -> list[str]:
        node = self._get_node(self._resolve(path))
        if node is None:
            raise FileNotFoundError(f"Нет такого пути: {path}")
        if not node.is_dir:
            raise NotADirectoryError(f"Не каталог: {path}")
        return sorted(node.children.keys())

    def change_dir(self, path: str):
        resolved = self._resolve(path)
        node = self._get_node(resolved)
        if node is None:
            raise FileNotFoundError(f"Нет такого пути: {path}")
        if not node.is_dir:
            raise NotADirectoryError(f"Не каталог: {path}")
        self.cwd = resolved


class Emulator:
    def __init__(self, vfs: VFS, script: str | None = None):
        self.vfs = vfs
        self.script_path = script
        self.running = True

    # ---------- Этап 1: парсер с раскрытием переменных ----------
    def expand_vars(self, text: str) -> str:
        pattern = re.compile(r"\$(?:\{(\w+)\}|(\w+))")

        def repl(m):
            name = m.group(1) or m.group(2)
            return os.environ.get(name, "")

        return pattern.sub(repl, text)

    def tokenize(self, line: str) -> list[str]:
        # простой парсер с поддержкой кавычек
        tokens = []
        current = []
        quote = None
        for ch in line:
            if quote:
                if ch == quote:
                    quote = None
                else:
                    current.append(ch)
            elif ch in ("'", '"'):
                quote = ch
            elif ch.isspace():
                if current:
                    tokens.append("".join(current))
                    current = []
            else:
                current.append(ch)
        if current:
            tokens.append("".join(current))
        return tokens

    # ---------- Команды ----------
    def cmd_ls(self, args: list[str]):
        path = args[0] if args else ""
        try:
            items = self.vfs.list_dir(path)
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"ls: {e}", file=sys.stderr)
            return 1
        if not items:
            return 0
        print("  ".join(items))
        return 0

    def cmd_cd(self, args: list[str]):
        if not args:
            self.vfs.cwd = "/"
            return 0
        try:
            self.vfs.change_dir(args[0])
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"cd: {e}", file=sys.stderr)
            return 1
        return 0

    def cmd_exit(self, args: list[str]):
        self.running = False
        return 0

    def cmd_conf_dump(self, args: list[str]):
        print(f"vfs={self.vfs.name}")
        print(f"cwd={self.vfs.cwd}")
        print(f"script={self.script_path or ''}")
        return 0

    def cmd_echo(self, args: list[str]):
        print(" ".join(args))
        return 0

    def dispatch(self, line: str) -> int:
        line = self.expand_vars(line.strip())
        if not line:
            return 0
        tokens = self.tokenize(line)
        if not tokens:
            return 0
        cmd, args = tokens[0], tokens[1:]
        handlers = {
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "exit": self.cmd_exit,
            "conf-dump": self.cmd_conf_dump,
            "echo": self.cmd_echo,
        }
        handler = handlers.get(cmd)
        if handler is None:
            print(f"{cmd}: команда не найдена", file=sys.stderr)
            return 1
        return handler(args)

    # ---------- Этап 2: стартовый скрипт ----------
    def run_script(self):
        if not self.script_path:
            return 0
        try:
            with open(self.script_path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            print(f"Ошибка чтения скрипта: {e}", file=sys.stderr)
            return 1
        for line in lines:
            line = line.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            print(f"{self.vfs.name}> {line}")
            rc = self.dispatch(line)
            if rc != 0:
                print(f"Скрипт остановлен с ошибкой (код {rc})", file=sys.stderr)
                return rc
        return 0

    # ---------- REPL ----------
    def repl(self):
        while self.running:
            try:
                line = input(f"{self.vfs.name}> ")
            except EOFError:
                break
            self.dispatch(line)


def parse_args(argv):
    p = argparse.ArgumentParser(description="Shell Emulator (Вариант №1)")
    p.add_argument("--vfs", help="Путь к CSV-файлу VFS")
    p.add_argument("--script", help="Путь к стартовому скрипту")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.vfs:
        vfs = VFS.from_csv(args.vfs, name=os.path.basename(args.vfs))
    else:
        vfs = VFS.default()

    # Этап 2: отладочный вывод параметров при запуске
    print(f"[DEBUG] vfs={args.vfs or '<default>'}")
    print(f"[DEBUG] script={args.script or '<none>'}")

    emu = Emulator(vfs, args.script)
    if args.script:
        rc = emu.run_script()
        if rc != 0:
            return rc
        # после скрипта — интерактивный режим
    emu.repl()
    return 0


if __name__ == "__main__":
    sys.exit(main())
