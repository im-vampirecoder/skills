# Mobile recipes

Assumes `R` and `srcfiles` from `recipes-cross-stack.md` are already
defined; tests (T), catalogs (M), dead code (D) and hops (H) live there.
On mobile, screens and navigation define the features and flows: start
from the navigation entries, then follow each screen to its validation,
wording, state and backend calls.

## Pitfalls for every mobile stack

```bash
# Reachability: every reference to a screen outside its own definition (S = screen type or route name)
S=CheckoutView; srcfiles \( -name "*.swift" -o -name "*.kt" -o -name "*.dart" -o -name "*.ts*" -o -name "*.js*" \
  -o -name "*.storyboard" -o -name "*.xml" \) | xargs -0 grep -nH -w "$S" | grep -v -E "(struct|class|fun|function) +$S"
# Remote config and feature flags that make a path conditional
srcfiles | xargs -0 grep -nH -E "RemoteConfig|remoteConfig|configValue\(forKey|getBoolean\(\"|getBool\('|LaunchDarkly|Statsig|isFeatureEnabled" | head -40
# Config files holding keys: file list, then key names only (grep -o never prints the value)
srcfiles \( -name "GoogleService-Info.plist" -o -name "google-services.json" -o -name "*.xcconfig" \) | xargs -0 -n1 echo
srcfiles -name "*.xcconfig" | xargs -0 grep -nH -o -E "^[A-Z_][A-Z0-9_]* *="
srcfiles \( -name "GoogleService-Info.plist" -o -name "google-services.json" \) | xargs -0 grep -nH -o -E "<key>[A-Za-z_]+</key>|\"[a-z_]+\" *:"
```

- A screen file is not a feature. It is reachable only if a navigation
  entry (link, route, segue, deep link, tab) points to it. No entry → 🟡,
  a Gap row with the pattern searched, then recipe D.
- A path behind remote config or a flag is conditional → 🟡: the default
  may be in code, the live value is not.
- Client-side validation can differ from the server's. Record both limits
  with both citations; when they disagree, write a Gap row, never pick one.
- `srcfiles` prunes `Pods`, `DerivedData`, `build`, `.dart_tool`,
  `.gradle`; generated files (`*.g.dart`, `*.freezed.dart`, `*.gr.dart`)
  are excluded by `dartfiles` below. Never `cat` the config files above.

## Swift / iOS

### Detect, screens, navigation

```bash
find "$R" -maxdepth 3 \( -name "*.xcodeproj" -o -name "*.xcworkspace" -o -name Package.swift -o -name Podfile \
  -o -name Cartfile \) -not -path "*/Pods/*" -print
srcfiles -name "*.swift" | xargs -0 grep -nH -E "struct +[A-Za-z0-9_]+ *: *View( |\{|,|$)|class +[A-Za-z0-9_]+ *: *UI[A-Za-z]*ViewController"
srcfiles -name "*.swift" | xargs -0 grep -nH -E "NavigationStack|NavigationSplitView|NavigationLink|\.navigationDestination|\.sheet\(|\.fullScreenCover\(|TabView|pushViewController|present\(|performSegue|Coordinator"
srcfiles \( -name "*.storyboard" -o -name "*.xib" \) | xargs -0 grep -nH -E "<segue |customClass=|storyboardIdentifier="
```

- `Podfile`/`Package.swift` name the libraries (networking, analytics,
  remote config) worth searching for next.
- Each `View`/`UIViewController` is a candidate screen; the
  `NavigationLink`, `.navigationDestination`, push, segue or coordinator
  line that opens it is the flow step. Cite both → ✅.
- `.sheet`/`.fullScreenCover` = modal step, opened when its
  `isPresented:` binding is true; `TabView` = top-level sections.
- A storyboard `<segue identifier=...>` matches a
  `performSegue(withIdentifier:)` call: that call names the trigger.

### Validation and wording

```bash
srcfiles -name "*.swift" | xargs -0 grep -nH -E "isValid|validate|\.count *[<>]=?|[<>]=? *[0-9]+|isEmpty|NSPredicate|Regex|\.disabled\("
srcfiles -name "*.swift" | xargs -0 grep -nH -E "String\(localized:|NSLocalizedString\(|LocalizedStringKey|Text\(\"|navigationTitle\(" | head -60
srcfiles \( -name "Localizable.strings" -o -name "*.xcstrings" \) | xargs -0 grep -nH -E "\"checkout\.too_many\""
```

