# JavaScript / TypeScript recipes

Assumes `R` and `srcfiles` from `recipes-cross-stack.md` are defined.
Recipes T, M, D and H live there; this file adds only what is specific to
Next.js, NestJS, Express and their shared front-end code.

## Pitfalls first

- **Route = folder path, not file name.** Every App Router screen is
  `page.tsx`; the URL is the folders above it. `app/(shop)/orders/page.tsx`
  serves `/orders`: route groups `(x)` and slots `@x` never reach the URL.
  `[id]` is a parameter, `[...slug]` a catch-all, `[[...slug]]` optional.
- **Barrel files hide definitions.** `export * from "./nav"` in `index.ts`
  is a pointer; cite the file that holds the code.
- **Generated output.** `.next/`, `dist/`, `build/` are compiled copies;
  `srcfiles` prunes them. Never cite a hit inside them.
- **Monorepos.** Each `apps/*` is its own surface (screens, actors); set
  `R` to the app folder. `packages/*` is shared code, cited from the app
  that uses it.

## Stack detection

```bash
find "$R" -name node_modules -prune -o -name package.json -print   # one per app/package
grep -nH -E '"(next|@nestjs/core|express|fastify|react|vue|next-auth|@auth/core|@clerk/nextjs|prisma|@prisma/client|typeorm|mongoose|sequelize|zod|yup|joi|class-validator|express-validator|next-intl|i18next|react-i18next|react-intl|jest|vitest|@playwright/test|cypress)"' "$R/package.json"
```

- Next.js 13.4+ may use `app/`, any version `pages/`; both can coexist.
  Cite the `package.json` line for the stack, never for a feature: a
  dependency proves nothing until you find where it is used.

## 1. Next.js

### Screens and URLs (App Router)

```bash
find "$R" \( -name node_modules -o -name .next \) -prune -o -type d \( -name app -o -name pages \) -print
srcfiles -path "*/app/*" -name "page.*" | xargs -0 grep -nH -E "export default"
# File -> URL: drop the app/ prefix, page file, (groups) and @slots
srcfiles -path "*/app/*" -name "page.*" | xargs -0 -n1 echo \
  | sed -E 'h; s#^.*/app/##; s#page\.[a-z]+$##; s#(\([^)]*\)|@[^/]*)/##g; s#/$##; s#^#/#; G; s#^(.*)\n(.*)$#\2  ->  \1#'
srcfiles -path "*/app/*" \( -name "layout.*" -o -name "loading.*" -o -name "error.*" -o -name "not-found.*" -o -name "template.*" \) \
  | xargs -0 grep -nH -E "export default|<(p|h[1-6]|span)>"
```

- Each `page.*` is one screen at the derived URL → ✅ citing its
  `export default` line; its business name comes from its heading or menu
  label, not the folder.
- `loading`, `error`, `not-found` are screen states → quote their text ✅.
  A `layout.*` over a group often holds a shared guard; read it before
  writing "no access check".

### Route handlers and Server Actions

```bash
srcfiles -name "route.*" | xargs -0 grep -nH -E "export (async )?(function|const) (GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b"
srcfiles \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  | xargs -0 grep -nH -E "^[[:space:]]*[\"']use server[\"']"
srcfiles | xargs -0 grep -lE "^[[:space:]]*[\"']use server[\"']" | tr '\n' '\0' \
  | xargs -0 grep -nH -E "export (async function|const) [A-Za-z_]+|throw new|error:"
```

- `route.*` exports one function per HTTP method at the folder path
  (`app/api/orders/route.ts` → `POST /api/orders`) → ✅ per method.
- A Server Action is a backend operation with no URL: name it by what it
  does, cite the export, grep its name for the calling screen. Returned
  `{ error: "..." }` or thrown texts → ✅ quoted; keys → recipe M.

### Pages Router

