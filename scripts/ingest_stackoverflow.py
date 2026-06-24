"""
Ingest curated StackOverflow-style knowledge into RAG.
Covers common programming Q&A: Python, JavaScript, Git, Docker, SQL, Linux, etc.
"""
import httpx
import time

RAG_URL = "http://127.0.0.1:8003/rag/add_batch"
AUTH_KEY = "jarvis-v3.1"
CHUNK_SIZE = 1500
OVERLAP = 200

# Curated knowledge base - common programming topics and answers
KNOWLEDGE = [
    # === Python ===
    ("python_list_comprehensions", "python",
     "Python List Comprehensions\n\n"
     "List comprehension — компактный способ создания списков.\n"
     "Синтаксис: [expression for item in iterable if condition]\n\n"
     "Примеры:\n"
     "squares = [x**2 for x in range(10)]  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]\n"
     "evens = [x for x in range(20) if x % 2 == 0]  # [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]\n"
     "flat = [x for sublist in matrix for x in sublist]  # flatten 2D list\n\n"
     "Dict comprehension: {k: v for k, v in items}\n"
     "Set comprehension: {x for x in items}\n"
     "Generator expression: (x for x in items) — lazy evaluation"),

    ("python_decorators", "python",
     "Python Decorators\n\n"
     "Decorator — функция, которая принимает другую функцию и расширяет её поведение.\n\n"
     "def my_decorator(func):\n"
     "    def wrapper(*args, **kwargs):\n"
     "        print('Before')\n"
     "        result = func(*args, **kwargs)\n"
     "        print('After')\n"
     "        return result\n"
     "    return wrapper\n\n"
     "@my_decorator\n"
     "def say_hello():\n"
     "    print('Hello!')\n\n"
     "Популярные декораторы: @property, @staticmethod, @classmethod, @functools.lru_cache\n"
     "Декоратор с аргументами:需要用三层 вложенности функций"),

    ("python_asyncio", "python",
     "Python asyncio\n\n"
     "asyncio — библиотека для асинхронного I/O в Python.\n\n"
     "async def fetch(url):\n"
     "    async with aiohttp.ClientSession() as session:\n"
     "        async with session.get(url) as response:\n"
     "            return await response.text()\n\n"
     "async def main():\n"
     "    tasks = [fetch(url) for url in urls]\n"
     "    results = await asyncio.gather(*tasks)\n\n"
     "asyncio.run(main())\n\n"
     "Ключевые понятия:\n"
     "- await — ожидание coroutine\n"
     "- asyncio.gather() — параллельное выполнение\n"
     "- asyncio.create_task() — запуск в фоне\n"
     "- asyncio.Queue — очередь для communication между корутинами"),

    ("python_context_managers", "python",
     "Python Context Managers\n\n"
     "Context manager управляет ресурсами: открытие/закрытие файлов, подключения, блокировки.\n\n"
     "with open('file.txt') as f:\n"
     "    data = f.read()\n\n"
     "Свой context manager:\n"
     "class Timer:\n"
     "    def __enter__(self):\n"
     "        self.start = time.time()\n"
     "        return self\n"
     "    def __exit__(self, *args):\n"
     "        self.elapsed = time.time() - self.start\n\n"
     "Или через contextlib:\n"
     "@contextmanager\n"
     "def timer():\n"
     "    start = time.time()\n"
     "    yield\n"
     "    print(f'Elapsed: {time.time() - start}')"),

    ("python_error_handling", "python",
     "Python Error Handling\n\n"
     "try:\n"
     "    result = risky_operation()\n"
     "except ValueError as e:\n"
     "    print(f'Value error: {e}')\n"
     "except (TypeError, KeyError) as e:\n"
     "    print(f'Type/Key error: {e}')\n"
     "except Exception as e:\n"
     "    print(f'Unexpected: {e}')\n"
     "finally:\n"
     "    cleanup()\n\n"
     "User-defined exceptions:\n"
     "class AppError(Exception):\n"
     "    def __init__(self, message, code):\n"
     "        super().__init__(message)\n"
     "        self.code = code\n\n"
     "Best practices: catch specific exceptions, use finally for cleanup, "
     "don't use bare except, raise with meaningful messages"),

    ("python_type_hints", "python",
     "Python Type Hints\n\n"
     "Type hints улучшают читаемость и помогают линтерам находить ошибки.\n\n"
     "from typing import Optional, List, Dict, Union, Callable\n\n"
     "def greet(name: str, times: int = 1) -> str:\n"
     "    return (f'Hello {name}! ' * times).strip()\n\n"
     "def process(items: List[Dict[str, Union[str, int]]]) -> Optional[str]:\n"
     "    ...\n\n"
     "Python 3.10+: можно использовать встроенные типы:\n"
     "def func(items: list[dict[str, str | int]]) -> str | None:\n"
     "    ...\n\n"
     "Protocol для structural subtyping:\n"
     "from typing import Protocol\n"
     "class Drawable(Protocol):\n"
     "    def draw(self) -> None: ..."),

    # === Git ===
    ("git_basics", "git",
     "Git Basics\n\n"
     "git init — создать репозиторий\n"
     "git clone <url> — клонировать\n"
     "git add <file> — добавить в staging\n"
     "git commit -m 'message' — закоммитить\n"
     "git push origin <branch> — отправить\n"
     "git pull — получить изменения\n"
     "git status — статус\n"
     "git log --oneline — история\n"
     "git diff — изменения\n"
     "git branch <name> — создать ветку\n"
     "git checkout <branch> — переключиться\n"
     "git merge <branch> — слить\n"
     "git stash — сохранить изменения временно\n"
     "git reset --hard HEAD~1 — откатить коммит"),

    ("git_advanced", "git",
     "Git Advanced\n\n"
     "Interactive rebase: git rebase -i HEAD~5\n"
     "Cherry-pick: git cherry-pick <commit>\n"
     "Bisect: git bisect start / git bisect good / git bisect bad\n"
     "Reflog: git reflog — восстановить потерянные коммиты\n"
     "Hooks: .git/hooks/pre-commit, .git/hooks/commit-msg\n"
     "Submodules: git submodule add <url> <path>\n"
     "Worktrees: git worktree add <path> <branch>\n"
     "Aliases: git config --global alias.co checkout"),

    # === Docker ===
    ("docker_fundamentals", "docker",
     "Docker Fundamentals\n\n"
     "docker build -t myapp . — собрать образ\n"
     "docker run -p 8080:80 myapp — запустить контейнер\n"
     "docker ps — запущенные контейнеры\n"
     "docker exec -it <id> bash — войти в контейнер\n"
     "docker logs <id> — логи\n"
     "docker stop <id> — остановить\n"
     "docker-compose up -d — запустить из compose\n"
     "docker-compose down — остановить\n\n"
     "Dockerfile:\n"
     "FROM python:3.11\n"
     "WORKDIR /app\n"
     "COPY . .\n"
     "RUN pip install -r requirements.txt\n"
     "CMD [\"python\", \"main.py\"]"),

    ("docker_compose", "docker",
     "Docker Compose\n\n"
     "version: '3.8'\n"
     "services:\n"
     "  web:\n"
     "    build: .\n"
     "    ports: ['8000:8000']\n"
     "    depends_on: [db]\n"
     "    environment:\n"
     "      DATABASE_URL: postgres://user:pass@db:5432/mydb\n"
     "  db:\n"
     "    image: postgres:16\n"
     "    volumes: [pgdata:/var/lib/postgresql/data]\n"
     "    environment:\n"
     "      POSTGRES_PASSWORD: pass\n"
     "volumes:\n"
     "  pgdata:\n\n"
     "Полезные команды:\n"
     "docker-compose logs -f — следить за логами\n"
     "docker-compose exec web bash — войти в сервис\n"
     "docker-compose down -v — удалить volumes"),

    # === SQL ===
    ("sql_basics", "sql",
     "SQL Basics\n\n"
     "SELECT columns FROM table WHERE condition ORDER BY column LIMIT 10;\n"
     "INSERT INTO table (col1, col2) VALUES ('a', 'b');\n"
     "UPDATE table SET col = 'new' WHERE id = 1;\n"
     "DELETE FROM table WHERE id = 1;\n\n"
     "JOINs:\n"
     "SELECT * FROM users u JOIN orders o ON u.id = o.user_id;\n"
     "LEFT JOIN — все записи из левой таблицы\n"
     "INNER JOIN — только совпадающие\n\n"
     "GROUP BY и HAVING:\n"
     "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id HAVING COUNT(*) > 5;\n\n"
     "Индексы: CREATE INDEX idx_name ON table (column);\n"
     "Транзакции: BEGIN; ... COMMIT; / ROLLBACK;"),

    ("sql_advanced", "sql",
     "SQL Advanced\n\n"
     "CTE (Common Table Expressions):\n"
     "WITH ranked AS (\n"
     "  SELECT *, ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) as rn\n"
     "  FROM employees\n"
     ")\n"
     "SELECT * FROM ranked WHERE rn <= 3;\n\n"
     "Window functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD()\n"
     "Subqueries: SELECT * FROM t WHERE id IN (SELECT id FROM t2)\n"
     "UNION / INTERSECT / EXCEPT\n"
     "CASE WHEN condition THEN result ELSE default END\n"
     "COALESCE(a, b, c) — first non-NULL\n"
     "NULLIF(a, b) — NULL if equal"),

    # === Linux ===
    ("linux_commands", "linux",
     "Linux Commands\n\n"
     "Файлы: ls -la, cp, mv, rm -rf, mkdir, touch, chmod, chown\n"
     "Текст: cat, grep -r 'pattern' /path, sed 's/old/new/g', awk '{print $1}'\n"
     "Поиск: find /path -name '*.py', locate, which\n"
     "Процессы: ps aux, top, htop, kill -9 PID, nohup\n"
     "Сеть: curl, wget, ss -tlnp, netstat, ping, traceroute\n"
     "Диски: df -h, du -sh, mount, lsblk\n"
     "Архивы: tar -xzf file.tar.gz, zip, unzip\n"
     "Пайпы: cmd1 | cmd2, cmd > file, cmd >> file, cmd 2>&1"),

    ("linux_systemd", "linux",
     "Linux systemd\n\n"
     "Создать сервис:\n"
     "[Unit]\n"
     "Description=My App\n"
     "After=network.target\n\n"
     "[Service]\n"
     "User=www-data\n"
     "WorkingDirectory=/opt/myapp\n"
     "ExecStart=/usr/bin/python3 main.py\n"
     "Restart=always\n\n"
     "[Install]\n"
     "WantedBy=multi-user.target\n\n"
     "Команды:\n"
     "systemctl enable myapp — автозапуск\n"
     "systemctl start myapp — запустить\n"
     "systemctl status myapp — статус\n"
     "journalctl -u myapp -f — логи"),

    # === JavaScript ===
    ("javascript_async", "javascript",
     "JavaScript Async/Await\n\n"
     "async function fetchData(url) {\n"
     "  const response = await fetch(url);\n"
     "  return await response.json();\n"
     "}\n\n"
     "Promise.all — параллельное выполнение:\n"
     "const [users, posts] = await Promise.all([\n"
     "  fetch('/api/users'),\n"
     "  fetch('/api/posts')\n"
     "]);\n\n"
     "Promise.allSettled — не падает при ошибке:\n"
     "const results = await Promise.allSettled(promises);\n\n"
     "Error handling:\n"
     "try {\n"
     "  const data = await riskyOperation();\n"
     "} catch (error) {\n"
     "  console.error(error.message);\n"
     "}"),

    ("javascript_es6", "javascript",
     "JavaScript ES6+ Features\n\n"
     "Destructuring: const { name, age } = user;\n"
     "Spread: const newArray = [...oldArray, newItem];\n"
     "Rest: function fn(a, ...rest) {}\n"
     "Template literals: `Hello ${name}!`\n"
     "Arrow functions: const fn = (a, b) => a + b;\n"
     "Optional chaining: user?.address?.city\n"
     "Nullish coalescing: value ?? 'default'\n"
     "Modules: export const fn = () => {}; import { fn } from './module';\n"
     "Map/Set: new Map([['key', 'value']])\n"
     "WeakMap/WeakRef: for caching without preventing GC"),

    # === Networking ===
    ("http_status_codes", "networking",
     "HTTP Status Codes\n\n"
     "2xx Success:\n"
     "200 OK — успешный запрос\n"
     "201 Created — создан\n"
     "204 No Content — успешно, нет тела\n\n"
     "3xx Redirection:\n"
     "301 Moved Permanently —永久重定向\n"
     "304 Not Modified — кэш актуален\n\n"
     "4xx Client Error:\n"
     "400 Bad Request — невалидный запрос\n"
     "401 Unauthorized — нужна авторизация\n"
     "403 Forbidden — нет доступа\n"
     "404 Not Found — не найдено\n"
     "429 Too Many Requests — rate limit\n\n"
     "5xx Server Error:\n"
     "500 Internal Server Error\n"
     "502 Bad Gateway\n"
     "503 Service Unavailable"),

    ("rest_api_design", "networking",
     "REST API Design\n\n"
     "Ресурсы — существительные: /users, /orders, /products\n"
     "HTTP методы:\n"
     "GET /users — список\n"
     "GET /users/:id — конкретный\n"
     "POST /users — создать\n"
     "PUT /users/:id — заменить\n"
     "PATCH /users/:id — частично обновить\n"
     "DELETE /users/:id — удалить\n\n"
     "Query params: /users?page=1&limit=20&sort=-created_at\n"
     "Пагинация: { data: [...], meta: { total, page, limit } }\n"
     "Фильтрация: /users?status=active&role=admin\n"
     "Versioning: /api/v1/users"),

    # === Security ===
    ("web_security", "security",
     "Web Security Basics\n\n"
     "SQL Injection:使用 параметризованных запросов\n"
     "XSS:Escape вывод, CSP заголовки\n"
     "CSRF: токены в формах\n"
     "Authentication: JWT, OAuth 2.0, Session cookies\n"
     "Password hashing: bcrypt, argon2 (никогда MD5/SHA1)\n"
     "HTTPS: всегда использовать в продакшене\n"
     "Rate limiting: ограничение количества запросов\n"
     "Input validation: валидировать на сервере, не доверять клиенту\n"
     "Headers: X-Content-Type-Options, X-Frame-Options, CSP"),

    # === DevOps ===
    ("ci_cd_basics", "devops",
     "CI/CD Basics\n\n"
     "Continuous Integration — автоматический запуск тестов при каждом коммите.\n"
     "Continuous Delivery — автоматическая деплой в staging.\n"
     "Continuous Deployment — автоматический деплой в прод.\n\n"
     "GitHub Actions:\n"
     "name: CI\n"
     "on: [push, pull_request]\n"
     "jobs:\n"
     "  test:\n"
     "    runs-on: ubuntu-latest\n"
     "    steps:\n"
     "      - uses: actions/checkout@v4\n"
     "      - uses: actions/setup-python@v5\n"
     "      - run: pip install -r requirements.txt\n"
     "      - run: pytest\n\n"
     "Pipeline stages: build → test → lint → security scan → deploy"),

    ("terraform_basics", "devops",
     "Terraform Basics\n\n"
     "Terraform — IaC (Infrastructure as Code) от HashiCorp.\n\n"
     "resource 'aws_instance' 'web' {\n"
     "  ami           = 'ami-0c55b159cbfafe1f0'\n"
     "  instance_type = 't2.micro'\n"
     "  tags = { Name = 'web-server' }\n"
     "}\n\n"
     "Команды:\n"
     "terraform init — инициализация\n"
     "terraform plan — план изменений\n"
     "terraform apply — применить\n"
     "terraform destroy — удалить\n"
     "terraform state list — список ресурсов\n\n"
     "Modules: переиспользование конфигураций\n"
     "Backends: хранение state в S3, Consul"),

    # === Data structures ===
    ("data_structures", "algorithms",
     "Common Data Structures\n\n"
     "Array: O(1) доступ по индексу, O(n) вставка\n"
     "Linked List: O(1) вставка, O(n) доступ\n"
     "Stack: LIFO — push, pop, peek\n"
     "Queue: FIFO — enqueue, dequeue\n"
     "Hash Table: O(1) поиск, вставка, удаление\n"
     "Binary Search Tree: O(log n) поиск\n"
     "Heap: O(log n) вставка, O(1) min/max\n"
     "Graph: adjacency list или matrix\n\n"
     "Когда что использовать:\n"
     "Частый поиск по индексу → Array\n"
     "Частые вставки/удаления → Linked List\n"
     "Быстрый поиск → Hash Table\n"
     "Приоритеты → Heap\n"
     "Отсортированные данные → BST"),

    ("algorithms_common", "algorithms",
     "Common Algorithms\n\n"
     "Binary Search: O(log n) — поиск в отсортированном массиве\n"
     "Quick Sort: O(n log n) average — быстрая сортировка\n"
     "Merge Sort: O(n log n) — стабильная сортировка\n"
     "BFS: обход в ширину — поиск кратчайшего пути\n"
     "DFS: обход в глубину — поиск компонент связности\n"
     "Dynamic Programming: оптимизация через мемоизацию\n"
     "Greedy: локально оптимальные решения\n\n"
     "Big O:\n"
     "O(1) — константа\n"
     "O(log n) — логарифм\n"
     "O(n) — линейная\n"
     "O(n log n) — линейно-логарифмическая\n"
     "O(n²) — квадратичная"),
]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def send_to_rag(documents: list[dict]) -> bool:
    try:
        r = httpx.post(
            RAG_URL,
            json={"documents": documents},
            headers={"X-Auth-Key": AUTH_KEY, "Content-Type": "application/json"},
            timeout=120,
        )
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"  RAG error: {e}")
        return False


def main():
    print(f"StackOverflow-style knowledge: {len(KNOWLEDGE)} topics")
    print("=" * 60)

    total_chunks = 0
    total_topics = 0

    for name, category, text in KNOWLEDGE:
        chunks = chunk_text(text)
        documents = [
            {
                "text": chunk,
                "id": f"so_{name}_{i}",
                "metadata": {
                    "source": "stackoverflow",
                    "category": category,
                    "topic": name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]

        if send_to_rag(documents):
            total_chunks += len(chunks)
            total_topics += 1
            print(f"  [{category}/{name}] OK: {len(chunks)} chunks")
        else:
            print(f"  [{category}/{name}] FAILED")

        time.sleep(0.3)

    print("=" * 60)
    print(f"Done: {total_topics} topics, {total_chunks} chunks ingested")


if __name__ == "__main__":
    main()
