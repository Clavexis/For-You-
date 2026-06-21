// clawpkg — a minimal, fast package manager.
//
//   - install / remove / update packages
//   - recursive dependency resolution (with cycle detection)
//   - JSON package manifests
//   - local package cache
//   - lock file (clawpkg.lock) recording exact installed versions
//
// A package "registry" is just a directory:
//   registry/<name>/<version>/package.json   (the manifest)
//   registry/<name>/<version>/files/...      (the package contents)
//
// This simulates a remote repo with the filesystem so the tool is fully
// self-contained and testable.
//
// Build:  cargo build --release
// Run  :  clawpkg install <name>
//
// Built by clavexis — github.com/clavexis

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::exit;

#[derive(Debug, Deserialize, Serialize, Clone)]
struct Manifest {
    name: String,
    version: String,
    #[serde(default)]
    dependencies: BTreeMap<String, String>,
}

#[derive(Debug, Default, Deserialize, Serialize)]
struct LockFile {
    #[serde(default)]
    packages: BTreeMap<String, String>, // name -> version
}

struct Config {
    registry: PathBuf,
    cache: PathBuf,
    install_dir: PathBuf,
    lock_path: PathBuf,
}

impl Config {
    fn new() -> Self {
        let registry = std::env::var("CLAWPKG_REGISTRY")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from("registry"));
        Config {
            registry,
            cache: PathBuf::from(".clawpkg/cache"),
            install_dir: PathBuf::from("clawpkg_modules"),
            lock_path: PathBuf::from("clawpkg.lock"),
        }
    }
}

// --- registry access ------------------------------------------------------
fn available_versions(cfg: &Config, name: &str) -> Vec<String> {
    let dir = cfg.registry.join(name);
    let mut versions: Vec<String> = match fs::read_dir(&dir) {
        Ok(rd) => rd
            .filter_map(|e| e.ok())
            .filter(|e| e.path().is_dir())
            .filter_map(|e| e.file_name().into_string().ok())
            .collect(),
        Err(_) => Vec::new(),
    };
    // Simple semver-ish sort (numeric by dotted components).
    versions.sort_by(|a, b| version_key(a).cmp(&version_key(b)));
    versions
}

fn version_key(v: &str) -> Vec<u64> {
    v.split('.').map(|p| p.parse::<u64>().unwrap_or(0)).collect()
}

fn latest_version(cfg: &Config, name: &str) -> Option<String> {
    available_versions(cfg, name).pop()
}

fn load_manifest(cfg: &Config, name: &str, version: &str) -> Option<Manifest> {
    let path = cfg.registry.join(name).join(version).join("package.json");
    let text = fs::read_to_string(path).ok()?;
    serde_json::from_str(&text).ok()
}

// --- dependency resolution ------------------------------------------------
// Resolves `name` (at `version` or latest) and all transitive dependencies.
// Returns name -> version, or an error string.
fn resolve(
    cfg: &Config,
    name: &str,
    version: Option<&str>,
    resolved: &mut BTreeMap<String, String>,
    visiting: &mut HashSet<String>,
) -> Result<(), String> {
    if visiting.contains(name) {
        return Err(format!("dependency cycle detected at '{}'", name));
    }
    // If already resolved, keep the first (we don't do version unification here).
    if resolved.contains_key(name) {
        return Ok(());
    }

    let ver = match version {
        Some(v) => v.to_string(),
        None => latest_version(cfg, name)
            .ok_or_else(|| format!("package '{}' not found in registry", name))?,
    };

    let manifest = load_manifest(cfg, name, &ver)
        .ok_or_else(|| format!("manifest for {}@{} not found", name, ver))?;

    visiting.insert(name.to_string());
    for (dep, dep_ver) in &manifest.dependencies {
        let req = if dep_ver == "*" { None } else { Some(dep_ver.as_str()) };
        resolve(cfg, dep, req, resolved, visiting)?;
    }
    visiting.remove(name);

    resolved.insert(name.to_string(), ver);
    Ok(())
}

// --- fs helpers -----------------------------------------------------------
fn copy_dir(src: &Path, dst: &Path) -> std::io::Result<()> {
    fs::create_dir_all(dst)?;
    if !src.exists() {
        return Ok(());
    }
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let path = entry.path();
        let target = dst.join(entry.file_name());
        if path.is_dir() {
            copy_dir(&path, &target)?;
        } else {
            fs::copy(&path, &target)?;
        }
    }
    Ok(())
}

