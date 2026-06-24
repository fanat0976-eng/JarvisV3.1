# PR Strategy — Рекомендации

## Когда делать PR

### Phase 1 (Core)
- **Когда:** Все тесты проходят, Docker работает, документация готова
- **Куда:** `main`分支
- **Кто:** Один мейнтейнер
- **Review:** 1-2 ревьюера

### Phase 2 (Extensions)
- **Когда:** Phase 1 замержен, все Phase 2 тесты проходят
- **Куда:** `main`分支 (через feature branch)
- **Кто:** Тот же мейнтейнер + контрибьюторы
- **Review:** 2-3 ревьюера

## Нaming Conventions

### Branches
```
feat/phase1-core
feat/phase2-extensions
feat/phase2-voice
feat/phase2-plugins
fix/brain-streaming
docs/readme-update
```

### Commits
```
feat(core): add FastAPI server with plugin system
feat(brain): add router, context, personality
feat(rag): add ChromaDB integration
feat(memory): add facts CRUD
feat(files): add sandboxed file operations
feat(web): add DuckDuckGo search
feat(tts): add edge-tts integration
feat(stt): add Whisper integration
feat(wizard): add first-run checker
feat(docker): add Dockerfile and compose
feat(dashboard): add web dashboard
feat(cli): add jarvis_cli.py
docs(readme): add full manual
test(unit): add router and personality tests
fix(brain): resolve streaming timeout
chore(ci): add GitHub Actions workflow
```

## PR Description Template

```markdown
## Summary
[1-3 sentences о чём PR]

## Changes
- [ ] Feature A
- [ ] Feature B
- [ ] Tests
- [ ] Documentation

## Testing
```bash
# Как тестировать
pytest
python core/server.py
curl http://localhost:8003/health
```

## Screenshots
[Если есть UI изменения]

## Related Issues
Fixes #123
```

## Review Checklist

### Для ревьюера
- [ ] Код читаемый и понятный
- [ ] Нет magic numbers
- [ ] Есть docstrings
- [ ] Тесты покрывают основные кейсы
- [ ] Нет security issues
- [ ] Документация актуальна
- [ ] Docker работает
- [ ] CI/CD проходит

## Post-Merge

### После merge Phase 1
- [ ] Создать GitHub Release v3.1.0-core
- [ ] Написать announcement в discussions
- [ ] Пригласить контрибьюторов

### После merge Phase 2
- [ ] Создать GitHub Release v3.1.0
- [ ] Обновить roadmap
- [ ] Написать blog post
- [ ] Запустить community plugins marketplace
