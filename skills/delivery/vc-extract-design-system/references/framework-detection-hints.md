# Framework Detection Hints

Loaded by `vc-extract-design-system` step 0 and by `vc-ui-scout`.
These are hints for finding things fast, not a list of supported
stacks. If a project uses something not listed, read its manifest and
entry point and work out the same four things: where styles live, where
components live, where routes are declared, and how navigation happens.

## Is it a web frontend?

Look in each submodule's manifests and top-level files:

| Signal | Likely stack |
|---|---|
| `package.json` depending on `react`, `next`, `vue`, `nuxt`, `@angular/core`, `svelte`, `@sveltejs/kit`, `solid-js`, `astro`, `lit` | JS/TS web frontend |
| `*.csproj` with `Microsoft.AspNetCore.Components`, `.razor` files | Blazor |
| `*.cshtml` with `_Layout.cshtml` | ASP.NET MVC / Razor Pages |
| `templates/` with Jinja/Django/Twig/ERB/Blade files and a static folder | Server-rendered web |
| `pubspec.yaml`, `app.json` + `react-native`, `.xcodeproj`, `AndroidManifest.xml`, MAUI `*.csproj` | Mobile — out of scope |

A backend-only submodule (API, workers, infra) is skipped silently.

## Where to look, by concern

### Tokens
- CSS custom properties in global stylesheets (`:root { --... }`,
  `[data-theme=...]` blocks for extra themes).
- SCSS/Less variable and map files (`_variables.scss`, `_tokens.scss`,
  `theme.less`).
- Theme objects passed to a UI library provider (`createTheme(...)`,
  `extendTheme(...)`, `ThemeProvider`, Angular Material/PrimeNG theme
  files, Vuetify config).
- Utility-framework config (`tailwind.config.*`, `uno.config.*`,
  `@theme` blocks in CSS).
- Design-token files (`tokens.json`, `*.tokens.json`, Style Dictionary
  config).
- Breakpoints often sit in a media-query helper or the framework config.

### Components
- Folders named `components/`, `shared/`, `ui/`, `common/`, `design-system/`,
  `lib/ui`, Storybook stories (`*.stories.*`) — stories are the best
  source of variants and states when they exist.
- Wrappers around a UI library (e.g. an app `Button` around a library
  button) count as the app's component; record the library underneath.

### Routes (screens)
- File-based routing: `pages/`, `app/` (`page.*`, `layout.*`),
  `routes/`, `src/routes/+page.*`.
- Config-based routing: route arrays/objects (`createBrowserRouter`,
  `RouterModule.forRoot`, `Routes` constants, Vue Router `routes`).
- Blazor `@page "/..."`; Razor Pages folder structure; MVC controller
  actions returning views.
- Guards: route guards, middleware, `canActivate`, `[Authorize]`,
  role checks wrapping a route or layout.

### Flows (navigation)
- Link components and `href`s, programmatic navigation calls
  (`navigate(...)`, `router.push(...)`, `NavigationManager.NavigateTo`),
  redirects, menu/sidebar config arrays, and navigation after form
  submission or a mutation's success handler.

## Running the app

The project's README, `package.json` scripts (`dev`, `start`, `serve`),
`launchSettings.json`, or `docker-compose.yml` usually say how. Suggest the
command to the user; never start long-running servers without asking.