- A literal limit (`qty <= 20`) at the cited line → ✅ rule.
  `.disabled(!isValid)` blocks the action without showing a message.
- Keys resolve in `Localizable.strings` (`"key" = "text";`) or the
  `.xcstrings` JSON; then apply recipe M. `Text("...")` literals may
  themselves be lookup keys: check the catalog before quoting.

### Models, storage, networking

```bash
srcfiles -name "*.swift" | xargs -0 grep -nH -E ": *(Codable|Decodable|Encodable)|@Model|NSManagedObject|CodingKeys"
srcfiles -path "*.xcdatamodeld/*" -name contents | xargs -0 grep -nH -E "<entity |<attribute |<relationship "
srcfiles -name "*.swift" | xargs -0 grep -nH -E "URLSession|URLRequest|AF\.request|Alamofire|Moya|httpMethod|\"/api/|var path"
```

- `Codable` structs mirror API payloads: confirm fields against the
  server model (recipe H) before naming them entity attributes.
- Core Data `<entity>` and SwiftData `@Model` are stored on the device;
  say so in the entity description.
- Endpoint enums map a case to a path: cite the `return "/api/..."` line,
  then match it to the server route (recipe H).

### Permissions, deep links, push, tests

```bash
srcfiles -name "*.plist" ! -name "GoogleService-Info.plist" | xargs -0 grep -nH -A1 -E "<key>NS[A-Za-z]+UsageDescription</key>"
srcfiles \( -name "*.plist" -o -name "*.entitlements" \) ! -name "GoogleService-Info.plist" | xargs -0 grep -nH -A2 -E "CFBundleURLSchemes|associated-domains"
srcfiles -name "*.swift" | xargs -0 grep -nH -E "onOpenURL|open url|continue userActivity|didRegisterForRemoteNotifications|UNUserNotificationCenter|didReceive"
srcfiles -name "*.swift" -path "*Tests*" | xargs -0 grep -nH -E "func test|@Test|@Suite|XCTSkip|\.disabled\(|\.enabled\(if:"
```

- The `<string>` after a `NS*UsageDescription` key (`-A1` prints it as
  `path-line-`) is the exact permission prompt → quote it, ✅. Why the
  data is needed beyond that sentence → 🟡.
- URL schemes and `applinks:` domains are entry points; each handled
  path starts a flow. A scheme with no handler code → Gap.
- Swift Testing `@Test(.disabled(...))` is skipped and `.enabled(if:)`
  conditional; label as recipe T says.

## Kotlin / Android

### Detect, manifest, screens, navigation

```bash
find "$R" -maxdepth 3 \( -name "settings.gradle*" -o -name "build.gradle*" -o -name "libs.versions.toml" \) -not -path "*/build/*" -print
srcfiles -name AndroidManifest.xml | xargs -0 grep -nH -E "<activity|<service|<receiver|<intent-filter|<data |<uses-permission|android:exported"
srcfiles -name "*.kt" | xargs -0 grep -nH -E "fun +[A-Z][A-Za-z0-9]*(Screen|Page|Route|Dialog|Sheet)\(|NavHost\(|composable\(\"|composable<|dialog\(\"|\.navigate\(|startDestination|@Serializable +(data +)?(class|object)"
srcfiles -path "*res/navigation*" -name "*.xml" | xargs -0 grep -nH -E "<(fragment|activity|dialog) |<action |<deepLink |startDestination"
srcfiles \( -name "*.kt" -o -name "*.java" \) | xargs -0 grep -nH -E "class +[A-Za-z0-9_]+.*: *[A-Za-z]*(Activity|Fragment)\(|extends +[A-Za-z]*(Activity|Fragment)"
```

- An `<activity>` with `<intent-filter>` + `<data>` is an entry point
  (deep link or launcher); cite the `<data>` line for the URL.
  `<uses-permission>` names the permission; the system writes the prompt,
  so any rationale text is in `strings.xml`.
- `composable("route")` or `composable<Type>` (type-safe route; the
  `@Serializable` class holds its arguments) registers a screen. A
  `@Composable fun XScreen` with no registration is unreachable (🟡).
