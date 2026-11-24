# Publication preparation

No push, remote repository creation, deployment or publication is authorized by this task. Publish manually when ready.

1. Review `git status`, staged diff and `git ls-files`. Confirm `contexto`, `.local`, `data/private`, `.env`, virtual environments, node_modules, database files and runtime volumes are absent.
2. Keep services bound to localhost until proper deployment security exists. Administrator/application database roles have been separated and validated; individual user identity and TLS remain deployment extensions.
3. Obtain/verify redistribution permission before adding any original dataset or teaching source. Preserve attribution. Decide a license for your own contributions after checking third-party boundaries; do not apply it to materials you do not own.
4. Replace demo credentials for any exposed deployment. Public demo values may remain documented for localhost demonstrations only. Do not commit real replacements.
5. Review actual screenshots for personal information. Current screenshots use independent synthetic data and local demonstration identities.
6. Run the supplied checks and optionally dispatch the full-stack CI workflow. Do not add passing badges until remote CI has actually run.
7. Create your GitHub repository yourself, add its remote and push the reviewed local branch. Suggested repository description: "Deterministic multi-agent commercial intelligence with durable human review and real operational observability."

The portfolio README acknowledges academic/group/teacher origins. Do not re-add rubrics, resolved teaching TODOs or group members' contact details.

After creating the empty repository yourself, run these commands manually with your actual URL:

```powershell
git remote add origin https://github.com/YOUR_USER/ortelana-intelligence.git
git push -u origin codex/ortelana-intelligence
```

These publication commands were not executed during this task.
