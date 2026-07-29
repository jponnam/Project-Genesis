# Observatory UI architecture and redesign

## Current architecture

The Observatory remains a server-rendered adapter over existing research
services:

```text
Browser
  └─ /ui/* FastAPI router
      ├─ Jinja2 templates + shared macros
      ├─ lightweight static CSS/JavaScript
      ├─ storage replay/inspection
      ├─ analytics/emergence/compare
      └─ scoped scenario/campaign execution
           └─ new artifacts under CIVITAS_RUNS_DIR
```

The redesign does not change the simulation engine, event schemas, domain
systems, API contracts, or execution safety model. Existing JSONL logs remain
immutable.

## Route inventory

| Surface | Routes |
|---|---|
| Overview / runs | `/ui/`, `/ui/runs`, `/ui/runs/{run_id}` |
| Agents | `/ui/runs/{run_id}/agents/{agent_id}` |
| Compare | `/ui/compare` |
| Scenarios | `/ui/scenarios`, `/ui/scenarios/{id}` and POST `/run` |
| Campaigns | `/ui/campaigns`, `/ui/campaigns/{id}`, results and POST `/run` |
| API docs | `/docs` |

## Redesign plan

1. Establish semantic design tokens, dark/light themes, responsive shell,
   persistent desktop sidebar, mobile drawer, and accessible shared macros.
2. Turn the landing page into a real-data overview and add a dedicated,
   searchable/sortable runs catalog.
3. Rebuild run detail around summary cards, metric series, society state,
   emergence evidence, agents, and a structured event timeline.
4. Upgrade compare, scenario, campaign, and agent surfaces with consistent
   controls, feedback, empty states, and technical disclosures.
5. Verify all routes/actions at desktop and mobile widths, test keyboard/theme
   interactions, remove favicon errors, and refresh screenshots/docs.

## Design-system principles

- Neutral observability aesthetic; color conveys status, not decoration.
- CSS variables own color, typography, spacing, geometry, elevation, and
  motion.
- System sans-serif for interface text; monospace for identifiers/data.
- Semantic HTML, skip link, landmarks, captions, visible focus, and
  `prefers-reduced-motion`.
- Charts use real metric series and retain visible labels/data summaries.
- JavaScript is progressive enhancement only: navigation drawer, theme,
  search/sort, copy feedback, disclosures, and submit state.