- Navigation XML: `<action>` = flow step, `<deepLink>` = entry point.

### UI state, validation, wording

```bash
srcfiles -name "*.kt" | xargs -0 grep -nH -E "sealed +(class|interface)|: *ViewModel\(|MutableStateFlow|StateFlow<|LiveData<|UiState"
srcfiles -name "*.kt" | xargs -0 grep -nH -E "validate|isValid|require\(|\.length *[<>]|[<>]=? *[0-9]+\)|Patterns\.|Regex\(|isBlank\(\)"
srcfiles -path "*res/layout*" -name "*.xml" | xargs -0 grep -nH -E "android:maxLength|android:inputType|android:hint="
srcfiles -path "*res/values*" -name "strings.xml" | xargs -0 grep -nH -E "name=\"err_too_many\""
```

- Members of a sealed UI-state type are the screen's states (loading,
  empty, error, content) → ✅ per member; the line assigning one is the
  transition.
- `R.string.x` / `@string/x` resolve in `res/values/strings.xml`
  (default) and `res/values-xx/` (locales); apply recipe M and quote
  `%1$d` placeholders as the template. `android:maxLength` is a client
  limit: compare with the server's.

### Room, network, background work, tests

```bash
srcfiles -name "*.kt" | xargs -0 grep -nH -E "@Entity|@Dao|@Query\(|@Insert|@Database|@PrimaryKey|@ForeignKey"
srcfiles \( -name "*.kt" -o -name "*.java" \) | xargs -0 grep -nH -E "@(GET|POST|PUT|PATCH|DELETE)\(\"|baseUrl\(|client\.(get|post|put|patch|delete)\(|HttpClient\("
srcfiles -name "*.kt" | xargs -0 grep -nH -E ": *(Coroutine)?Worker\(|(OneTime|Periodic)WorkRequest|enqueueUniqueWork|setConstraints|FirebaseMessagingService"
srcfiles \( -path "*src/test*" -o -path "*src/androidTest*" \) \( -name "*.kt" -o -name "*.java" \) | xargs -0 grep -nH -E "@Test|@Ignore|onView\(|onNodeWith|assert"
```

- Room `@Entity` = local table. Retrofit annotations and Ktor calls give
  the path for recipe H.
- A WorkManager request is a scheduled process: interval and constraints
  are ✅ rules; why that interval → 🟡.
- Espresso/Compose tests quote visible text; still resolve it in the
  catalog. `@Ignore` → recipe T.

## Flutter

```bash
# Hand-written Dart only, used below
dartfiles() { srcfiles -name "*.dart" ! -name "*.g.dart" ! -name "*.freezed.dart" ! -name "*.gr.dart"; }
srcfiles -name pubspec.yaml | xargs -0 grep -nH -E "^ +(go_router|auto_route|[a-z_]*bloc|[a-z_]*riverpod|provider|dio|http|freezed[a-z_]*|json_[a-z_]+|firebase_[a-z_]+|flutter_localizations|intl):|generate:"
```

- The dependencies tell you which routing, state and network patterns to
  search for. Always cite the hand-written file, never its generated twin.

### Routes, screens, validators

```bash
dartfiles | xargs -0 grep -nH -E "GoRoute\(|ShellRoute\(|routes: *\{|@RoutePage|AutoRoute\(|onGenerateRoute|context\.(go|push)\(|Navigator\.(push|pushNamed)"
dartfiles | xargs -0 grep -nH -E "class +[A-Z][A-Za-z0-9]*(Screen|Page|View) +extends +[A-Za-z]*Widget"
dartfiles | xargs -0 grep -nH -E "validator:|maxLength:|inputFormatters:|LengthLimitingTextInputFormatter|RegExp\(|[<>]=? *[0-9]+\)"
```

- `GoRoute(path:)`, a `routes:` map entry or auto_route `@RoutePage`
  registers a screen; `context.go`/`Navigator.push` lines are flow steps;
  path parameters (`:id`) are the screen's inputs.
- Each `return` in a `validator:` closure is one rule with its message:
  a literal is quoted as written (✅), a localized one goes through ARB.

### Wording, models, state

