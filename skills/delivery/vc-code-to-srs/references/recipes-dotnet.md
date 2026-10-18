# .NET recipes (ASP.NET Core)

Assumes `R` and `srcfiles` from `recipes-cross-stack.md` are defined; its
rules and recipes T, M, D, H still apply. One extra helper, C# sources
without generated files:

```bash
csfiles() { srcfiles -name "*.cs" ! -name "*.Designer.cs" ! -name "*.g.cs" ! -name "*.g.i.cs" "$@"; }
```

## Stack and version

```bash
srcfiles \( -name "*.csproj" -o -name "Directory.Build.props" -o -name "Directory.Packages.props" -o -name "global.json" \) | xargs -0 grep -nH -E "<TargetFrameworks?>|Sdk=|\"version\"|<PackageReference|<PackageVersion"
csfiles -name "Program.cs" | xargs -0 grep -nH -E "Add(Controllers|RazorPages|RazorComponents|ServerSideBlazor|SignalR|MediatR|DbContext|Authentication|Authorization|HostedService|HttpClient|RefitClient|MassTransit|Hangfire|Quartz|FeatureManagement|ProblemDetails)|Use[A-Z][A-Za-z]*\(|Map[A-Z][A-Za-z]*\("
```

- `TargetFramework` and `Sdk=` (`.Web` = web app, `.Worker` = background
  service) go in the report header ✅. Package names pick which sections
  below to run; versions are context, not requirements.
- `Program.cs` (or `Startup.cs`) is the wiring map: registered = live. A
  handler class never registered is 🟡 (recipe D).

## Endpoints: controllers and minimal APIs

```bash
csfiles | xargs -0 grep -nH -E "^\s*\[(Route|Http(Get|Post|Put|Patch|Delete)|ApiController|Area)\b|class [A-Za-z]+Controller\b"
csfiles | xargs -0 grep -nH -E "\bclass [A-Za-z]+Controller\b" | grep -E "partial"
csfiles | xargs -0 grep -nH -E "\.Map(Get|Post|Put|Patch|Delete|Methods|Group|Hub|Fallback[A-Za-z]*)\("
```

- Route = class `[Route]` prefix + method template, cite both lines:
  `[Route("api/[controller]")]` on `OrdersController` + `[HttpPost("{id}/refund")]`
  = `POST api/orders/{id}/refund`. `[controller]` = class name minus
  `Controller`; bare `[HttpPost]` = the prefix; a template starting `/`
  or `~/` ignores it; no `[Route]` at all = `MapControllerRoute`.
- `partial` controllers spread actions over files; read every file the
  second command lists before saying a feature has no endpoint.
- `MapGroup("/api/v2/orders")` prefixes every `Map*` on the returned
  variable (follow it into extension methods), and its
  `.RequireAuthorization()` applies to all of them.
