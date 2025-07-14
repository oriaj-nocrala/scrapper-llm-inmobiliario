# 🚀 GitHub Actions - Scrapper LLM Inmobiliario

Este directorio contiene los workflows de GitHub Actions para CI/CD, testing y automatización.

## 📁 Estructura

```
.github/
├── workflows/
│   ├── ci-cd.yml                 # Pipeline principal de CI/CD
│   ├── pr-tests.yml              # Tests para Pull Requests
│   ├── nightly-tests.yml         # Tests programados nocturnos
│   ├── release.yml               # Automatización de releases
│   ├── dependabot-auto-merge.yml # Auto-merge de dependencias
│   └── badges.yml                # Actualización de badges
├── dependabot.yml                # Configuración de Dependabot
├── ISSUE_TEMPLATE/               # Templates para issues
└── README.md                     # Esta documentación
```

## 🔄 Workflows

### 1. **ci-cd.yml** - Pipeline Principal
**Trigger**: Push a `main`/`develop`, Pull Requests
**Funcionalidad**:
- ✅ Análisis de calidad de código (flake8, black, isort, mypy)
- 🧪 Tests unitarios, integración y funcionales
- 🛡️ Análisis de seguridad (bandit, safety)
- 🐳 Construcción y tests de Docker
- 📊 Análisis de código interno (God Classes, calidad)
- 🏗️ Build y push de imagen Docker
- 🚀 Despliegue a staging/producción

### 2. **pr-tests.yml** - Tests de Pull Request
**Trigger**: Pull Requests
**Funcionalidad**:
- ⚡ Tests rápidos para feedback inmediato
- 📊 Análisis de archivos modificados
- 🐳 Tests de Docker si se modifican archivos relacionados
- 💬 Comentarios automáticos con resultados

### 3. **nightly-tests.yml** - Tests Nocturnos
**Trigger**: Cron (2:00 AM UTC), Manual
**Funcionalidad**:
- 🔗 Tests de integración completos
- ⚡ Tests de rendimiento y benchmarks
- 🔒 Análisis de seguridad profundo
- 📊 Análisis completo de código
- 🐳 Tests completos de Docker
- 📊 Reportes nocturnos

### 4. **release.yml** - Automatización de Releases
**Trigger**: Release published, Manual
**Funcionalidad**:
- ✅ Validación pre-release
- 🏗️ Construcción de imagen de release
- 🧪 Tests de release (smoke, integración, rendimiento)
- 🚀 Despliegue automático a staging/producción
- 📊 Reportes post-release

### 5. **dependabot-auto-merge.yml** - Auto-merge de Dependencias
**Trigger**: Pull Requests de Dependabot
**Funcionalidad**:
- 🤖 Auto-merge para actualizaciones menores/patch
- 📝 Comentarios para actualizaciones mayores
- 🏷️ Etiquetado automático
- 🔐 Aprobación automática de actualizaciones de seguridad

### 6. **badges.yml** - Actualización de Badges
**Trigger**: Push, Schedule, Manual
**Funcionalidad**:
- 📊 Actualización de badges de estado
- 📊 Métricas de cobertura de código
- 🔒 Estado de seguridad
- 📈 Métricas de calidad

## 🔧 Configuración

### Variables de Entorno
```bash
# Requeridas
GITHUB_TOKEN          # Token automático de GitHub
CODECOV_TOKEN          # Token de Codecov (opcional)

# Opcionales
SLACK_WEBHOOK_URL      # Para notificaciones Slack
DOCKER_REGISTRY        # Registry alternativo
```

### Secrets
```bash
# Agregar en GitHub Settings > Secrets
GITHUB_TOKEN           # Automático
CODECOV_TOKEN          # Para métricas de cobertura
SLACK_WEBHOOK_URL      # Para notificaciones
```

### Environments
```bash
# Configurar en GitHub Settings > Environments
staging                # Ambiente de pruebas
production            # Ambiente de producción
```

## 🚀 Uso

### Ejecutar Tests Manualmente
```bash
# Desde GitHub UI
Actions > [Workflow] > Run workflow

# Desde CLI
gh workflow run ci-cd.yml
gh workflow run nightly-tests.yml --ref main
```

### Crear Release
```bash
# Crear tag y release
git tag v1.0.0
git push origin v1.0.0

# Desde GitHub UI
Releases > Create a new release
```

### Configurar Dependabot
El archivo `dependabot.yml` está configurado para:
- Actualizaciones semanales los lunes
- Límites de PRs abiertas
- Auto-merge para actualizaciones menores

## 📊 Métricas y Reportes

### Artifacts Generados
- `security-reports` - Reportes de seguridad
- `code-analysis-reports` - Análisis de código
- `integration-test-results` - Resultados de tests
- `nightly-report` - Reporte nocturno
- `release-report` - Reporte de release

### Badges Disponibles
- ![CI/CD](https://github.com/repo/workflows/CI/badge.svg)
- ![Tests](https://github.com/repo/workflows/Tests/badge.svg)
- ![Coverage](https://codecov.io/gh/repo/branch/main/graph/badge.svg)
- ![Quality](https://img.shields.io/badge/quality-8.5-green)
- ![Security](https://img.shields.io/badge/security-secure-green)

## 🔍 Monitoreo

### Health Checks
- Tests automáticos en cada push
- Verificaciones de seguridad semanales
- Análisis de calidad continuo
- Monitoreo de dependencias

### Notificaciones
- Fallos en CI/CD
- Actualizaciones de seguridad
- Releases exitosos
- Reportes nocturnos

## 🛠️ Troubleshooting

### Fallos Comunes

#### 1. Tests Fallan
```bash
# Verificar localmente
pytest tests/ -v
docker build -t test .
docker run --rm test python -m pytest
```

#### 2. Docker Build Falla
```bash
# Probar build local
docker build -t scrapper-llm .
docker run --rm scrapper-llm health
```

#### 3. Dependabot No Funciona
```bash
# Verificar configuración
cat .github/dependabot.yml
# Verificar permisos en Settings > Actions
```

### Logs y Debugging
```bash
# Ver logs de workflow
gh run list
gh run view [run-id]

# Descargar artifacts
gh run download [run-id]
```

## 📚 Recursos

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Dependabot Documentation](https://docs.github.com/en/github/administering-a-repository/keeping-your-dependencies-updated-automatically)
- [Docker GitHub Actions](https://docs.docker.com/ci-cd/github-actions/)
- [Codecov GitHub Actions](https://github.com/codecov/codecov-action)

## 🤝 Contribución

Para modificar workflows:
1. Crear branch de feature
2. Modificar workflow en `.github/workflows/`
3. Probar en branch de desarrollo
4. Crear PR con descripción detallada
5. Revisar y hacer merge a main

---

**Nota**: Estos workflows están optimizados para desarrollo colaborativo y despliegue continuo. Para configuraciones específicas del proyecto, consultar con el equipo de DevOps.