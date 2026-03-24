# Claude Code Configuration for Optimization

## Context Management
**Max context size:** 4000 tokens
- Keep context focused on relevant files only
- Avoid reading large log files, database dumps, or binary files

## File Access Guidelines

### ✅ Files to Prioritize
- `src/**/*.{py,js,ts,tsx}` - Source code files
- `config/**/*` - Configuration files
- `*.md` - Documentation files (except large generated ones)
- `requirements.txt`/`package.json` - Dependency files

### ⚠️ Files to Avoid Unless Explicitly Requested
- `vector_db_data/**/*` - Vector database files (often very large)
- `logs/**/*` - Log files (can be massive)
- `tmp/**/*`, `temp/**/*` - Temporary files
- `*.sqlite`, `*.db` - Database files
- `__pycache__/**/*`, `*.pyc` - Python cache files
- `.git/**/*` - Git internal files

## Tool Usage Optimization

### Use Glob for File Discovery
```bash
# Instead of reading entire directories
Glob pattern="src/**/*.py"
```

### Use Grep for Content Search
```bash
# Instead of reading entire files
Grep pattern="def process_" type="py"
```

### Read Files Strategically
- Only read files when necessary for the task
- Use line limits when reading large files: `Read file_path="large_file.log" limit=100`
- For PDFs, always specify page ranges: `Read file_path="doc.pdf" pages="1-5"`

## Performance Tips

### 1. Batch Operations
When multiple independent searches are needed:
```bash
# Run in parallel
Glob pattern="*.py"
Glob pattern="*.js"
```

### 2. Cache Common Patterns
Frequently used file patterns:
- Python source: `src/**/*.py`
- Configuration: `config/**/*.{json,yaml,toml}`
- Tests: `tests/**/*.py`

### 3. Memory Management
- Clear task lists regularly with `/clear-tasks`
- Use `/fast` mode for simple tasks
- Avoid keeping large file contents in conversation history

## Workflow Optimization

### For Code Changes
1. **Always read first** before editing any file
2. **Use Edit tool** instead of Write for small changes
3. **Create commits only when explicitly requested**
4. **Use ExitPlanMode** for non-trivial changes requiring approval

### For Research Tasks
1. **Start with Glob** to find relevant files
2. **Use Grep** to search for specific patterns
3. **Read selectively** - only open files that are likely relevant
4. **Use Agent tool** with Explore agent for complex codebase exploration

## Security Considerations
- **Never read** `.env`, `secrets.*`, `credentials.*` files
- **Avoid executing** Bash commands that could modify system state
- **Always confirm** before making destructive changes (rm, git reset, etc.)

## Auto-Memory Guidelines
Save to memory only:
- Stable project architecture patterns
- User preferences for workflow
- Frequently used file paths
- Solutions to recurring problems

Do NOT save:
- Temporary state or in-progress work
- Session-specific context
- Unverified assumptions

## Example Optimized Workflow
```
# For finding all API endpoints:
1. Glob pattern="src/api/**/*.py"
2. Grep pattern="@app.route" type="py" output_mode="content"
3. Read only the relevant files that contain matches
```

## Performance Monitoring
- If a task is taking too long, use `/cancel` to stop it
- For large operations, use `run_in_background` and check status later
- Monitor token usage with `/token-usage` command

---

**Last updated:** 2026-03-24
**Project:** AI Learning Chat with Agent
**Maintainer:** Claude Code Optimizer