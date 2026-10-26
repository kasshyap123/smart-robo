# Repository maintenance

Repository: https://github.com/kasshyap123/smart-robo

Keep component firmware separate from integrated rover firmware as it is added.
Update the README when hardware capabilities change. The website is a local
simulation until live communication is implemented.

From the `website` directory, run:

```sh
node scripts/build.mjs
node scripts/check.mjs
```

Generated `website/dist/` is ignored by Git. The build includes only public-facing
website assets in that folder; CAD source stays in the source repository.

Public scope is code, CAD, website assets, and setup guides. Do not add audio
samples, precompiled firmware, test logs, or test-result records without revisiting
the owner's publication preference. Keep `.env` and credentials out of commits.
