---
name: fixing-accessibility
description: Use while implementing or observing interactive web UI to check accessible names, semantic controls, keyboard behavior, focus, forms, dialogs, and state announcements against the task's requirements.
---

# Accessible interaction

Use native buttons, links, labels, inputs, and tables where they express the required behavior. Give every interactive control an accessible name; an icon-only control needs an explicit name and decorative icons should be hidden from the accessibility tree. Keep labels and field errors associated with inputs, and expose invalid and required states.

Check the actual keyboard path: Tab reaches controls in a useful order, focus stays visible, Enter or Space activates the relevant control, Escape closes an applicable overlay, and focus returns to its trigger. A modal keeps focus inside while open. Custom grids, tabs, menus, and comboboxes need the roles and state attributes required by their behavior. Loading, errors, and changed states must be perceivable beyond color or a transient toast.

Use the task's exact accessible names and state requirements when specified. Inspect the rendered accessibility tree and operate the control; reading markup alone cannot show whether the interaction works. Prefer a targeted fix at the failing control over broad UI rewrites.
