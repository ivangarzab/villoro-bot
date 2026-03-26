# Deployment Guide — VilloroBot on Sparked Host

## Quick Start

VilloroBot deploys on **Sparked Host (Apollo panel)** using a **startup command** that automatically pulls code and installs dependencies.

### Prerequisites

1. **GitHub Personal Access Token (PAT)**
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Scope: `repo`
   - Copy the token (you'll need it once)

2. **Apollo Environment Variable**
   - Log into Apollo panel
   - Set environment variable: `GH_TOKEN=<your-token>`

### Setup (One-time)

1. **Update `requirements.txt`** to use the PAT:
   ```
   kluvs-brain @ git+https://ivangarzab:${GH_TOKEN}@github.com/ivangarzab/kluvs-brain.git
   ```

2. **Commit and push:**
   ```bash
   git add requirements.txt
   git commit -m "Deploy: Use GitHub token for private dependency"
   git push
   ```

3. **Set Apollo startup command** (if not already set):
   ```bash
   if [[ -d .git ]]; then git pull; fi; if [[ ! -z ${PY_PACKAGES} ]]; then pip3 install -U --prefix .local ${PY_PACKAGES}; fi; if [[ -f /home/container/requirements.txt ]]; then pip3 install -U --prefix .local -r requirements.txt; fi; python3 /home/container/${STARTUP_FILE}
   ```

4. **Restart the bot** in Apollo — deployment happens automatically

### Testing Locally

Before deploying to the server, test locally:

```bash
export GH_TOKEN=<your-token>
make update-brain
```

If `make update-brain` succeeds, the deployment will work on the server.

### Troubleshooting

| Issue | Fix |
|-------|-----|
| `Permission denied (publickey)` | Check that `GH_TOKEN` is set in Apollo |
| `ModuleNotFoundError: kluvs_brain` | Verify `requirements.txt` syntax; restart bot |
| Startup hangs | Check internet connectivity; verify token scope includes `repo` |

### Security Notes

- **Never commit the token to git** — always use `${GH_TOKEN}` environment variable
- Token is stored securely in Apollo's environment management
- Rotate the token periodically in GitHub settings
- If the token leaks, revoke it immediately in GitHub

### Updating the Bot

1. Push code changes to `main`
2. Apollo's startup script automatically pulls and reinstalls
3. Bot restarts — no manual deployment needed

### SSH Key Info

This deployment uses **GitHub Personal Access Tokens**, not SSH keys. You don't need to manage SSH credentials on the server.
