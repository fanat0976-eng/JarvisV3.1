"""
Jarvis CLI — Command-line interface for Jarvis V3.1.
Plugin management, system checks, benchmarking.
"""
import sys
import io
import json
import argparse
import httpx
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = "http://127.0.0.1:8003"
AUTH_KEY = "jarvis-v3.1"


def _headers():
    return {"X-Auth-Key": AUTH_KEY, "Content-Type": "application/json"}


def _server_ok():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


# ── Plugin commands ──

def plugin_list(args):
    """List installed community plugins."""
    from core.plugin_sandbox import PluginSandbox
    sandbox = PluginSandbox()
    manifests = sandbox.discover_community()

    if not manifests:
        print("Нет установленных community-плагинов.")
        print(f"Каталог: {sandbox.COMMUNITY_DIR if hasattr(sandbox, 'COMMUNITY_DIR') else 'plugins/community'}")
        return

    print(f"{'Имя':<20} {'Версия':<10} {'Описание'}")
    print("-" * 60)
    for m in manifests:
        status = "✓" if m.enabled else "✗"
        print(f"  {status} {m.name:<18} {m.version:<10} {m.description[:40]}")


def plugin_install(args):
    """Install a community plugin."""
    from core.plugin_sandbox import PluginSandbox
    sandbox = PluginSandbox()

    source = args.source
    print(f"Установка плагина: {source}")

    if source.startswith("http"):
        ok = sandbox.install_from_url(source)
    else:
        plugin_dir = sandbox.COMMUNITY_DIR / source
        manifest_path = plugin_dir / "plugin.json"
        if manifest_path.exists():
            print(f"Плагин '{source}' уже установлен.")
            return
        ok = _install_from_registry(source, sandbox)

    if ok:
        print(f"✓ Плагин '{source}' установлен.")
    else:
        print(f"✗ Не удалось установить '{source}'.")


def _install_from_registry(name: str, sandbox) -> bool:
    registry_path = PROJECT_ROOT / "plugins" / "community" / "registry.json"
    if not registry_path.exists():
        print("Реестр не найден. Создайте plugins/community/registry.json")
        return False

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    entry = None
    for p in registry.get("plugins", []):
        if p["name"] == name:
            entry = p
            break

    if not entry:
        print(f"Плагин '{name}' не найден в реестре.")
        available = [p["name"] for p in registry.get("plugins", [])]
        if available:
            print(f"Доступные: {', '.join(available)}")
        return False

    if "url" in entry:
        return sandbox.install_from_url(entry["url"])

    plugin_dir = sandbox.COMMUNITY_DIR / name
    plugin_dir.mkdir(parents=True, exist_ok=True)

    (plugin_dir / "plugin.json").write_text(
        json.dumps(entry.get("manifest", {"name": name}), indent=2),
        encoding="utf-8",
    )

    if "handler" in entry:
        (plugin_dir / "handler.py").write_text(
            entry["handler"], encoding="utf-8"
        )

    return True


def plugin_uninstall(args):
    """Uninstall a community plugin."""
    from core.plugin_sandbox import PluginSandbox
    sandbox = PluginSandbox()

    ok = sandbox.uninstall(args.name)
    if ok:
        print(f"✓ Плагин '{args.name}' удалён.")
    else:
        print(f"✗ Плагин '{args.name}' не найден.")


def plugin_info(args):
    """Show info about a plugin."""
    from core.plugin_sandbox import PluginSandbox
    sandbox = PluginSandbox()
    plugin_dir = sandbox.COMMUNITY_DIR / args.name
    manifest_path = plugin_dir / "plugin.json"

    if not manifest_path.exists():
        print(f"Плагин '{args.name}' не найден.")
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


# ── System commands ──

def cmd_health(args):
    """Check system health."""
    if not _server_ok():
        print("✗ Сервер не запущен на порту 8003")
        return

    r = httpx.get(f"{BASE_URL}/health", headers=_headers(), timeout=10)
    d = r.json()
    print(f"✓ Сервер: v{d['version']}, плагинов: {d['plugins_loaded']}/{d['plugins_total']}")

    r = httpx.get(f"{BASE_URL}/rag/health", headers=_headers(), timeout=10)
    rag = r.json()
    print(f"✓ RAG: {rag.get('documents', 0)} документов")