```bash
srcfiles -path "*/pages/*" ! -path "*/pages/api/*" ! -name "_app.*" ! -name "_document.*" | xargs -0 grep -nH -E "export default"
srcfiles -path "*/pages/api/*" | xargs -0 grep -nH -E "export default|req\.method|res\.status\([0-9]+\)"
```

- `pages/orders/[id].tsx` → `/orders/[id]`; `index.tsx` → the folder URL;
  `pages/api/x.ts` → `/api/x`, every method unless a `req.method` / 405
  branch limits it → ✅. `getServerSideProps` redirects are guards.

### Middleware, auth and actors

```bash
srcfiles -name "middleware.*" | xargs -0 grep -nH -E "matcher|redirect|rewrite|NextResponse\.|cookies|headers"
srcfiles | xargs -0 grep -nH -E "Provider\(|providers:|callbacks|signIn\(|session\(|jwt\(|getServerSession|auth\(\)|clerkMiddleware|authMiddleware|currentUser|createRouteMatcher|\.protect\(" | head -60
srcfiles | xargs -0 grep -nH -E "role|isAdmin|permissions?" | grep -v -E "aria-|role=\"" | head -40
```

- `matcher` = URLs the guard covers; the redirect target = what an
  anonymous visitor gets → ✅ per path. Outside every matcher (and without
  a layout check) a screen is public.
- Each provider (Google, credentials, email link) is a sign-in way → ✅.
  A filtering `signIn` callback (domain, flag) is a rule → ✅, quoted.
- Roles copied in `session`/`jwt` callbacks are actors → 🔵 only when a
  guard or UI check also reads them; what a role means is 🟡.

## 2. NestJS

### Modules, controllers and full paths

```bash
srcfiles -name "*.ts" | xargs -0 grep -nH -E "setGlobalPrefix|enableVersioning|@Module\("
srcfiles -name "*.controller.ts" | xargs -0 grep -nH -E "@Controller\(|@(Get|Post|Put|Patch|Delete|All)\(|@Version\("
```

- Full path = global prefix + `@Controller` + method path (`api` +
  `orders` + `:id` → `GET /api/orders/:id`); cite the method line. A
  controller in no `@Module({ controllers })` is not served → 🟡, recipe D.

### Guards, roles and public routes

```bash
srcfiles -name "*.ts" | xargs -0 grep -nH -E "@UseGuards\(|@Roles\(|@Public\(|SetMetadata\(|implements CanActivate|APP_GUARD"
```

- A class guard covers every method; a method guard only that one.
  `@Roles("admin")` → ✅ "only administrators can ...". Global `APP_GUARD`
  plus `@Public()` = signed-in by default; list the exceptions ✅.

### DTO validation: limits

```bash
srcfiles -name "*.ts" | xargs -0 grep -nH -E "@(IsEmail|IsNotEmpty|IsOptional|Length|MinLength|MaxLength|Min|Max|Matches|IsEnum|IsIn|IsInt|IsPositive|ArrayMaxSize|ArrayMinSize|IsDateString|ValidateNested)\(|message:"
srcfiles -name "main.ts" | xargs -0 grep -nH -E "ValidationPipe|whitelist|forbidNonWhitelisted|transform"
```

- Each decorator → one ✅ rule with its numbers: `@Length(3, 40)` above
  `name` → "Name must be 3 to 40 characters". `message:` is the exact
  wording; without one, mark the wording 🟡.
- No `ValidationPipe` (global or `@UsePipes`) → not enforced; Gap row.

### Exceptions, filters, pipes and interceptors

```bash
srcfiles -name "*.ts" | xargs -0 grep -nH -E "throw new [A-Za-z]*(Exception|Error)\(|extends HttpException|super\(\"|HttpStatus\.[A-Z_]+"
srcfiles -name "*.ts" | xargs -0 grep -nH -E "@Catch\(|implements (ExceptionFilter|NestInterceptor|PipeTransform)|useGlobal(Filters|Interceptors|Pipes)"
```

