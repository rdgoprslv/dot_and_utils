# Yocto / BitBake Cheat Sheet

## Fish Memory

### devtool (recipe development / workspace)

```bash
devtool upgrade <recipe>
```

Upgrade a recipe to a newer upstream version inside the workspace.

```bash
devtool reset <recipe>
```

Remove the recipe from workspace and restore original layer version.

```bash
devtool reset -f <recipe>
```

Force reset even if there are local changes.

```bash
devtool status
```

List recipes currently being modified in the workspace.

```bash
devtool build <recipe>
```

Build a recipe using workspace sources (instead of layer version).

---

### bitbake (build system core)

```bash
bitbake <recipe>
```

Build a recipe (full build).

```bash
bitbake <recipe> -c clean
```

Remove build output (keeps downloads and sstate).

```bash
bitbake <recipe> -c cleanall
```

Remove everything (build + downloads + sstate for that recipe).

```bash
bitbake <recipe> -c devshell
```

Open a shell with full build environment for debugging.

```bash
bitbake -e <recipe>
```

Dump all environment variables used for that recipe.

Example:

```bash
bitbake -e weston | grep ^PV=
```

shows recipe version.

---

### recipe & layer inspection

```bash
bitbake -s
```

List all available recipes and versions.

```bash
bitbake -s | grep <name>
```

Search for a specific recipe.

```bash
bitbake-layers show-recipes
```

List all recipes from all layers.

```bash
bitbake-layers show-recipes | grep <name>
```

Find where a recipe exists and its versions.

```bash
bitbake-layers add-layer <path>
```

Add a new layer to the build.

---

### debugging inside build

```bash
bitbake <recipe> -c devshell
```

Drop into build shell.

Then inside:

```bash
which <tool>
```

Check if a tool (e.g. `glslangValidator`) is available in sysroot.

```bash
find tmp/work -name <file>
```

Locate generated files in build directory.

---

### manual workspace cleanup

```bash
rm -rf workspace/sources/<recipe>
rm -rf workspace/recipes/<recipe>
```

Manually remove devtool workspace files (if reset fails).

---

## Common variables

```bitbake
DEPENDS += "pkg"
```

Add build-time dependency (target or native depending on suffix).

```bitbake
DEPENDS += "pkg-native"
```

Add **host tool dependency** (used during build).

```bitbake
PACKAGECONFIG:remove = "feature"
```

Disable a feature (e.g. `vulkan`).

```bitbake
EXTRA_OEMESON += "..."
```

Pass extra flags to Meson build system.

```bitbake
PREFERRED_VERSION_<recipe> = "x.y"
```

Force a specific recipe version.

---

## Reminders

* **-native** → runs on host (build machine)
* **target package** → runs on device
* **workspace/** → devtool sandbox (safe to delete)
* **clean vs cleanall**:

  * `clean` → rebuild from sstate
  * `cleanall` → rebuild from scratch
