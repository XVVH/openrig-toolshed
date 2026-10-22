# openrig-toolshed

A community [OpenRig](https://github.com/mvschwarz/openrig) rig. `toolshed` is a fork of
`openrig-world`'s [`workshop`](https://github.com/mvschwarz/openrig-world/tree/main/rigs/workshop)
bundle (pinned at `47388ef`, 2026-10-21) — same four seats (`orch-lead`, `dev-build`, `dev-review`,
`dev-qa`), same permissions and culture.

Not upstreamed to `openrig-world` on purpose — kept as an independent community rig so it can
diverge.

## What's different from `workshop`

Adds a `prototype-before-ask` skill (a port of [pstack](https://github.com/cursor/plugins/tree/main/pstack)'s
`Prototype` playbook, behavioral/timing half only — no visual decisions in v1) on both the
`lead` and `builder` profiles, plus one inserted line in each of
`guidance/lead.md` and `guidance/builder.md`: before asking the person about a "which approach"
fork, classify it first. A fact observable by running something is settled by a throwaway
script and reported as a decision + evidence, not asked as a question. A genuine product or
preference call still goes to the person.

See [`rigs/toolshed/`](rigs/toolshed/) for the installable bundle and its own README.

## Install

```sh
rig bundle install https://github.com/XVVH/openrig-toolshed/tree/main/rigs/toolshed \
  --preset recommended --target ~/rigs/toolshed --cwd . --plan
```

Drop `--plan` to install and launch.

## Status

Scaffolded from `workshop` (2026-10-21). `prototype-before-ask` lives at
[`rigs/toolshed/agents/toolshed/bundle-skills/prototype-before-ask/`](rigs/toolshed/agents/toolshed/bundle-skills/prototype-before-ask/)
and is selected by the `lead` and `builder` profiles in `agent.yaml`; the
classify-before-ask line is in `guidance/lead.md` ("Scope the work") and
`guidance/builder.md` ("Make the change"). Pi profiles (`all-pi`) do not select
it yet.