- One endpoint = one requirement candidate in business words ("a manager
  refunds an order"); the route appears only in the citation.

## Screens: Razor Pages, MVC views, Blazor

```bash
srcfiles \( -name "*.cshtml" -o -name "*.razor" \) | xargs -0 grep -nH -E "^@page|^@attribute|^@model|^@inject"
csfiles -name "*.cshtml.cs" | xargs -0 grep -nH -E "public .* On(Get|Post|Put|Delete)[A-Za-z]*(Async)?\("
```

- Each `@page` is a screen ✅ (no route string = folder path under
  `Pages/`). MVC views (`Views/<Controller>/<Action>.cshtml`) belong to
  the action of the same name.
- `OnPostConfirm` = a `Confirm` form handler, one user action. Blazor
  handlers live in `@code { }` or a `.razor.cs` partial.

## Authorization: actors and roles

```bash
srcfiles \( -name "*.cs" -o -name "*.razor" \) ! -name "*.Designer.cs" | xargs -0 grep -nH -E "\[Authorize|\[AllowAnonymous|RequireAuthorization|AllowAnonymous\(\)|AddPolicy\(|RequireRole\(|RequireClaim\(|IsInRole\("
```

- `Roles = "Customer,Manager"` = either role ✅. A policy is not an
  actor: resolve `Policy = "CanRefund"` to its `AddPolicy` line, cite both.
- Class `[Authorize]` covers every action, method `[AllowAnonymous]`
  overrides it, stacked ones must all pass. A `FallbackPolicy` makes
  everything private by default: check it before calling one public.
- Plain `[Authorize]` = "any signed-in user" ✅; who those users are is 🟡
  unless a role or claim says so.

## Validation: business rules with real limits

```bash
csfiles | xargs -0 grep -nH -E "\[(Required|StringLength|MaxLength|MinLength|Range|RegularExpression|EmailAddress|Phone|Url|Compare|CreditCard)\b|ErrorMessage(ResourceName)? *="
csfiles | xargs -0 grep -nH -E "AbstractValidator<|RuleFor\(|WithMessage\(|WithErrorCode\(|\.(NotEmpty|NotNull|MaximumLength|MinimumLength|Length|InclusiveBetween|ExclusiveBetween|GreaterThan(OrEqualTo)?|LessThan(OrEqualTo)?|Matches|Must|MustAsync)\("
```

- State the limit as written: `[StringLength(100, MinimumLength = 2)]` =
  "2 to 100 characters" ✅; `[Range(1, 20)]` = "1 to 20 inclusive" ✅.
  Stacked attributes (`[EmailAddress, MaxLength(254)]`) are each a rule.
- A limit held in a constant (`OrderLimits.MaxItems`): cite the rule line
  and the constant line (next section).
- `ErrorMessage = "..."` / `WithMessage("...")` is the wording ✅, with
  placeholders (`{MaxValue}`) kept. A resource key
  (`ErrorMessageResourceName`, `L["..."]`) goes through recipe M.
- `Must(BeEven)` hides the rule in a method: cite its body. Quote a regex
  as is; its plain meaning is 🔵 at best.

## Constants and options

```bash
csfiles | xargs -0 grep -nH -E "\bconst [A-Za-z<>]+ [A-Za-z_]+ *=|static readonly [A-Za-z<>]+ [A-Za-z_]+ *=" | head -60
csfiles | xargs -0 grep -nH -E "IOptions(Snapshot|Monitor)?<|Configure<|GetSection\(|\.Bind\(|GetValue<"
srcfiles -name "appsettings.json" | xargs -0 grep -nH -E "^\s*\"[A-Za-z0-9_:.-]+\" *:" | sed -E 's/(: *"[^"]*" *:).*/\1/'
```

- A `const` or `static readonly` used by a rule is a hard limit ✅.
- An `IOptions<T>` property is configurable: "a configurable maximum
  (setting `Orders:MaxOpenOrders`)" ✅; the value per environment is 🟡.
  The third command prints keys only; keep it so.
- Never open `appsettings.Development.json`, `appsettings.*.local.json`,
  `secrets.json` or user secrets (`UserSecretsId`), and never copy a
  value from `appsettings.json` into the docs.

## EF Core: entities, constraints, migrations

```bash
csfiles | xargs -0 grep -nH -E "DbSet<|: *DbContext\b|IEntityTypeConfiguration<|Entity<"
csfiles | xargs -0 grep -nH -E "\.(HasMaxLength|IsRequired|HasPrecision|HasDefaultValue(Sql)?|IsUnique|HasIndex|HasKey|HasOne|HasMany|WithOne|WithMany|HasForeignKey|OnDelete|HasConversion|HasQueryFilter)\("
srcfiles -path "*Migrations*" -name "*.cs" ! -name "*.Designer.cs" ! -name "*ModelSnapshot.cs" | xargs -0 grep -nH -E "(CreateTable|AddColumn|AlterColumn|DropTable|DropColumn|RenameColumn|CreateIndex)(<[a-z]+>)?\(|name: *\"|maxLength:|defaultValue:"
```

- Each `DbSet<T>` is an entity, named in business words.
  `HasMaxLength(32).IsRequired()` = stored limit ✅; if it differs from the
  request validation limit, report both and raise a 🟡 question.
- `IsUnique()` = "no two share a reference" ✅; `HasMany/WithOne` =
  cardinality; `OnDelete(Cascade)` = children go with the parent ✅;
  `HasQueryFilter` (soft delete, tenant) hides rows silently.
- Migration names are a timeline of business concepts (`AddRefundWindow`),
  for scoping only. `defaultValue: 14` is the database default ✅, not
  proof the app uses 14. A column dropped later is gone; skip it.

## Enums and state machines

```bash
csfiles | xargs -0 grep -nH -E "\benum [A-Za-z]+(Status|State|Type|Kind|Stage|Step)?\b"
csfiles | xargs -0 grep -nH -E "Status *[!=]= *[A-Z][A-Za-z]+\.|Status *= *[A-Z][A-Za-z]+\.|case [A-Z][A-Za-z]+Status\."
```

- Enum members are the states ✅. Each guarded assignment
  (`if (Status != Pending) throw` then `Status = Cancelled`) is one
  transition ✅; a diagram assembled from several sites is 🔵; a member
  with no assignment site is 🟡 ("reachable?").

## MediatR and domain events: feature boundaries

```bash
csfiles | xargs -0 grep -nH -E "IRequest(<[^>]+>)?\b|IRequestHandler<|INotification\b|INotificationHandler<|ICommand|IQuery|\.Send\(|\.Publish\(|AddDomainEvent\(|DomainEvent"
```

- One command (`CreateOrder : IRequest<int>`) = one user action; one
  query = one read or screen. Rules live in the handler and in
  `<Command>Validator`, usually in the same folder.
- Notification and domain event handlers are "then the system also..." steps.

## Background work and messaging

```bash
csfiles | xargs -0 grep -nH -E ": *(BackgroundService|IHostedService)\b|IConsumer<|RecurringJob\.|BackgroundJob\.|IJob\b|WithCronSchedule|CreateSender\(|CreateProcessor\(|ServiceBusTrigger|TimerTrigger|\[Queue|\.Publish\(|\.Send\("
```

- `BackgroundService`, Hangfire `RecurringJob`, Quartz `IJob` = a system
  actor on a schedule ✅ (cite the interval or cron); why is 🟡.
- `.Publish(` on `IMediator`/`IPublisher` stays in-process; on MassTransit
  `IBus`/`IPublishEndpoint` or a `ServiceBusSender` it leaves the process
  and, with a consumer of the same message or queue elsewhere, is a
  cross-repo hop (recipe H). Check the field type first.

## SignalR hubs and outbound HTTP

```bash
csfiles | xargs -0 grep -nH -E ": *Hub(<[A-Za-z]+>)?\b|MapHub<|SendAsync\(\"|Clients\.(All|Caller|Group|User)"
csfiles | xargs -0 grep -nH -E "AddHttpClient|AddRefitClient|BaseAddress|HttpClient\b|\.(Get|Post|Put|Delete|Patch)(AsJson|Async|FromJson)[A-Za-z]*\(\"|\[(Get|Post|Put|Delete|Patch)\(\""
```

- Hub methods are client actions; `SendAsync("StatusChanged")` is a live
  update: match the event name on the client (recipe H) first.
- A typed client or Refit interface (`[Post("/shipments")]`) is one
  external service, named by role ("payment provider"); cite the
  registration and the call. Base URLs from config: key only.

## Resources (.resx) and localizers

```bash
srcfiles -name "*.resx" | xargs -0 grep -nH -A2 -E "<data name=\"TooManyItems\"" | grep -E "<value>" | sed -E 's/^(.*\.resx)-([0-9]+)-/\1:\2:/'
srcfiles \( -name "*.cs" -o -name "*.razor" -o -name "*.cshtml" \) ! -name "*.Designer.cs" | xargs -0 grep -nH -E "IStringLocalizer|IHtmlLocalizer|IViewLocalizer|[A-Za-z_]*[Ll]ocalizer\[\"|\b_?[lL]\[\""
```

- Key = `<data name="...">`; wording = the `<value>` line, which is what
  you cite. The `sed` turns grep's context separator back into `path:line`.
- `Messages.resx` is the neutral catalog, `Messages.vi.resx` etc. are
  translations: quote the neutral one (recipe M). `Messages.TooManyItems`
  in code = key `TooManyItems`; never cite `Messages.Designer.cs`.

## Error shape: ProblemDetails and exception middleware

```bash
csfiles | xargs -0 grep -nH -E "ProblemDetails|UseExceptionHandler|IExceptionHandler|IMiddleware|StatusCodes\.Status[0-9]+|Results\.(Problem|ValidationProblem|NotFound|BadRequest|Conflict)|throw new [A-Za-z]+Exception\("
```

- "Rejected with 422, title 'Business rule violated'" is ✅ only when the
  throw and the middleware or `IExceptionHandler` mapping are both cited.
- `[ApiController]` turns failed DataAnnotations into a 400 with field
  errors automatically (cite it). An exception nothing maps ends as a
  generic 500: 🔵, plus a 🟡 question on what the user should see.

## Tests: xUnit, NUnit, MSTest

```bash
csfiles -path "*Test*" | xargs -0 grep -nH -E "\[(Fact|Theory|InlineData|MemberData|Test|TestCase|TestMethod|DataRow)\b|Should[A-Z]|Assert\."
csfiles -path "*Test*" | xargs -0 grep -nH -E "Skip *=|\[Ignore|, *Ignore|\[Explicit|, *Explicit|Assert\.Inconclusive"
```

- `[InlineData]`, `[TestCase]`, `[DataRow]` rows are the boundary values;
  cite the row line, then apply recipe T.
- Skip forms: xUnit `[Fact(Skip = "...")]`, NUnit `[Ignore]` and
  `[Explicit]` (not run by default), MSTest `[Ignore]`,
  `Assert.Inconclusive`. All 🟡, never ✅.

## Obsolete paths and feature flags

```bash
srcfiles \( -name "*.cs" -o -name "*.razor" -o -name "*.cshtml" \) ! -name "*.Designer.cs" | xargs -0 grep -nH -E "\[Obsolete|\[FeatureGate|IFeatureManager|IsEnabledAsync\(|<feature "
srcfiles -name "appsettings.json" | xargs -0 grep -nH -A20 -E "\"FeatureManagement\"" | grep -E "\"[A-Za-z0-9_.-]+\" *:" | sed -E 's/^(.*\.json)-([0-9]+)-/\1:\2:/; s/("[^"]*" *:).*/\1/'
```

- `[Obsolete]` or `[FeatureGate("BulkImport")]` → recipe D. Flag names
  come from the second command; whether a flag is on in production is
  runtime config, so ask "is `BulkImport` on?", never infer it.

## .NET pitfalls

- Skip `obj/`, `bin/`, `*.Designer.cs`, `*.g.cs`, `*ModelSnapshot.cs`:
  generated, full of routes and keys that look real (`srcfiles` prunes
  the folders; `csfiles` or `! -name` drops the files).
- Partial classes (controllers, `.razor.cs`, page models) split one
  feature over files; search by class name, not by file.
- Resolve every route token and prefix before citing: `[controller]`,
  `[area]`, `MapGroup`, `UsePathBase`, `v{version:apiVersion}`.
- Keys, never values, from any settings or secrets source.
