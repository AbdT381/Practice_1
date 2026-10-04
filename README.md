# Practice_1
Этап 1
import os
import sys


def parse_arguments(user_input):
    """Парсит ввод пользователя и раскрывает переменные окружения."""
    # Раскрываем переменные окружения реальной ОС (например, $HOME или %USERPROFILE%)
    expanded_input = os.path.expandvars(user_input)

    # Разбиваем строку на команду и аргументы
    tokens = expanded_input.split()
    if not tokens:
        return None, []

    command = tokens[0]
    args = tokens[1:]
    return command, args


def main():
    vfs_name = "MyVFS"
    print(f"--- Добро пожаловать в {vfs_name} CLI Прототип ---")
    print("Доступные команды: ls, cd, exit. Поддерживается раскрытие переменных (например, $HOME).\n")

    while True:
        try:
            # Требование 2: Приглашение к вводу содержит имя VFS
            user_input = input(f"{vfs_name} $> ")

            # Требование 3: Парсинг и раскрытие переменных окружения
            command, args = parse_arguments(user_input)

            # Если введена пустая строка
            if not command:
                continue

            # Требование 5: Команда exit
            if command == "exit":
                if args:
                    print("Ошибка: команда 'exit' не принимает аргументы.")
                    continue
                print("Завершение работы прототипа VFS. До свидания!")
                sys.exit(0)

            # Требование 4: Команды-заглушки ls и cd
            elif command in ["ls", "cd"]:
                print(f"[Заглушка] Вызвана команда: {command}")
                print(f"[Заглушка] Аргументы: {args if args else 'нет'}")

            # Обработка неизвестных команд (Обработка ошибок)
            else:
                print(f"Ошибка: неизвестная команда '{command}'. Доступные команды: ls, cd, exit.")

        except KeyboardInterrupt:
            # Красивый выход по Ctrl+C
            print("\nПрограмма прервана пользователем. Выход.")
            sys.exit(0)
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()
