# GoalGen Version Control Strategy

**Repository**: `/Users/kalyan/projects/goalgen`
**Current Version**: v0.1.0
**Date**: 2025-12-01

---

## Repository Structure

```
main (protected)
├── v0.1.0 (tag) ← Current baseline
├── feature/* (feature branches)
├── fix/* (bug fix branches)
└── release/* (release preparation branches)
```

---

## Branching Strategy

### Main Branch (`main`)

**Purpose**: Stable, tested code only
**Protection**: Always working, all tests passing
**Merge Requirements**:
- All tests passing (100%)
- E2E validation complete
- Code review (if team grows)
- Documentation updated

### Feature Branches (`feature/*`)

**Naming**: `feature/<issue-number>-<short-description>`
**Examples**:
- `feature/001-rename-langgraph-to-workflow`
- `feature/002-add-frmk-setup-generation`
- `feature/003-memory-checkpointer-fallback`

**Workflow**:
```bash
# Create feature branch
git checkout -b feature/001-rename-langgraph-to-workflow

# Work on feature
# ... make changes ...
git add .
git commit -m "Rename langgraph/ to workflow/ in generators"

# Merge back to main when complete
git checkout main
git merge feature/001-rename-langgraph-to-workflow
git tag v0.2.0
```

### Fix Branches (`fix/*`)

**Naming**: `fix/<issue-number>-<short-description>`
**Examples**:
- `fix/001-template-crash-on-missing-field`
- `fix/002-import-error-in-base-agent`

**Workflow**:
```bash
# Create fix branch
git checkout -b fix/001-template-crash

# Apply fix
# ... make changes ...
git add .
git commit -m "Fix: Template crash on missing deployment field"

# Merge back
git checkout main
git merge fix/001-template-crash
```

### Release Branches (`release/*`)

**Naming**: `release/v<major>.<minor>.<patch>`
**Examples**:
- `release/v0.2.0`
- `release/v1.0.0`

**Workflow**:
```bash
# Create release branch
git checkout -b release/v0.2.0

# Prepare release (update version, docs, etc.)
git commit -m "Prepare v0.2.0 release"

# Merge to main
git checkout main
git merge release/v0.2.0
git tag -a v0.2.0 -m "Version 0.2.0: Feature X complete"
```

---

## Version Numbering (Semantic Versioning)

**Format**: `MAJOR.MINOR.PATCH`

### MAJOR (0.x.x → 1.x.x)
**When**: Breaking changes to public API
- Change spec schema (backward incompatible)
- Change generator CLI interface
- Remove/rename major features

**Example**: v0.x.x → v1.0.0 (production-ready)

### MINOR (x.0.x → x.1.x)
**When**: New features (backward compatible)
- Add new generator
- Add new target
- Enhance existing functionality
- Fix critical gaps