fn load_lock(cfg: &Config) -> LockFile {
    fs::read_to_string(&cfg.lock_path)
        .ok()
        .and_then(|t| serde_json::from_str(&t).ok())
        .unwrap_or_default()
}

fn save_lock(cfg: &Config, lock: &LockFile) {
    let text = serde_json::to_string_pretty(lock).unwrap();
    let _ = fs::write(&cfg.lock_path, text);
}

// --- commands -------------------------------------------------------------
fn cmd_install(cfg: &Config, spec: &str) -> Result<(), String> {
    let (name, version) = parse_spec(spec);
    let mut resolved = BTreeMap::new();
    let mut visiting = HashSet::new();
    resolve(cfg, &name, version.as_deref(), &mut resolved, &mut visiting)?;

    println!("Resolved {} package(s):", resolved.len());
    let mut lock = load_lock(cfg);
    for (pkg, ver) in &resolved {
        // Cache the package, then install it.
        let registry_files = cfg.registry.join(pkg).join(ver).join("files");
        let cache_dir = cfg.cache.join(format!("{}-{}", pkg, ver));
        copy_dir(&registry_files, &cache_dir).map_err(|e| e.to_string())?;

        let install_target = cfg.install_dir.join(pkg);
        let _ = fs::remove_dir_all(&install_target);
        copy_dir(&cache_dir, &install_target).map_err(|e| e.to_string())?;

        lock.packages.insert(pkg.clone(), ver.clone());
        println!("  + {}@{}", pkg, ver);
    }
    save_lock(cfg, &lock);
    println!("Installed. Lock file updated.");
    Ok(())
}

fn cmd_remove(cfg: &Config, name: &str) -> Result<(), String> {
    let mut lock = load_lock(cfg);
    if lock.packages.remove(name).is_none() {
        return Err(format!("'{}' is not installed", name));
    }
    let _ = fs::remove_dir_all(cfg.install_dir.join(name));
    save_lock(cfg, &lock);
    println!("Removed {}.", name);
    Ok(())
}

fn cmd_update(cfg: &Config) -> Result<(), String> {
    let lock = load_lock(cfg);
    if lock.packages.is_empty() {
        println!("Nothing installed.");
        return Ok(());
    }
    let names: Vec<String> = lock.packages.keys().cloned().collect();
    for name in names {
        let current = lock.packages.get(&name).cloned().unwrap_or_default();
        if let Some(latest) = latest_version(cfg, &name) {
            if version_key(&latest) > version_key(&current) {
                println!("Updating {} {} -> {}", name, current, latest);
                cmd_install(cfg, &name)?;
            } else {
                println!("{} is up to date ({}).", name, current);
            }
        }
    }
    Ok(())
}

fn cmd_list(cfg: &Config) {
    let lock = load_lock(cfg);
    if lock.packages.is_empty() {
        println!("No packages installed.");
        return;
    }
    println!("Installed packages:");
    for (name, ver) in &lock.packages {
        println!("  {} @ {}", name, ver);
    }
}

fn parse_spec(spec: &str) -> (String, Option<String>) {
    match spec.split_once('@') {
        Some((n, v)) => (n.to_string(), Some(v.to_string())),
        None => (spec.to_string(), None),
    }
}

fn usage() {
    eprintln!(
        "clawpkg — a minimal package manager\n\n\
         Usage:\n  \
         clawpkg install <name[@version]>\n  \
         clawpkg remove <name>\n  \
         clawpkg update\n  \
         clawpkg list\n\n\
         Registry path: $CLAWPKG_REGISTRY (default ./registry)\n\
         Built by clavexis — github.com/clavexis"
    );
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let cfg = Config::new();

    let result = match args.get(1).map(|s| s.as_str()) {
        Some("install") => match args.get(2) {
            Some(spec) => cmd_install(&cfg, spec),
            None => {
                usage();
                exit(1);
            }
        },
        Some("remove") => match args.get(2) {
            Some(name) => cmd_remove(&cfg, name),
            None => {
                usage();
                exit(1);
            }
        },
        Some("update") => cmd_update(&cfg),
        Some("list") => {
            cmd_list(&cfg);
            Ok(())
        }
        _ => {
            usage();
            exit(if args.len() <= 1 { 0 } else { 1 });
        }
    };

    if let Err(e) = result {
        eprintln!("error: {}", e);
        exit(1);
    }
}
