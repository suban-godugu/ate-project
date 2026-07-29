# Machine Learning (supervised)

## What this adds

- **Removal classifier** (LightGBM binary) for redundant pattern removal scores
- **Ordering ranker** (LightGBM LambdaMART) for early-fail execution order
- Optional blend into existing FastAPI services without changing response schemas
- Operator accept/reject feedback at `POST /ml/feedback`

## Pipeline

```bash
# From project root
python -m ml.scripts.build_dataset
python -m ml.scripts.train_removal
python -m ml.scripts.train_ordering
python -m ml.scripts.evaluate
```

## Enable scoring in the API

Defaults: `ml_enabled=false`, `ml_shadow_mode=true` (log ML scores, return heuristics).

```bash
set BACKEND_ML_ENABLED=true
set BACKEND_ML_SHADOW_MODE=false
set BACKEND_ML_REMOVAL_BLEND=0.7
set BACKEND_ML_ORDERING_BLEND=0.7
python -m backend.app
```

## Safety

Removal predictions with `unique_fail_contribution > 0` are forced toward keep.