- `NotFoundException("Order not found")` → ✅ 404 with the quoted text;
  custom subclasses carry it in `super(...)`. A filter can rewrite every
  message; read it before calling thrown text final wording.

### Entities, schemas and migrations

```bash
srcfiles -name "*.ts" | xargs -0 grep -nH -E "@Entity\(|@Column\(|@PrimaryGeneratedColumn|@(OneToMany|ManyToOne|ManyToMany|OneToOne)\(|export enum"
srcfiles -name "*.prisma" | xargs -0 grep -nH -E "^(model|enum) |@unique|@default|@relation"
srcfiles -name "*.ts" | xargs -0 grep -nH -E "@Schema\(|@Prop\(|new (mongoose\.)?Schema\(|SchemaFactory"
srcfiles \( -path "*/migrations/*" -o -path "*/prisma/migrations/*" \) | xargs -0 grep -nH -E "CREATE TABLE|ALTER TABLE|ADD COLUMN|ADD \"|DROP" | head -40
```

- Entity → business entity; constraints (`length: 40`, `@unique`,
  `required`, `maxlength`) → ✅ data rules. An enum lists states ✅;
  transitions need the code that sets the field (🔵 when 2+ sites agree).
- A column dropped by a later migration is not current; don't document it.

### Queues, schedules, events, WebSockets

```bash
srcfiles -name "*.ts" | xargs -0 grep -nH -E "@Processor\(|@Process\(|@InjectQueue\(|\.add\(\"|@Cron\(|@Interval\(|@Timeout\(|@OnEvent\(|\.emit\(\"|@WebSocketGateway|@SubscribeMessage\("
```

- `@Cron("0 2 * * *")` → ✅ "runs daily at 02:00" (server time zone unless
  `timeZone:` is set). The business reason is 🟡.
- `@InjectQueue("x")` in one repo and `@Processor("x")` in another is a
  hop → recipe H. Gateway messages are live updates; name them by what
  the user sees change.

## 3. Express

### Routers and mounted prefixes

```bash
srcfiles \( -name "*.js" -o -name "*.ts" -o -name "*.mjs" \) | xargs -0 grep -nH -E "(app|router|[a-zA-Z]+Router)\.(get|post|put|patch|delete|all|use|route)\(" | head -80
srcfiles \( -name "*.js" -o -name "*.ts" -o -name "*.mjs" \) | xargs -0 grep -nH -E "require\(\"\./routes|from \"\./routes|express\.Router\(|Router\(\)"
```

- Full path = each `app.use("/prefix", router)` down the chain + the
  router's path (`/api/v1/orders` + `/:id`). Match the `app.use` variable
  to the router file's `require`/`import` first. One `router.route()`
  can chain several methods; functions before the last handler are
  middleware (guards, validators).

### Middleware guards, validation, errors

```bash
srcfiles \( -name "*.js" -o -name "*.ts" \) | xargs -0 grep -nH -E "status\(40[13]\)|req\.user|requireAuth|requireRole|passport\.authenticate|jwt\.verify"
srcfiles \( -name "*.js" -o -name "*.ts" \) | xargs -0 grep -nH -E "Joi\.|z\.(object|string|number)|body\(\"|query\(\"|param\(\"|\.(min|max|isLength|isInt|isEmail|regex)\(|withMessage\("
srcfiles \( -name "*.js" -o -name "*.ts" \) | xargs -0 grep -nH -E "function [A-Za-z]*\(err, *req, *res, *next\)|\(err, *req, *res, *next\) *=>|res\.status\([0-9]+\)\.json\("
```

- A 401/403 branch gives the actor and exact refusal text → ✅. Validator
  chains carry limits (`isInt({ min: 1, max: 30 })` → "1 to 30" ✅) and
  `withMessage` the wording.
- The four-argument error handler decides what any uncaught error shows;
  its fallback text (`"Something went wrong"`) → ✅.

### Models

