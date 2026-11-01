#!/usr/bin/env bash
# Publica en GitHub los issues de esta carpeta. Omite los que ya existan.
# Requiere GitHub CLI autenticado: gh auth login
# Uso, desde la raíz del repositorio: bash docs/issues/crear_issues.sh
set -euo pipefail

cd "$(dirname "$0")"

create_label() {
  gh label create "$1" --color "$2" --description "$3" --force >/dev/null
}

create_label "modelo" "1D76DB" "Modelos de predicción"
create_label "datos" "0E8A16" "Fuentes y procesamiento de datos"
create_label "producto" "5319E7" "Dashboard y experiencia de uso"
create_label "investigación" "FBCA04" "Evaluación y preguntas abiertas"
create_label "mantenimiento" "BFDADC" "Orden del repositorio y del código"
create_label "prioridad:alta" "B60205" "Hacer primero"
create_label "prioridad:media" "D93F0B" "Hacer después de lo prioritario"
create_label "prioridad:baja" "C5DEF5" "Puede esperar"

existing="$(gh issue list --state all --limit 500 --json title --jq '.[].title')"

for file in LMX-*.md; do
  id="${file%.md}"
  title="$(sed -n 's/^title: //p' "$file" | head -n 1 | tr -d '\r')"
  labels="$(sed -n 's/^labels: //p' "$file" | head -n 1 | tr -d '\r')"

  if grep -qF "[$id]" <<<"$existing"; then
    echo "Ya existe: $title"
    continue
  fi

  tail -n +6 "$file" | gh issue create --title "$title" --label "$labels" --body-file -
done
