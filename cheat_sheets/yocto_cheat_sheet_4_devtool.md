# Yocto `devtool` Cheat Sheet

## Core idea

`devtool` = **temporary workspace for editing recipes + sources safely**

```text
workspace/
├── sources/   -> source code (git repo)
└── recipes/   -> auto-generated recipes
```

## BASIC COMMANDS

### Add new recipe

```bash
devtool add <recipe> <src>
```

Examples:

```bash
devtool add python3-peewee https://pypi.org/project/peewee/4.0.3/
# or
devtool add my-app ./my-app/
```

### Modify existing recipe

```bash
devtool modify <recipe>
```

pulls source into workspace so you can edit

### Build recipe

```bash
devtool build <recipe>
```

### Deploy to device (fast testing)

```bash
devtool deploy-target <recipe> root@<ip>
```

### Remove from device

```bash
devtool undeploy-target <recipe> root@<ip>
```

### Check active workspace

```bash
devtool status
```

### Reset (discard workspace changes)

```bash
devtool reset <recipe>
```

Force:

```bash
devtool reset -f <recipe>
```

### Persist into your layer

```bash
devtool finish <recipe> <layer>
```

---

## WORKFLOWS

### Create new package (e.g. Python lib)

```bash
devtool add python3-peewee <url>
devtool build python3-peewee
devtool deploy-target python3-peewee root@<ip>
devtool finish python3-peewee meta-yourlayer
```

### Modify existing package

```bash
devtool modify weston
## edit source
devtool build weston
devtool deploy-target weston root@<ip>
devtool finish weston meta-yourlayer
```

### Develop your app (fast loop)

```bash
devtool add my-app ./my-app
```

Then iterate:

```bash
## edit code locally
devtool build my-app
devtool deploy-target my-app root@<ip>
```

---

## PATCH WORKFLOW

To persist changes:

```bash
cd workspace/sources/<recipe>

## edit files
git add .
git commit -m "my change"

devtool finish <recipe> <layer>
```

commits -> patches automatically

---

## CLEAN SOURCE BEFORE FINISH

Fix “dirty tree” errors:

```bash
rm -rf build/ *.egg-info
git clean -fdx
```

OR:

```bash
devtool finish -f <recipe> <layer>
```

---

## MULTIPLE RECIPES

You can work on many at once:

```bash
devtool add pkg1 ...
devtool add pkg2 ...
devtool add pkg3 ...
```

Build all via image:

```bash
bitbake <image>
```

---

## DEBUGGING

### Open build shell

```bash
bitbake <recipe> -c devshell
```

### Check source location

```bash
devtool status
```

---

## COMMON FIXES

### Dependency missing

```bitbake
DEPENDS += "pkg-native"
```

### Runtime dependency

```bitbake
RDEPENDS:${PN} += "python3-xyz"
```

### Include files in package

```bitbake
FILES:${PN} += "path/to/files"
```
