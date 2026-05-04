# Yocto Distro Creation Cheat Sheet

## Core distro config files

### `conf/distro/<mydistro>.conf`

Main distro definition.

Common settings:

```bitbake
DISTRO = "mydistro"
DISTRO_NAME = "My Custom Distro"

# Init system
DISTRO_FEATURES:append = " systemd"
VIRTUAL-RUNTIME_init_manager = "systemd"

# Package format
PACKAGE_CLASSES = "package_rpm"

# Default features
DISTRO_FEATURES:append = " wayland opengl"

# Remove unwanted features
DISTRO_FEATURES:remove = " x11"
```

---

## DISTRO_FEATURES (global feature control)

Controls what gets enabled across the system.

### Examples

```bitbake
wayland
x11
opengl
vulkan
systemd
pulseaudio
bluetooth
wifi
```

### Debug

```bash
bitbake -e <recipe> | grep DISTRO_FEATURES
```

---

## PACKAGECONFIG (per-recipe features)

Enable/disable features inside packages:

```bitbake
PACKAGECONFIG:append:pn-weston = " vulkan"
PACKAGECONFIG:remove:pn-weston = " x11"
```

Check options:

```bash
bitbake -e weston | grep PACKAGECONFIG
```

---

## Providers (select implementations)

Choose which package provides a feature:

```bitbake
PREFERRED_PROVIDER_virtual/egl = "mesa"
PREFERRED_PROVIDER_virtual/libgl = "mesa"
PREFERRED_PROVIDER_virtual/weston = "weston"
```

---

## Version control

Force versions:

```bitbake
PREFERRED_VERSION_weston = "15.0.0"
```

---

## Adding layers

```bash
bitbake-layers add-layer ../meta-openembedded/meta-oe
```

Check layers:

```bash
bitbake-layers show-layers
```

---

## Dependency inspection

```bash
bitbake -g <image>
```

Generates:

* `pn-depends.dot`
* `task-depends.dot`

Visualize:

```bash
dot -Tpng pn-depends.dot -o deps.png
```

---

## Debugging build issues

### Check why something is included:

```bash
bitbake -e <recipe> | grep ^DEPENDS=
```

### Check provider:

```bash
bitbake -e | grep PREFERRED_PROVIDER
```

---

## Sysroot debugging

```bash
bitbake <recipe> -c devshell
```

Inside:

```bash
echo $PATH
which <tool>
pkg-config --modversion <lib>
```

---

## Removing unwanted stuff globally

```bitbake
DISTRO_FEATURES:remove = " x11"
```

or:

```bitbake
PACKAGE_EXCLUDE += "package-name"
```

---

## Performance tweaks

```bitbake
BB_NUMBER_THREADS = "8"
PARALLEL_MAKE = "-j8"
```

---

## Licensing control

```bitbake
LICENSE_FLAGS_ACCEPTED += "commercial"
```

---

## Init system selection

### systemd:

```bitbake
DISTRO_FEATURES:append = " systemd"
VIRTUAL-RUNTIME_init_manager = "systemd"
```

### sysvinit:

```bitbake
DISTRO_FEATURES:remove = " systemd"
VIRTUAL-RUNTIME_init_manager = "sysvinit"
```

---

## Graphics stack selection

### Wayland only:

```bitbake
DISTRO_FEATURES:append = " wayland opengl"
DISTRO_FEATURES:remove = " x11"
```

### X11:

```bitbake
DISTRO_FEATURES:append = " x11"
```

---

## Important concepts

### Native vs target

* `*-native` -> runs on build machine
* normal packages -> run on target

---

### DISTRO vs MACHINE

* `DISTRO` -> software policy (features, init, graphics)
* `MACHINE` -> hardware (CPU, kernel, BSP)

---

### IMAGE vs DISTRO

* **DISTRO** -> defines rules
* **IMAGE** -> defines what is installed

---

## Cleaning and rebuilding

```bash
bitbake <recipe> -c clean
bitbake <recipe> -c cleanall
```
