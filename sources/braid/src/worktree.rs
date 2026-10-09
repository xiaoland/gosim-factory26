use std::path::{Path, PathBuf};

use git2::{ErrorClass, ErrorCode, Repository};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum WorktreeError {
    #[error("repository {0} is not a Git repository")]
    NotRepository(PathBuf),
    #[error("work directory {0} already exists but is not the requested clone")]
    TargetConflict(PathBuf),
    #[error("Git operation failed: {0}")]
    Git(String),
    #[error("cannot prepare work directory {path}: {source}")]
    Io { path: PathBuf, source: std::io::Error },
}

impl From<git2::Error> for WorktreeError {
    fn from(error: git2::Error) -> Self {
        Self::Git(error.to_string())
    }
}

#[derive(Debug, Clone)]
pub struct WorktreeRequest<'a> {
    pub source: &'a Path,
    pub target: &'a Path,
    pub git: &'a Path,
    pub head_ref: &'a str,
    pub local_branch: &'a str,
    pub member_login: &'a str,
}

#[derive(Debug, Clone)]
pub struct ProvisionedWorktree {
    pub source: PathBuf,
    pub path: PathBuf,
    pub head_ref: String,
    pub local_branch: String,
}

pub fn provision(request: &WorktreeRequest<'_>) -> Result<ProvisionedWorktree, WorktreeError> {
    let source = tokio::task::block_in_place(|| canonical_repository(request.source))?;
    if !Repository::open(&source)?.is_bare() {
        return Err(WorktreeError::NotRepository(source));
    }
    if request.target.exists() {
        return verify_existing(request, &source);
    }
    if let Some(parent) = request.target.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|source| WorktreeError::Io { path: parent.to_path_buf(), source })?;
    }
    let target = request
        .target
        .to_str()
        .ok_or_else(|| WorktreeError::Git("work directory path is not UTF-8".into()))?;
    let origin =
        source.to_str().ok_or_else(|| WorktreeError::Git("origin path is not UTF-8".into()))?;
    let start_branch = request.head_ref.trim_start_matches("refs/heads/");
    tokio::task::block_in_place(|| {
        if let Err(error) = run_git(
            request.git,
            None,
            &["clone", "--no-local", "--branch", start_branch, origin, target],
        ) {
            if request.target.exists() {
                std::fs::remove_dir_all(request.target).map_err(|source| WorktreeError::Io {
                    path: request.target.to_path_buf(),
                    source,
                })?;
            }
            return Err(error);
        }
        if request.local_branch != start_branch {
            run_git(request.git, Some(request.target), &["switch", "-c", request.local_branch])?;
        }
        exclude_private_notes(request.target)?;
        set_member_identity(request.target, request.member_login, request.git)?;
        Ok::<(), WorktreeError>(())
    })?;
    verify_existing(request, &source)
}

pub fn set_member_identity(
    path: &Path,
    member_login: &str,
    git: &Path,
) -> Result<(), WorktreeError> {
    run_git(git, Some(path), &["config", "--local", "user.name", &format!("@{member_login}")])?;
    run_git(
        git,
        Some(path),
        &["config", "--local", "user.email", &format!("{member_login}@braid.local")],
    )?;
    Ok(())
}

pub fn resume(
    path: &Path,
    origin: &Path,
    member_login: &str,
    git: &Path,
) -> Result<(), WorktreeError> {
    let target = path
        .canonicalize()
        .map_err(|source| WorktreeError::Io { path: path.to_path_buf(), source })?;
    let repo =
        Repository::open(&target).map_err(|_| WorktreeError::TargetConflict(target.clone()))?;
    let expected = canonical_repository(origin)?;
    let remote = run_git(git, Some(&target), &["remote", "get-url", "origin"])?;
    if repo.is_bare()
        || repo.workdir() != Some(target.as_path())
        || Path::new(&remote).canonicalize().ok().as_deref() != Some(expected.as_path())
    {
        return Err(WorktreeError::TargetConflict(target));
    }
    set_member_identity(&target, member_login, git)
}

fn exclude_private_notes(target: &Path) -> Result<(), WorktreeError> {
    let exclude = Repository::open(target)?.path().join("info").join("exclude");
    let existing = std::fs::read_to_string(&exclude).unwrap_or_default();
    if existing.lines().any(|line| line.trim() == ".braid/") {
        return Ok(());
    }
    let mut updated = existing;
    if !updated.is_empty() && !updated.ends_with('\n') {
        updated.push('\n');
    }
    updated.push_str(".braid/\n");
    std::fs::write(&exclude, updated).map_err(|source| WorktreeError::Io { path: exclude, source })
}

