# Yocto / BitBake Cheat Sheet

## Fish Memory

### Build & Run

#### `bitbake <target>`

Build a recipe or image

```sh
bitbake core-image-weston
```

#### `bitbake <image> -c <task>`

Run a specific task of a recipe

```sh
bitbake python3 -c compile
```

---

### Cleaning

#### `bitbake -c clean <recipe>`

Remove work directory (keeps downloads/sstate)

#### `bitbake -c cleansstate <recipe>`

Full reset of a recipe (forces rebuild from scratch)

#### `bitbake -c cleanall <recipe>`

Removes everything including downloaded sources

---

### Debug / Inspection

#### `bitbake -e <recipe>`

Dump full environment (variables, overrides, etc.)

#### `bitbake -s`

List available recipes and versions

#### `bitbake -g <target>`

Generate dependency graph (`.dot` files)

---

### Devtool (you used this earlier)

#### `devtool upgrade <recipe>`

Upgrade recipe to newer upstream version

#### `devtool modify <recipe>`

Extract recipe source to workspace for editing

#### `devtool build <recipe>`

Build modified recipe in workspace

#### `devtool reset <recipe>`

Undo `devtool modify`

---

### Layers

#### `bitbake-layers show-layers`

List all enabled layers and priorities

#### `bitbake-layers add-layer <path>`

Add a layer to build

#### `bitbake-layers remove-layer <path>`

Remove a layer

#### `bitbake-layers show-recipes`

Show which layer provides each recipe

---

### Recipe / Files Debug

#### `bitbake -c devshell <recipe>`

Open shell inside recipe build environment

#### `bitbake -c menuconfig virtual/kernel`

Kernel configuration menu

---

### Configuration Checks

#### `bitbake -e | grep <VAR>`

Check final value of a variable

```sh
bitbake -e python3 | grep ^PV=
```

---

### Task Control

#### `bitbake <recipe> -c install -f`

Force re-run a specific task

#### `bitbake <recipe> -f`

Force rebuild (ignores stamp)

---

### Image Content

#### `bitbake <image> -c rootfs`

Rebuild only root filesystem

#### `bitbake <image> -c populate_sdk`

Generate SDK

---

## Reminders

* **recipe (`.bb`)** = how to build something
* **task** = step (`do_compile`, `do_install`, etc.)
* **image** = final filesystem
* **layer** = collection of recipes
* **sstate** = shared build cache
