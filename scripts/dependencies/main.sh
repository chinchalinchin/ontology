#!/usr/bin/env bash
set -euo pipefail

OUT_DIR="docs/static/svg"
mkdir -p "${OUT_DIR}"

export PYTHONPATH="src"

echo "Generating Core Dependencies Graph..."
pydeps src/app \
  --only app.assets.base app.assets.frames.core app.assets.animations.core \
         app.game.engine app.game.screen app.game.board \
         app.game.logic.mechanics.base app.game.logic.mechanics.core.animation \
  -x 'app.game.menus*' 'app.services*' 'app.config*' 'app.models*' \
  --max-bacon=0 \
  --cluster \
  --rmprefix app. \
  --rankdir LR \
  --noshow -T svg \
  -o "${OUT_DIR}/dependencies-core.svg"

echo "Generating Core + Generators Graph..."
pydeps src/app \
  --only app.assets.base app.assets.frames.core app.assets.animations.core \
         app.game.engine app.game.screen app.game.board \
         app.game.logic.mechanics.base app.game.logic.mechanics.core.animation \
         app.services.generators.game \
  -x 'app.game.menus*' 'app.services.orchestration*' 'app.services.generators.menus*' 'app.config*' 'app.models*' \
  --max-bacon=0 \
  --cluster \
  --rmprefix app. \
  --rankdir LR \
  --noshow \
  -T svg \
  -o "${OUT_DIR}/dependencies-generators.svg"

echo "Generating Mechanics Pipeline Graph..."
pydeps src/app \
  --only app.game.logic.mechanics app.game.board app.assets.base \
  -x 'app.game.menus*' 'app.services*' 'app.config*' 'app.models*' \
  --max-bacon=0 \
  --cluster \
  --rmprefix app. \
  --rankdir LR \
  --noshow \
  -T svg \
  -o "${OUT_DIR}/dependencies-mechanics.svg"

echo "Generating Models & Boundaries Graph..."
pydeps src/app \
  --only app.models app.config app.assets.base \
  -x 'app.game*' 'app.services*' \
  --max-bacon=0 \
  --cluster \
  --rmprefix app. \
  --rankdir TB \
  --noshow \
  -T svg \
  -o "${OUT_DIR}/dependencies-models.svg"

echo "Generating Menu & Event Bus Graph..."
pydeps src/app \
  --only app.game.menus app.services.generators.menus app.game.engine app.game.screen \
  -x 'app.game.logic.mechanics*' 'app.services.generators.game*' 'app.services.orchestration*' 'app.config*' 'app.models*' \
  --max-bacon=0 \
  --cluster \
  --rmprefix app. \
  --rankdir LR \
  --noshow \
  -T svg \
  -o "${OUT_DIR}/dependencies-menus.svg"

echo "Generating Bootstrap & Orchestration Graph..."
pydeps src/app \
  --only app.services.orchestration app.services.generators app.game.engine app.game.board \
  -x 'app.config*' 'app.models*' 'app.game.logic*' 'app.game.menus.controllers*' \
  --max-bacon=0 \
  --cluster \
  --rmprefix app. \
  --rankdir LR \
  --noshow \
  -T svg \
  -o "${OUT_DIR}/dependencies-orchestration.svg"

echo "All dependency graphs successfully written to ${OUT_DIR}/"