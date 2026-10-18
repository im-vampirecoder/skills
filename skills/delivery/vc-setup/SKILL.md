---
name: vc-setup
description: Configure this repo's tracker connection, submodule layout and repo source, and story tag for the vc workflow. Also protects secrets (deny rules plus a PreToolUse hook in .claude/settings.json) and, on Azure DevOps, saves the team's members for sprint capacity. Run once per tracking repo before any other /vc:* skill. `vc-setup secure` adds only the secret protection to an existing repo; `vc-setup members` refreshes the saved team members. `vc-setup reinit` re-clones the configured submodule repos after a fresh checkout, without touching the config. `vc-setup migrate` one-time-moves old specs/ task-breakdown output into the current per-feature tasks/ layout.
---

# Setup

Configure `.vc/config.toml` for this tracking repo. Every other `/vc:*`
skill reads this file, so run this one first.

## Workflow

0. **Resolve the mode**
   - Parse `$ARGUMENTS` for a leading `reinit`, `migrate`, `secure`, or
     `members` token. `reinit` → go to **Reinit Mode** below. `migrate` →
     go to **Migrate Mode** below. `secure` → run step 7 (Protect secrets)
     only, then stop. `members` → go to **Members Mode** below. None →
     continue with step 1 as normal.

1. **Check for an existing config**
   - If `.vc/config.toml` already exists, print its current contents and
     ask via `AskUserQuestion` what to do, in this order: "Reinitialize —
     re-clone the configured submodule repos (a fresh checkout doesn't
     bring the gitignored submodule folder along)" (Recommended), "Update
     specific fields", "Reconfigure from scratch". Reinitialize routes to
     **Reinit Mode** below; updating specific fields jumps straight to the
     relevant step below; reconfiguring from scratch continues with step 2.
     A config with no `[[team_members]]` (Azure DevOps) or a repo with no
     secret protection in `.claude/settings.json` → also offer those steps
     (`members` / `secure` mode do the same on their own). An Azure
     DevOps config with no `feature_closed_state`, or a repo with no
     `docs/glossary.md` → also offer the Feature closed state question
     (step 2's state table) and the glossary (step 6).
   - Setup before v1.11.1 wrote `submodule_root` under `[ado]` and
     `cloned` under `[repos.ado]` / `[repos.github]`, where no reader
     finds them. If the existing config has either, show the fix (move
     `submodule_root` to the top level, `cloned` into `[repos]`, values
     unchanged) and apply it once the user confirms, whatever option
     they pick above.

2. **Choose the issue tracker**
   - Ask which tracker this project uses: Azure DevOps, GitHub, Linear, or
     Local (files only).
   - Only Azure DevOps has a working sync implementation right now
     (`vc-sync-to-tracker` / `vc-sync-to-ado`). If the user picks
     GitHub, Linear, or Local, say so plainly: "Only Azure DevOps syncs
     today — I'll save your choice, but sync-to-tracker won't do anything
     for this tracker yet." Save the choice anyway, so the field is
     already set once support lands.
   - If Azure DevOps: ask only for the organization name, then fetch
     everything else from Azure DevOps instead of asking the user to type
     it - typed project, area, and iteration names are the usual source
     of mismatches. The CLI check below comes first, since the fetches
     need it. Then, in order:
     1. **Project.** List the organization's projects and let the user
        pick one with `AskUserQuestion` (one project → use it and say so;
        more than 4 → show a numbered list and ask for the number):
        ```bash
        az devops project list --org https://dev.azure.com/<organization> \
          --query "value[].name" -o tsv
        ```
        If the call fails (wrong organization name, no access), report
        the error and ask for the organization again; only if the user
        says listing is not allowed for them, fall back to asking for
        the project name by hand.
     2. **Team**, then **area path** and **iteration path**: chosen after
        the team below, because the team supplies the defaults.
     Never ask the user to type an area or iteration path. Offer only
     values that exist in the project, so a typo cannot reach the config.
   - Do not ask for a default parent epic/feature. `vc-sync-to-tracker`
     always parents a story to its own feature's epic (synced in the
     same run), never to a statically configured work item — there's
     nothing to collect here.
     Check the CLI is ready:
     ```bash
     az account show >/dev/null 2>&1 || echo "not logged in"
     az extension show --name azure-devops >/dev/null 2>&1 || echo "azure-devops extension missing"
     ```
     If not logged in, tell the user to run `az login` themselves — this
     skill never handles credentials and must not attempt login on their
     behalf. If the extension is missing, tell them to run
     `az extension add --name azure-devops`. Report the check results;
     don't run either fix yourself.
   - Check whether the `azure-devops-cli` skill is installed, globally or
     locally:
     ```bash
     ls ~/.claude/skills 2>/dev/null | grep -i azure-devops-cli
     ls ~/.claude/plugins 2>/dev/null | grep -i azure-devops-cli
     ls .claude/skills 2>/dev/null | grep -i azure-devops-cli
     ```
     `vc-sync-to-tracker`'s exact `az boards` / `az devops invoke`
     command syntax depends on this skill being present, so treat it as
     required, not optional, for the Azure DevOps tracker. If none of
     the checks find it, tell the user it's required and ask them to
     confirm before installing it — do not run the install command
     without an explicit yes:
     ```
     npx -y skills@latest add https://github.com/github/awesome-copilot --skill azure-devops-cli
     ```
     Only run it after the user confirms. If they decline, stop this
     step and tell them Azure DevOps sync won't work correctly without
     it — don't silently continue as if it were optional.
   - **Detect the story-level work item type.** A project's process
     template decides whether the story level is called "User Story"
     (Agile), "Product Backlog Item" (Scrum), or something else (e.g.
     "Requirement" for CMMI) — `vc-sync-to-tracker` needs the exact
     name to create story-level work items, and guessing wrong 404s the
     create call. Query it directly rather than assuming:
     ```bash
     az devops invoke \
       --area wit --resource workitemtypes \
       --route-parameters project="<project>" \
       --org https://dev.azure.com/<organization> \
       --api-version 7.1 \
       --http-method GET \
       --query "value[].name" -o tsv
     ```
     Match the returned names against `User Story` and `Product Backlog
     Item` — the two names covering Agile and Scrum, the common cases:
     - Exactly one of the two present → use it, and tell the user which
       one was detected.
     - Neither present (a custom or CMMI-based process) → show the full
       list of returned names and ask the user directly via
       `AskUserQuestion` which one represents the story level — never
       guess.
     - Both present (an unusual custom process) → ask the user directly
       which one to use.
     Store the resolved name as `story_work_item_type` under `[ado]` in
     step 6's config.
   - **Choose the team.** `vc-plan-sprint-candidates` reads the
     team's sprints (iterations) and backlog iteration. List the teams:
     ```bash
     az devops team list --project "<project>" \
       --org https://dev.azure.com/<organization> --query "[].name" -o tsv
     ```
     One team → use it and say so. Several → ask which one plans its
     sprints in this repo (default `<project> Team`). Store it as `team`
     under `[ado]`.
   - **Choose the area path and iteration path.** Fetch them from the
     project and the chosen team; never ask the user to type them.
     - Area paths - the project's tree, flattened:
       ```bash
       az boards area project list --project "<project>" --depth 6 \
         --org https://dev.azure.com/<organization> -o json
       ```
     - Iteration paths - same, for iterations:
       ```bash
       az boards iteration project list --project "<project>" --depth 6 \
         --org https://dev.azure.com/<organization> -o json
       ```
     - The team's defaults (its backlog areas, default and backlog
       iteration), used to order the choices and mark the likely one:
       ```bash
       az devops invoke --area work --resource teamsettings \
         --route-parameters project="<project>" team="<team>" \
         --org https://dev.azure.com/<organization> \
         --api-version 7.1 --http-method GET -o json
       az devops invoke --area work --resource teamfieldvalues \
         --route-parameters project="<project>" team="<team>" \
         --org https://dev.azure.com/<organization> \
         --api-version 7.1 --http-method GET -o json
       ```
     - Normalise each node `path` to the form work items use: drop the
       leading `\` and the structure segment (`Area` / `Iteration`), so
       `\MyProject\Area\Backend` becomes `MyProject\Backend`. The
       tree root alone is the project name itself. Store exactly the
       normalised string, never a hand-edited one.
     - **Area path:** the team's own areas (`teamfieldvalues`) come first
       and the team's default is marked Recommended; offer them via
       `AskUserQuestion`, with "Show all areas" listing the rest of the
       tree as a numbered table. Store as `area_path`.
     - **Iteration path:** offer "Team default" (store `""`, so Azure
       DevOps falls back to the team's default iteration) first and
       Recommended, then the team's backlog iteration and its sprints
       from the tree. Store as `iteration_path`.
     - A fetch that fails or returns nothing (permissions, an empty
       tree) → report which one, and only then fall back to asking the
       user to type the value; say it was not verified against Azure
       DevOps.
   - **Save the team members.** Sprint capacity is planned per person
     (`vc-plan-sprint-candidates`' capacity file), so keep the team's
     roster here. List the members of the chosen team:
     ```bash
     az devops team list-member --team "<team>" --project "<project>" \
       --org https://dev.azure.com/<organization> \
       --query "[].identity.{name: displayName, id: id}" -o json
     ```
     Show them as a numbered table (name, id) and ask via
     `AskUserQuestion`: "Save all" (Recommended), "Leave some out", or
     "Don't save". Leave some out → ask which, by number or name. Groups
     and service accounts in the list (no person behind them) are
     suggested for leaving out. Store the kept ones as `[[team_members]]`
     entries (`name`, `id`) in step 6's config. Never store an email
     address, token, or anything beyond name and id.
   - **Choose the sprint states for stories and bugs, and the Feature
     closed state.** Three skills move work items between states, and
     process templates name them differently, so the user picks them once
     here: `vc-sync-to-tracker` pushes `ready` (set by `vc-prd-clarify` /
     `vc-tasks-breakdown`, or by hand for a bug) as the ready state,
     `vc-plan-sprint-candidates` only proposes items in it,
     `vc-implement` moves a story to the active state when work starts,
     and `vc-sync-to-tracker` moves a feature whose PRD is `delivered`
     to the Feature closed state.
     - List the `Feature` type's states the same way, for the last
       question below.
     - Check the `Bug` type exists in the type list fetched above (the
       Basic process has none; it uses `Issue`). Present → store
       `bug_work_item_type = "Bug"`; absent → show the list and ask which
       type holds bugs, or "None" (store `""` and skip the bug questions).
     - List each type's states, in workflow order, with their category:
       ```bash
       az devops invoke \
         --area wit --resource workItemTypeStates \
         --route-parameters project="<project>" type="<work item type>" \
         --org https://dev.azure.com/<organization> \
         --api-version 7.1 \
         --http-method GET \
         --query "value[].[name, category]" -o tsv
       ```
     - Show the user each type's states, then ask via `AskUserQuestion`,
       one question per item below, offering that type's states as the
       options (most likely first; `Other` covers a state not shown):

       | Question | Stored under `[ado]` | Likely answer | Also offer |
       |---|---|---|---|
       | Which story state means "ready for a sprint"? | `ready_state` | a `Proposed` state after the first: `Ready`, Scrum's `Approved` | "No ready state" |
       | Which story state means "work has started"? | `active_state` | the first `InProgress` state: Agile's `Active`, Scrum's `Committed` | - |
       | Which bug state means "ready for a sprint"? | `bug_ready_state` | as for stories (Scrum bug: `Approved`) | "No ready state" |
       | Which Feature state means "delivered"? | `feature_closed_state` | the first `Completed` state: Agile's `Closed`, Scrum's `Done` | - |

     - "No ready state" (e.g. Agile's `User Story` and `Bug` go straight
       from `New` to `Active`) → store `""` and tell the user: `ready` then
       lives in the local files only, and a process admin can add a
       custom `Ready` state (Proposed category) and re-run `/vc:setup`.
     - Never pick a state for the user, even when only one fits.

3. **Choose the submodule subfolder**
   - Ask what subfolder code repos should be pulled into as git
     submodules (default: `src`).
   - Create the folder (`mkdir -p <folder>`) and add it to `.gitignore`,
     so an empty placeholder directory doesn't need a tracked file to
     exist. Do not add any submodule yourself — `git submodule add` is
     entirely the user's own step, outside this skill's scope.
   - Note for the user: because the folder is gitignored, adding a
     submodule under it later will require `git submodule add -f`
     (git otherwise refuses to add a path inside an ignored directory).

4. **Choose the story tag**
   - Ask what tag(s) synced stories should carry in the tracker, so
     they're identifiable as vc-managed work items. More than one is
     fine — accept a comma-separated list (e.g. `vc, backlog`).
   - Store it as typed, comma-separated: `story = "vc,backlog"` in
     the config below. Trim whitespace around each tag, but don't split
     it into a TOML array — `vc-sync-to-tracker` reads it as one
     comma-separated string and converts it to Azure DevOps' own `; `
     tag delimiter at sync time.

5. **Choose repository source, select repos, and pull them**
   - Do this last, after every other question in this skill has been
     answered. Everything in this step — the access checks, the repo
     listing, and the clones themselves — is slow and network-dependent,
     so it shouldn't gate or get tangled up with the rest of setup: if
     it fails partway, everything else the user already answered should
     still be intact.
   - Ask where the submodule repos are hosted: Azure DevOps, GitHub, or
     None. If None, skip the rest of this step entirely.
   - **Azure DevOps:**
     - If the tracker chosen in step 2 is already Azure DevOps, ask
       whether the repos live in that same organization/project before
       prompting for new values.
     - Ask for the organization, and fetch its projects as in step 2 for the
       user to pick from, rather than asking for a typed project name.
     - Verify access and fetch the repo list in one call:
       ```bash
       az repos list --organization "https://dev.azure.com/<org>" \
         --project "<project>" \
         --query "[].{name:name, url:remoteUrl}" -o table
       ```
       If this fails, report it and stop this step — tell the user to
       check `az login` and their project permissions; don't attempt to
       fix access yourself.
   - **GitHub:**
     - Ask for the organization or user account the repos belong to.
     - Verify access and fetch the repo list:
       ```bash
       gh auth status
       gh repo list <owner> --limit 200 --json name,url
       ```
       If `gh auth status` fails, tell the user to run `gh auth login`
       themselves — this skill never handles credentials on the user's
       behalf.
   - **List and select:** use real checkbox multi-select for this —
     the `AskUserQuestion` tool with `multiSelect: true` — never a
     typed free-text answer. `AskUserQuestion` caps a single question
     at 4 options, so do it in two stages:
     1. **Coarse gate** (one question, 3 options): **All** (every
        fetched repo), **None** (nothing — same effect as choosing
        None for repo hosting above; the rest of this step becomes a
        no-op), or **Choose specific repos**. This keeps the two
        common answers to one screen regardless of how many repos were
        fetched.
     2. **Batched checkboxes** (only if "Choose specific repos" was
        picked): split the fetched repos into batches of 3. Each batch
        becomes one question in the `AskUserQuestion` call, offering
        those 3 repos as checkboxes plus a 4th standing option, **All
        remaining repos**, so the user isn't forced to page through
        every batch. `AskUserQuestion` allows up to 4 questions per
        call, so pack up to 4 batches (12 repos) into a single call —
        the user answers all of them in one submission instead of one
        screen per batch. Only issue a second call, packed the same
        way, if more than 4 batches remain. If any batch's "All
        remaining repos" is checked, select every repo not yet shown
        (in addition to anything else checked across that same call)
        and stop — skip issuing further calls. Otherwise union
        everything checked across every batch and every call into the
        final selection.
     - If nothing ends up selected, skip the rest of this step.
   - **Clone** (access to each host was already verified above when
     listing repos — no separate authorization step, and nothing here
     ever writes to git's global credential store): for each selected
     repo, clone it as its own background task (a background `Bash`
     call or a dispatched subagent) so multiple repos clone in parallel:
     - GitHub: `gh repo clone <owner>/<repo-name> <submodule_root>/<repo-name>`
       — uses the already-authenticated `gh` session for just this call.
     - Azure DevOps: scope the credential to this one invocation with
       `-c`, never `--global`, so nothing persists after the clone:
       ```bash
       git -c credential."https://dev.azure.com".helper='!f() { echo username=az; echo "password=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)"; }; f' \
         clone <clone-url> <submodule_root>/<repo-name>
       ```
       This only works for Microsoft Entra ID (AAD)-backed
       organizations. If a clone still fails auth, tell the user to
       install Git Credential Manager or supply a PAT themselves —
       don't collect, store, or configure a credential helper on their
       behalf, even if the user offers to.
     This is a plain clone, not `git submodule add` — turning it into
     an actual submodule stays the user's own later step, same as the
     note in step 3. Wait for every clone job to finish, and note by
     name any that failed — the config written next should only list
     the repos that actually succeeded.

6. **Write the config**
   - Create the `.vc/` folder if it doesn't exist, and write
     `.vc/config.toml`:
     ```toml
     tracker = "azure-devops"
     submodule_root = "src"

     [ado]
     organization = "..."
     project = "..."
     area_path = "..."
     iteration_path = ""
     story_work_item_type = "User Story"
     team = "<project> Team"
     ready_state = ""
     active_state = "Active"
     bug_work_item_type = "Bug"
     bug_ready_state = ""
     feature_closed_state = "Closed"

     [repos]
     source = "azure-devops"
     cloned = ["service-a", "service-b"]

     [repos.ado]
     organization = "..."
     project = "..."

     [tags]
     story = "vc,backlog"

     [[team_members]]
     name = "Anna de Vries"
     id = "6f1c...-...-..."

     [[team_members]]
     name = "Ravi Patel"
     id = "a93e...-...-..."
     ```
   - Omit the `[ado]` section entirely if a different tracker was chosen
     — there's nothing to configure for it yet.
   - Omit `[repos]` entirely if None was chosen for repo hosting in
     step 5. Use `[repos.github]` with an `owner` field instead of
     `[repos.ado]` when the repos are on GitHub. `cloned` lists the repo
     names actually cloned in step 5, not just selected.
   - Key placement matters: in TOML every key after a `[table]` header
     belongs to that table. `submodule_root` is a top-level key, so it
     goes before `[ado]`; `cloned` belongs to `[repos]`, so it goes
     before `[repos.ado]` / `[repos.github]`. Every other skill reads
     them as top-level `submodule_root` and `[repos].cloned`.
   - `[[team_members]]` goes last (TOML array tables must follow the plain
     keys); omit it when no members were saved.
   - **Create the glossary.** If `docs/glossary.md` doesn't exist, copy
     `assets/glossary-template.md` to it (create `docs/` if needed) and
     tell the user it holds the project's domain terms, edited by hand,
     and that `vc-docs` and `vc-prd` will propose new terms as a diff
     for them to approve. If it already exists, leave it exactly as it
     is, even when it doesn't match the template. Runs for every tracker.

7. **Protect secrets**
   - Add deny rules for secret files and a PreToolUse hook that blocks
     commands which would print a secret, to the tracking repo's shared
     `.claude/settings.json`. Runs for every tracker. Full procedure,
     including the merge, confirmation, and hook test:
     `references/protect-secrets.md`.
   - The user can decline; say plainly that the agent can then read
     `.env` files and print secrets in this repo.

8. **Confirm**
   - Print the final config back to the user and confirm it looks right
     before finishing. Congratulate them — setup is done, and every
     other `/vc:*` skill can now read this config.

## Members Mode (`vc-setup members`)

Refreshes `[[team_members]]` in an existing `.vc/config.toml` - for a
new joiner, someone leaving, or a repo set up before members were saved.
Azure DevOps only: another tracker → say there is nothing to fetch and
offer to type the names in by hand (no `id` then).

1. Read `[ado]` (`organization`, `project`, `team`). Missing → tell the
   user to run `/vc:setup` first and stop.
2. Fetch the members with the command in step 2's "Save the team members".
3. Show the difference against the saved list: new in ADO, no longer in
   ADO, unchanged. Ask once which changes to apply (add the new, remove
   the gone, both, or none).
4. Rewrite only the `[[team_members]]` entries, keeping the rest of the
   file as it is, and print the saved list.

## Reinit Mode (`vc-setup reinit`)

Re-clones this tracking repo's configured submodule repos after a fresh
checkout — `git clone`/`git pull` never brings the gitignored submodule
folder along, so a teammate picking up an already-configured repo needs
this instead of the full interactive setup. Reached via step 0's `reinit`
token, or offered as the recommended option in step 1 when
`.vc/config.toml` already exists. Writes nothing to
`.vc/config.toml` — the config is already correct; this mode only
fills in the gitignored working directory it points to.

1. **Read the submodule configuration**
   - Require `.vc/config.toml` to exist — if it doesn't, tell the user
     there's nothing to reinitialize and to run `/vc:setup` (no
     arguments) instead.
   - Read `submodule_root`, `[repos].source`, the matching
     `[repos.ado].organization`/`.project` or `[repos.github].owner`, and
     `[repos].cloned` — this is the exact set of repos to pull, no
     re-asking which ones. A config written before v1.11.1 may hold them
     as `[ado].submodule_root` and `[repos.ado].cloned` /
     `[repos.github].cloned`; read those as a fallback, and tell the user
     that `/vc:setup` (no arguments) moves them to the right place.
   - No `[repos]` section, or an empty `cloned` list → tell the user this
     config never had any submodule repos configured, stop.

2. **Verify access**
   - Azure DevOps source: `az account show >/dev/null 2>&1 || echo "not logged in"`.
     Not logged in → tell the user to run `az login` themselves, stop.
   - GitHub source: `gh auth status`. Fails → tell the user to run
     `gh auth login` themselves, stop.
   - Same rule as the main flow: never handle credentials on the user's
     behalf, only check and report.

3. **Create the submodule root folder**
   - `mkdir -p <submodule_root>` if it doesn't already exist — it's
     already gitignored from the original setup's step 3, tracked in
     `.gitignore`, so nothing else to do here.

4. **Clone**
   - Same per-host clone mechanics as the main flow's step 5's own Clone
     step — `gh repo clone` for GitHub, a `-c`-scoped (never `--global`)
     credential helper for Azure DevOps. Nothing here ever writes to
     git's global credential store.
   - For each repo in `cloned` not already present at
     `<submodule_root>/<repo-name>` (skip ones that already exist — a
     partial reinit, or a repo the user already cloned by hand, is never
     clobbered), spawn its own background clone job so multiple repos
     pull in parallel. Construct the clone target from the stored
     org/project (Azure DevOps) or owner (GitHub) and the repo name —
     same shape as the main flow's step 5. Wait for every job to finish.

5. **Report**
   - List repos cloned, repos already present (skipped), and repos that
     failed, plus the submodule root path.

## Migrate Mode (`vc-setup migrate`)

One-time move of `vc-tasks-breakdown` output from the old flat
`specs/<feature-slug>/story-<n>-<short-description>/` layout into the
current `<feature folder>/tasks/` layout (`artifacts/<feature-slug>/`
for an unassigned feature, `artifacts/epic-<epic-slug>/feature-<feature-slug>/`
for an assigned one). Reached only via step 0's `migrate` token — a standalone
operation, not part of the configure-then-confirm flow above.

1. Find every `specs/<feature-slug>/story-<n>-<short-description>/`
   folder. None found → tell the user there's nothing to migrate, stop.
2. For each, resolve its feature's current folder by globbing
   `artifacts/epic-*/feature-<feature-slug>/`, then
   `artifacts/<feature-slug>/` (unassigned) — the feature-slug is
   already known from the old path itself. No match → skip that folder
   and report it rather than guessing one.
3. Build the move plan: old `task-<m>-*.md` files →
   `<feature folder>/tasks/story-<n>-task-<m>-<task-slug>.md`;
   old `spec.md` → `<feature folder>/tasks/story-<n>-spec.md`.
4. **Show the full move plan and confirm before touching anything** —
   never move files silently, same rule `vc-propose-epic` follows for
   its own folder moves.
5. On confirmation: `git mv` each file (creating the destination
   `tasks/` folder first if it doesn't exist yet), preserving history —
   never a plain filesystem move on a tracked file. Frontmatter (`id`,
   `story_id`, `ado_id`, `last_synced`) travels with the file untouched;
   only the path and filename change.
6. Delete each now-empty old `story-<n>-.../` folder, then the
   `specs/<feature-slug>/` folder once every story under it has moved,
   then `specs/` itself once every feature's folder under it is gone.
   Leave anything unexpected in place (a file that isn't a `task-*.md`
   or `spec.md`) and flag it rather than deleting blindly.
7. Report: folders migrated, files moved, anything skipped or flagged.

Re-running when nothing is left under the old layout: report there's
nothing to migrate and stop — same idempotent-safe rule step 1 above
follows for the normal config flow.

## Notes

- Outside Reinit and Migrate Mode, this skill writes only
  `.vc/config.toml`, an empty `docs/glossary.md` when none exists
  (step 6, never overwritten), and creates the submodule subfolder from
  step 3, plain-cloning repos into it (step 5) as the very last thing it
  does before writing the config. It never touches `artifacts/` or runs `git
  submodule add` itself; turning a cloned repo into an actual submodule
  stays the user's own step. Reinit Mode only creates the submodule
  subfolder and clones into it, never writing `.vc/config.toml`.
  Migrate Mode is the other deliberate exception — it moves files
  between `specs/` and `artifacts/`, nothing else.
- It never collects, stores, or enters a credential on the user's
  behalf, and never writes to git's global credential store — step 5's
  Clone step (and Reinit Mode's own step 4) only checks the user's
  existing `az`/`gh` login and, for Azure DevOps, scopes a token to the
  single clone invocation via `git -c`, never `--global`.
- Re-running is always safe: step 1 always shows current values before
  anything changes, and Reinit Mode skips any repo already present at
  its target path instead of clobbering it.