```bash
srcfiles \( -name "*.js" -o -name "*.ts" \) | xargs -0 grep -nH -E "new (mongoose\.)?Schema\(|mongoose\.model\(|sequelize\.define\(|DataTypes\.|allowNull|enum: *\[|(min|max|maxlength|required): "
```

- Read as NestJS entities (Prisma: the `*.prisma` command there). Limits
  for one field that disagree across validator, schema and model → Gap
  row citing every line.

## 4. Front-end code shared by all three

### Navigation and menus: user-visible feature names

```bash
srcfiles \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" -o -name "*.vue" \) | xargs -0 grep -nH -E "label: *\"|title: *\"|href: *\"|<Link[^>]+href=|router\.push\(" | head -60
```

- Menu labels are the features' business names → use as titles, cite the
  label line. A screen with no menu entry: find how it is reached, or 🟡.

### Forms and client-side limits

```bash
srcfiles \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" \) | xargs -0 grep -nH -E "z\.(object|string|number|enum|array)|yup\.|\.(min|max|length|email|regex|matches|required)\(|useForm\(|zodResolver|yupResolver" | head -60
```

- Client limits → ✅ rules for the screen. Client `max(25)` against server
  `@Max(20)` for one field is a conflict → Gap row citing both lines plus
  an open question; never pick one silently.
- Schema messages (`email("Enter a valid email")`) are inline wording;
  keys go through recipe M.

### Data fetching, stores, environment

```bash
srcfiles \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" \) | xargs -0 grep -nH -E "fetch\(|axios\.|useQuery\(|useMutation\(|useSWR\(|createApi\(" | head -60
srcfiles \( -name "*.tsx" -o -name "*.jsx" -o -name "*.ts" \) | xargs -0 grep -nH -E "create\(\(set|createSlice\(|configureStore\(|atom\(|defineStore\(|createContext\("
srcfiles | xargs -0 grep -nH -o -E "process\.env\.[A-Z0-9_]+|import\.meta\.env\.[A-Z0-9_]+" | sort -u -t: -k3
```

- Each backend path called → match the server route, then recipe H. Store
  actions (`clear` a cart) earn a rule only when a screen calls them.
- Env names only. `NEXT_PUBLIC_*` reaches the browser; the rest stays on
  the server. Read but missing from `.env.example` → Gap.

### i18n catalogs

```bash
srcfiles | xargs -0 grep -nH -E "next-intl|useTranslations\(|getTranslations\(|i18next|useTranslation\(|react-intl|FormattedMessage|intl\.formatMessage" | head -40
srcfiles \( -path "*/messages/*" -o -path "*/locales/*" -o -path "*/i18n/*" -o -path "*/lang/*" \) -name "*.json" | xargs -0 -n1 echo
```

- Catalogs: next-intl `messages/<locale>.json`, i18next
  `public/locales/<lng>/<ns>.json`, react-intl often `lang/`.
  `useTranslations("orders")` + `t("empty")` = key `orders.empty` → recipe M.

### Test frameworks

```bash
srcfiles \( -name "*.test.*" -o -name "*.spec.*" -o -path "*/e2e/*" -o -path "*/cypress/*" \) | xargs -0 grep -nH -E "(describe|it|test)\(\"|cy\.visit\(|page\.goto\(" | head -60
srcfiles \( -name "*.test.*" -o -name "*.spec.*" -o -path "*/e2e/*" -o -path "*/cypress/*" \) | xargs -0 grep -nH -E "\.(skip|todo|fixme|only)\(|\bx(it|describe|test)\("
```

- Jest/Vitest tests prove rules; Playwright (`page.goto`) and Cypress
  (`cy.visit`) tests prove multi-screen flows → ✅ citing the test name.
- `.skip`, `.todo`, `xit`, `test.fixme` → never ✅; 🟡 plus a Gap row
  (recipe T). `.only` means the rest of that file was not run; note it.