```bash
dartfiles | xargs -0 grep -nH -E "AppLocalizations\.of\(context\)!?\.[A-Za-z]+|context\.l10n\.|\.tr\(\)"
srcfiles -name "*.arb" | xargs -0 grep -nH -E "\"@@locale\"|\"qtyRequired\""
dartfiles | xargs -0 grep -nH -E "@freezed|@Freezed|@JsonSerializable|factory +[A-Za-z]+\.fromJson|@HiveType|@collection"
dartfiles | xargs -0 grep -nH -E "extends +(Cubit|Bloc)<|sealed +class|extends +[A-Za-z]+State( |\{)|Provider<|@riverpod|Notifier<|emit\("
```

- The getter name is the ARB key, one `app_<locale>.arb` per language;
  the `@key` description says what the text is for, never why the rule
  exists. Apply recipe M.
- Bloc/Cubit state subclasses are the screen states; `emit(...)` lines
  are the transitions → ✅.

### Network and tests

```bash
dartfiles | xargs -0 grep -nH -E "dio\.(get|post|put|patch|delete)\(|http\.(get|post|put|patch|delete)\(|Uri\.parse\(|baseUrl"
srcfiles -name "*_test.dart" | xargs -0 grep -nH -E "test\(|testWidgets\(|group\(|skip: *(true|'|\")"
```

- dio/http paths go to recipe H. A `skip:` argument marks a skipped test
  → recipe T.

## React Native

```bash
# JS/TS source, used below
jsfiles() { srcfiles \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \); }
find "$R" -maxdepth 1 \( -name package.json -o -name app.json -o -name "app.config.*" \) -print0 | xargs -0 grep -nH -E "\"(react-native|expo|expo-router|@react-navigation/[a-z-]+|react-hook-form|zod|yup|i18next|react-i18next|axios|detox)\"|\"scheme\"|UsageDescription|\"permissions\""
```

- `app.json` (Expo) holds the URL `scheme`, iOS permission prompts
  (`infoPlist` `NS*UsageDescription`) and Android permissions: quote them
  as for native apps.

### Navigation and screens

```bash
jsfiles | xargs -0 grep -nH -E "create(NativeStack|Stack|BottomTab|Drawer)Navigator|<[A-Za-z]+\.Screen|prefixes:|screens: *\{|navigation\.(navigate|push|replace)\("
[ -d "$R/app" ] && find "$R/app" -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" \) -print
jsfiles | xargs -0 grep -nH -E "<Link +href=|router\.(push|replace)\(|useLocalSearchParams|<Redirect"
```

- React Navigation: each `<Stack.Screen name=...>` registers a screen;
  the `linking` config (`prefixes`, `screens`) maps URLs to screens.
- Expo Router: the file path under `app/` is the route (`[id]` = a
  parameter, `(group)` = no URL segment, `_layout` = the navigator); the
  path list is the citation. `Link`/`router.push` lines are flow steps.

### Forms, wording, API calls, tests

```bash
jsfiles | xargs -0 grep -nH -E "useForm\(|zodResolver|yupResolver|z\.(object|string|number)|yup\.(object|string|number)|\.(min|max|length|email|regex|matches|required)\("
jsfiles | xargs -0 grep -nH -E "[^A-Za-z]t\(['\"]|i18n\.t\(|useTranslation\(|<Trans "
srcfiles -path "*locales*" -name "*.json" | xargs -0 grep -nH -E "\"too_many\" *:"
jsfiles | xargs -0 grep -nH -E 'fetch\(|axios\.(get|post|put|patch|delete|create)\(|baseURL|BASE_URL|/api/'
srcfiles \( -name "*.test.*" -o -name "*.spec.*" -o -name "*.e2e.*" \) | xargs -0 grep -nH -E "it\(|test\(|\.skip\(|xit\(|element\(by\.|toBeVisible"
```

- A schema line (`.max(20, ...)`) is the rule and often the message key
  → ✅; compare it with the server limit.
- Nested JSON breaks a dotted-key search (`checkout.too_many` is
  `"too_many"` inside `"checkout"`): grep the last segment, confirm the
  parent with `sed -n` on that file, then apply recipe M.
- Path constants (`API.orders`) and template URLs go to recipe H; cite
  the constant and the call that uses it.
- Detox (`element(by.id(...))`) tests assert an end-to-end flow → ✅ for
  the steps they check; `.skip` → recipe T.