**Example**: v0.1.0 → v0.2.0 (after fixing GAP #7)

### PATCH (x.x.0 → x.x.1)
**When**: Bug fixes only
- Fix template errors
- Fix validation logic
- Fix documentation typos

**Example**: v0.1.0 → v0.1.1 (template hotfix)

---

## Current Version History

### v0.1.0 (2025-12-01) - Baseline Release ✅

**Status**: E2E tested, working code generation

**What's Included**:
- Complete generator system (14 generators)
- Spec validator (50+ rules)
- 62 unit tests (100% passing)
- E2E testing complete
- Documentation (25+ markdown files)

**Test Results**:
```
✅ Code Generation:     100%
✅ Syntax Validation:   100%
✅ Test Pass Rate:      62/62 (100%)
✅ Runtime Execution:   Working (LangGraph builds)
✅ Local Testing:       Enabled (MemorySaver)
```

**Known Issues** (documented, not blocking):
- GAP #1: Missing dependency installation guidance
- GAP #7: langgraph/ directory naming collision (fixed in test_output)

**Commit**: `525ca21`
**Files**: 138 files, 35,186 lines
**Tag**: `v0.1.0`

---

## Upcoming Versions (Planned)

### v0.2.0 - Generator Improvements (Next)

**Planned Changes**:
1. Rename langgraph/ → workflow/ in generators
2. Generate frmk/setup.py automatically
3. Add memory checkpointer fallback to templates
4. Generate QUICKSTART.md

**Target**: 2-3 days
**Branch**: `feature/001-apply-e2e-fixes`

### v0.3.0 - Enhanced Testing

**Planned Changes**:
1. Generate unit tests for agents
2. Add integration test templates
3. Mock LLM testing support
4. Improved test documentation

**Target**: 1 week

### v1.0.0 - Production Ready

**Requirements**:
- All critical gaps resolved
- Azure deployment tested
- Full E2E validation
- Performance benchmarks
- Security audit
- Public documentation

**Target**: 4-6 weeks

---

## Commit Message Convention

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Code style (formatting, no logic change)
- **refactor**: Code restructuring (no feature change)
- **test**: Add/update tests
- **chore**: Build process, dependencies

### Examples

```
feat(langgraph): Rename generated directory to workflow/

- Changes langgraph_dir → workflow_dir in generator
- Updates all templates to use workflow imports
- Fixes GAP #7 (naming collision with installed package)

Resolves: #7
```

```
fix(templates): Add defensive check for deployment.environments

- Prevents crash when optional field missing
- Adds default value fallback
- Updates README template

Fixes: #3
```

```
test(validator): Add tests for nested optional fields

- Tests all deployment.* field combinations
- Tests state_management.* scenarios
- Ensures no crashes on minimal specs
```

---

## Git Workflow Commands

### Create Feature Branch
```bash
git checkout main
git pull  # (if remote exists)
git checkout -b feature/001-my-feature
```

### Commit Changes
```bash
git add <files>
git commit -m "feat(scope): Description"
```

### Merge Feature to Main
```bash
# Make sure tests pass
pytest tests/

# Switch to main
git checkout main

# Merge feature
git merge feature/001-my-feature

# Tag if significant
git tag -a v0.2.0 -m "Version 0.2.0 description"
```

### View History
```bash
# Commit history
git log --oneline --graph

# Tags
git tag -l

# Show specific version
git show v0.1.0
```

### Revert to Previous Version
```bash
# Create branch from tag
git checkout -b hotfix-from-v0.1.0 v0.1.0

# Or reset main (careful!)
git checkout main
git reset --hard v0.1.0
```

---

## Release Checklist

Before tagging a new version:

- [ ] All tests passing (`pytest tests/`)
- [ ] E2E validation complete (if major/minor)
- [ ] IMPLEMENTATION_STATUS.md updated
- [ ] README.md version updated
- [ ] TESTING.md results current
- [ ] Breaking changes documented
- [ ] Migration guide written (if needed)
- [ ] Commit message follows convention
- [ ] Tag message includes changelog

---

## Repository Backup Strategy

### Local Backups
```bash
# Create backup branch
git branch backup-$(date +%Y%m%d)

# Or export as bundle
git bundle create goalgen-backup-$(date +%Y%m%d).bundle --all
```

### Remote Repository (Future)

When ready to push to GitHub:

```bash
# Add remote
git remote add origin https://github.com/username/goalgen.git

# Push main and tags
git push -u origin main
git push --tags
```

**Recommended**: Private repository initially, public after v1.0.0

---

## Maintenance

### Cleanup Old Branches
```bash
# List merged branches
git branch --merged

# Delete merged feature branch
git branch -d feature/001-my-feature
```

### Archive Old Tags
```bash
# Keep major versions
# Delete old patch versions if needed
git tag -d v0.1.1-beta
```

---

## Current Status

```
Repository:    Initialized ✅
Initial Commit: 525ca21 ✅
Baseline Tag:   v0.1.0 ✅
Tests:         62/62 passing ✅
E2E Status:    Complete ✅
```

**Ready for**: Feature development and improvements

---

## Quick Reference

```bash
# Check status
git status

# View history
git log --oneline -10

# View tags
git tag -l

# Current branch
git branch --show-current

# Show changes
git diff

# Show last commit
git show HEAD
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-01
**Maintained By**: GoalGen Team