def cmd_benchmark(args):
    """Run system benchmark."""
    if not _server_ok():
        print("✗ Сервер не запущен")
        return

    endpoint = "/benchmark/quick" if args.quick else "/benchmark/run"
    print(f"Запуск бенчмарка ({'быстрый' if args.quick else 'полный'})...")
    r = httpx.get(f"{BASE_URL}{endpoint}", headers=_headers(), timeout=120)
    d = r.json()

    print(f"\nРезультат: {d['passed']}/{d['total']} пройдено\n")
    for name, result in d.get("results", {}).items():
        status = "✓" if result.get("ok") else "✗"
        print(f"  {status} {name}: {result.get('message', '')}")


def cmd_wizard(args):
    """Run first-check wizard."""
    if not _server_ok():
        print("✗ Сервер не запущен")
        return

    r = httpx.get(f"{BASE_URL}/wizard/check", headers=_headers(), timeout=30)
    d = r.json()

    print(f"\nСистемная проверка: {'✓ Все ОК' if d['all_ok'] else '✗ Есть проблемы'}\n")
    for name, check in d.get("checks", {}).items():
        status = "✓" if check.get("ok") else "✗"
        print(f"  {status} {name}: {check.get('message', '')}")


def cmd_create_plugin(args):
    """Create a new community plugin skeleton."""
    from core.plugin_sandbox import COMMUNITY_DIR
    name = args.name
    plugin_dir = COMMUNITY_DIR / name

    if plugin_dir.exists():
        print(f"Плагин '{name}' уже существует.")
        return

    plugin_dir.mkdir(parents=True)

    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": args.description or f"Community plugin: {name}",
        "author": args.author or "unknown",
        "dependencies": [],
        "permissions": ["events", "cache"],
        "api_version": "1.0",
        "min_jarvis_version": "3.1",
        "enabled": True,
    }
    (plugin_dir / "plugin.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    handler = f'''"""
{name} plugin — community plugin for Jarvis V3.1.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health():
    return {{"status": "ok", "plugin": "{name}"}}


@router.get("/info")
def info():
    return {{"name": "{name}", "version": "0.1.0", "description": "TODO"}}


def on_startup():
    print("  [{name}] Started")


def on_shutdown():
    pass
'''
    (plugin_dir / "handler.py").write_text(handler, encoding="utf-8")

    print(f"✓ Плагин '{name}' создан: {plugin_dir}")
    print("  plugin.json — манифест")
    print("  handler.py  — код плагина")


# ── Main ──

def main():
    parser = argparse.ArgumentParser(
        description="J.A.R.V.I.S V3.1 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    # plugin
    plugin_p = sub.add_parser("plugin", help="Управление плагинами")
    plugin_sub = plugin_p.add_subparsers(dest="action")

    plugin_sub.add_parser("list", help="Список плагинов")
    install_p = plugin_sub.add_parser("install", help="Установить плагин")
    install_p.add_argument("source", help="Имя из реестра или URL")
    uninstall_p = plugin_sub.add_parser("uninstall", help="Удалить плагин")
    uninstall_p.add_argument("name", help="Имя плагина")
    info_p = plugin_sub.add_parser("info", help="Инфо о плагине")
    info_p.add_argument("name", help="Имя плагина")
    create_p = plugin_sub.add_parser("create", help="Создать плагин")
    create_p.add_argument("name", help="Имя плагина")
    create_p.add_argument("--description", "-d", help="Описание")
    create_p.add_argument("--author", "-a", help="Автор")

    # system
    sub.add_parser("health", help="Проверка здоровья системы")
    bench_p = sub.add_parser("benchmark", help="Системный бенчмарк")
    bench_p.add_argument("--quick", "-q", action="store_true", help="Быстрый тест")
    sub.add_parser("wizard", help="First-run проверка")

    args = parser.parse_args()

    if args.command == "plugin":
        if args.action == "list":
            plugin_list(args)
        elif args.action == "install":
            plugin_install(args)
        elif args.action == "uninstall":
            plugin_uninstall(args)
        elif args.action == "info":
            plugin_info(args)
        elif args.action == "create":
            cmd_create_plugin(args)
        else:
            plugin_p.print_help()
    elif args.command == "health":
        cmd_health(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    elif args.command == "wizard":
        cmd_wizard(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
