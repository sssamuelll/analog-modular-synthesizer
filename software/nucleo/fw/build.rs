use std::path::{Path, PathBuf};
use std::process::Command;

fn main() {
    println!("cargo:rustc-link-arg-bins=--nmagic");
    println!("cargo:rustc-link-arg-bins=-Tlink.x");
    println!("cargo:rustc-link-arg-bins=-Tdefmt.x");
    println!("cargo:rerun-if-changed=memory.x");
    println!("cargo:rerun-if-changed=build.rs");
    // El codigo que entra en el binario: si cambia sin que se mueva `HEAD`, `-sucio`
    // tiene que aparecer. Sin esto el guion corria una sola vez por commit y un
    // binario con cambios encima seguia diciendo que era el commit limpio.
    println!("cargo:rerun-if-changed=src");
    println!("cargo:rerun-if-changed=Cargo.toml");
    println!("cargo:rerun-if-changed=../core/src");
    println!("cargo:rerun-if-changed=../core/Cargo.toml");

    // La revision de git, embebida en el binario y publicada por `defmt` al
    // arrancar. No es adorno: `resistencia_j2.csv` es la puerta de fabricacion
    // (acta del 11-09, ficha 1) y una fila que no dice con que firmware se midio
    // no se puede repetir -- y las dos tandas del soak, al piso y al peldano 2,
    // son binarios distintos que solo se diferencian en una constante.
    println!("cargo:rustc-env=SAM17_GIT={}", revision());
    vigilar_git();
}

/// Corre `git` y devuelve su salida sin espacios, o `None` si falla por lo que
/// sea (no esta instalado, no es un repo, el comando devuelve error).
fn git(args: &[&str]) -> Option<String> {
    let salida = Command::new("git").args(args).output().ok()?;
    if !salida.status.success() {
        return None;
    }
    Some(String::from_utf8(salida.stdout).ok()?.trim().to_string())
}

/// `<rev corta>`, con `-sucio` detras si el arbol tiene cambios sin commitear, o
/// `sin-git` si cualquiera de las dos preguntas falla.
///
/// **`sin-git` cuando falla una sola de las dos, a proposito.** Una rev sin
/// saber si el arbol esta limpio es peor que no tener rev: se leeria como
/// *«este commit exacto»* cuando podria ser ese commit mas cambios encima.
///
/// `git status --porcelain` mira el **repo entero**, no solo `fw/`. Es de
/// sobra -- un cambio en un DXF del case marca el firmware `-sucio` sin que el
/// binario cambie --, y el exceso va en la direccion segura: nunca dira limpio
/// sobre un arbol que no lo esta.
fn revision() -> String {
    const SIN_GIT: &str = "sin-git";
    let (Some(rev), Some(estado)) = (
        git(&["rev-parse", "--short", "HEAD"]),
        git(&["status", "--porcelain"]),
    ) else {
        return SIN_GIT.to_string();
    };
    if rev.is_empty() {
        return SIN_GIT.to_string();
    }
    if estado.is_empty() {
        rev
    } else {
        format!("{rev}-sucio")
    }
}

/// Pide a cargo que vuelva a correr este guion cuando `HEAD` se mueva, para que
/// `SAM17_GIT` no se quede pegado al commit del primer build. (Cuando cambia el
/// codigo sin mover `HEAD` lo piden las rutas de `main`.)
///
/// **El `.git` de un worktree es un archivo, no un directorio** (dice
/// `gitdir: .../\.git/worktrees/<nombre>`), asi que no vale con mirar `.git/HEAD`
/// a mano: hay que preguntarle a git donde estan las cosas.
///
/// Y son dos sitios distintos: el `HEAD` del worktree vive en **su** gitdir
/// (`--git-dir`), pero el archivo de la rama a la que apunta vive en el dir
/// **comun** (`--git-common-dir`), que en un worktree es el `.git` del repo
/// principal. Se vigilan los dos, mas `packed-refs`, por si la rama estuviera
/// empaquetada y no tuviera archivo suelto.
///
/// Solo se emiten rutas que existen: una ruta inexistente en
/// `rerun-if-changed` deja el guion corriendo en cada build.
fn vigilar_git() {
    let Some(gitdir) = git(&["rev-parse", "--git-dir"]).map(absoluta) else {
        return;
    };
    let comun = git(&["rev-parse", "--git-common-dir"]).map(absoluta);

    vigilar(&gitdir.join("HEAD"));
    if let Some(comun) = &comun {
        vigilar(&comun.join("packed-refs"));
    }

    // Con `HEAD` desprendido no hay rama que vigilar, y `HEAD` de arriba ya
    // contiene el SHA: cambia solo.
    if let Some(referencia) = git(&["symbolic-ref", "-q", "HEAD"]) {
        vigilar(&gitdir.join(&referencia));
        if let Some(comun) = &comun {
            vigilar(&comun.join(&referencia));
        }
    }
}

/// `git rev-parse` puede contestar una ruta relativa al directorio de trabajo,
/// que durante el build es la raiz del paquete.
fn absoluta(ruta: String) -> PathBuf {
    let p = PathBuf::from(ruta);
    if p.is_absolute() {
        return p;
    }
    match std::env::current_dir() {
        Ok(cwd) => cwd.join(p),
        Err(_) => p,
    }
}

fn vigilar(ruta: &Path) {
    if ruta.exists() {
        println!("cargo:rerun-if-changed={}", ruta.display());
    }
}
