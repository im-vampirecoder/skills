---
name: update-packages
description: Update outdated NuGet packages in a .NET solution using dotnet-outdated. Use when the user wants to upgrade NuGet packages, check for outdated dependencies, mentions dotnet-outdated, or asks to update package versions in a .NET/C# project.
---

# Update NuGet Packages

Finds every outdated NuGet package in a .NET solution and upgrades them, respecting Central Package Management (CPM) when the repo uses it. Confirm with the user before mutating any file, and before running the build/test verification.

## Process

1. **Locate the solution.** Search the workspace and its subfolders for `.sln` or `.slnx` files. If none are found, tell the user this doesn't look like a .NET project and stop - the rest of the skill doesn't apply. If more than one is found, ask the user which solution to target.

2. **Check for Central Package Management.** Look for `Directory.Packages.props` in the same folder as the solution file. Note whether it exists - it decides which upgrade path Step 6 takes.

3. **Ensure `dotnet-outdated` is installed.** Run `dotnet tool list --global` and check for `dotnet-outdated-tool`. If it isn't listed, install it: `dotnet tool install --global dotnet-outdated-tool`.

4. **Run the scan.** From the solution folder, run `dotnet outdated` against the `.sln`/`.slnx` file. Read the table output and note, per package, its name and the version in the "Latest" column.

5. **Confirm before changing anything.** Summarize what would be upgraded (package names, current -> latest versions) and ask the user to confirm. If they decline, stop here.

   Once confirmed, ask whether to make the change in a git worktree or directly in the working folder. Only ask this if the project is inside a git repository - if it isn't, skip straight to working in place. If a `worktree` skill or equivalent tooling is available, use it to create the worktree; otherwise `git worktree add` manually.

6. **Apply the upgrade.**
   - **Directory.Packages.props exists (CPM):** `dotnet outdated -u` doesn't reliably rewrite CPM version pins. Instead, edit `Directory.Packages.props` directly - for each package from Step 4, update its `<PackageVersion Include="..." Version="..." />` entry to the latest version noted.
   - **No Directory.Packages.props:** run `dotnet outdated -u` against the solution and wait for it to finish; it rewrites the `.csproj` files directly.

7. **Verify the build.** Run `dotnet build` against the solution. If it fails, report the errors to the user and stop - do not proceed to testing with a broken build.

8. **Run tests, if any exist.** Scan the solution's projects for test projects - look for `<IsTestProject>true</IsTestProject>`, a test framework package reference (`Microsoft.NET.Test.Sdk`, `xunit`, `NUnit`, `MSTest.TestFramework`), or `*.Tests.csproj`/`*.Test.csproj` naming. If any are found, ask the user whether to run `dotnet test`. If they confirm, run it and report any failures.

9. **Finish.** Summarize what was upgraded, where (worktree or working folder), and the build/test result.