fn verify_existing(
    request: &WorktreeRequest<'_>,
    source: &Path,
) -> Result<ProvisionedWorktree, WorktreeError> {
    let target = request
        .target
        .canonicalize()
        .map_err(|source| WorktreeError::Io { path: request.target.to_path_buf(), source })?;
    let repo =
        Repository::open(&target).map_err(|_| WorktreeError::TargetConflict(target.clone()))?;
    if repo.is_bare() || repo.workdir() != Some(target.as_path()) || repo.path() == source {
        return Err(WorktreeError::TargetConflict(target));
    }
    let head = repo.head()?;
    if head.shorthand()? != request.local_branch {
        return Err(WorktreeError::TargetConflict(target));
    }
    let remote = run_git(request.git, Some(&target), &["remote", "get-url", "origin"])?;
    if Path::new(&remote).canonicalize().ok().as_deref() != Some(source) {
        return Err(WorktreeError::TargetConflict(target));
    }
    exclude_private_notes(&target)?;
    set_member_identity(&target, request.member_login, request.git)?;
    Ok(ProvisionedWorktree {
        source: source.to_path_buf(),
        path: target,
        head_ref: request.head_ref.to_owned(),
        local_branch: request.local_branch.to_owned(),
    })
}

fn canonical_repository(path: &Path) -> Result<PathBuf, WorktreeError> {
    if !path.is_dir() {
        return Err(WorktreeError::NotRepository(path.to_path_buf()));
    }
    Repository::discover(path)
        .map(|repo| repo.workdir().map_or_else(|| repo.path().to_path_buf(), Path::to_path_buf))
        .map_err(|error| {
            if error.class() == ErrorClass::Repository && error.code() == ErrorCode::NotFound {
                WorktreeError::NotRepository(path.to_path_buf())
            } else {
                WorktreeError::Git(error.to_string())
            }
        })
}

fn run_git(git: &Path, cwd: Option<&Path>, args: &[&str]) -> Result<String, WorktreeError> {
    let mut command = std::process::Command::new(git);
    if let Some(cwd) = cwd {
        command.arg("-C").arg(cwd);
    }
    let output = command
        .args(args)
        .output()
        .map_err(|source| WorktreeError::Io { path: cwd.unwrap_or(git).to_path_buf(), source })?;
    if !output.status.success() {
        return Err(WorktreeError::Git(format!(
            "git {} failed: {}",
            args.join(" "),
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_owned())
}

/// A review clone fetches a retained ref rather than following the live PR branch.
pub struct ReviewWorktreeRequest<'a> {
    pub source: &'a Path,
    pub target: &'a Path,
    pub git: &'a Path,
    pub commit: &'a str,
    pub retained_ref: &'a str,
    pub local_branch: &'a str,
    pub member_login: &'a str,
}
pub fn provision_review(
    request: &ReviewWorktreeRequest<'_>,
) -> Result<ProvisionedWorktree, WorktreeError> {
    let source = canonical_repository(request.source)?;
    if !Repository::open(&source)?.is_bare() {
        return Err(WorktreeError::NotRepository(source));
    }
    if !request.target.exists() {
        if let Some(parent) = request.target.parent() {
            std::fs::create_dir_all(parent)
                .map_err(|source| WorktreeError::Io { path: parent.to_path_buf(), source })?;
        }
        let target = request
            .target
            .to_str()
            .ok_or_else(|| WorktreeError::Git("review path is not UTF-8".into()))?;
        let origin = source
            .to_str()
            .ok_or_else(|| WorktreeError::Git("review origin is not UTF-8".into()))?;
        run_git(request.git, None, &["clone", "--no-local", "--no-checkout", origin, target])?;
        run_git(request.git, Some(request.target), &["fetch", "origin", request.retained_ref])?;
        let fetched = run_git(request.git, Some(request.target), &["rev-parse", "FETCH_HEAD"])?;
        if fetched != request.commit {
            return Err(WorktreeError::Git(format!(
                "retained review ref {} resolved to {fetched}, expected {}",
                request.retained_ref, request.commit
            )));
        }
        run_git(
            request.git,
            Some(request.target),
            &["switch", "-c", request.local_branch, request.commit],
        )?;
        exclude_private_notes(request.target)?;
    }
    verify_review(request.target, &source, request.commit, request.member_login, request.git)?;
    let path = request
        .target
        .canonicalize()
        .map_err(|source| WorktreeError::Io { path: request.target.to_path_buf(), source })?;
    let branch = run_git(request.git, Some(&path), &["symbolic-ref", "--short", "HEAD"])?;
    if branch != request.local_branch {
        return Err(WorktreeError::TargetConflict(path));
    }
    Ok(ProvisionedWorktree {
        source,
        path,
        head_ref: request.retained_ref.into(),
        local_branch: request.local_branch.into(),
    })
}

/// Verify without resetting: dirty files remain available as review evidence.
pub fn verify_review(
    path: &Path,
    origin: &Path,
    commit: &str,
    member: &str,
    git: &Path,
) -> Result<(), WorktreeError> {
    resume(path, origin, member, git)?;
    let actual = run_git(git, Some(path), &["rev-parse", "HEAD"])?;
    if actual != commit {
        return Err(WorktreeError::Git(format!(
            "review checkout HEAD is {actual}, expected frozen candidate {commit}"
        )));
    }
    exclude_private_notes(path)
}
