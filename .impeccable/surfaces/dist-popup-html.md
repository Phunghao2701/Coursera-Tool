---
version: 1
slug: "dist-popup-html"
primary_target: "dist/popup.html"
related_targets: []
---

# Popup Surface Brief

## Scope and Mode

Replace the popup's visual interface while preserving its existing supported actions. Mode: Operate.

## Audience and Job

The primary user is the local extension owner, working on a Coursera course in Edge. They open the popup to choose a course action quickly.

## Action and Task

Scan the action names and activate one action in the current course tab. Settings remain a secondary action. Skip Video+ is excluded.

## Proof and Content

Use the existing action labels and settings control. Keep the active course as the context; do not add account, usage, or expiry panels.

## Constraints

Use a light Coursera-adjacent minimal style with a single blue accent and a one-column list. Preserve current action handlers and do not initiate unrelated external navigation.

## Unresolved Decisions

ChatGPT Sign in for Quiz auto-fill remains pending OpenAI partner access. The user rejected an API key path.

## Direction contract

**THESIS:** Make the active course's actions readable in one glance. Refuse the competing-card dashboard that gives every control equal weight.

**OWN-WORLD:** Use the ordered clarity of a course action sheet: white list surface, cool neutral background, thin separators, and Coursera blue for interaction.

**STORY:** The learner sees the course-tool title, recognizes the available action names, and selects one without scanning account or plan status.

**FIRST VIEWPORT:** At 340px wide, keep the title at upper left and settings at upper right; place one supporting line below; show actions as a single-column, 40px-minimum-height list.

**FORM:** Course Action Sheet, grounded direction 5 of 7; seed key `1b4db317`. The user chose a light palette and one-column action list.

**FINISH:** unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
