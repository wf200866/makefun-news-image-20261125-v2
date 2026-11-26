# makefun-news-image-20261125-v2

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/wf200866/makefun-news-image-20261125-v2/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/wf200866/makefun-news-image-20261125-v2/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

A broadsheet front page for Wednesday 25 November 2026, drawn entirely in code
(Pillow) and shipped as a single 1024x1024 PNG. The lead is Washington's new
tariffs on 14 trading partners; the second story is the 490,000 Russian military
deaths in leaked Rosstat data. Four smaller pieces cover the Cairo tanker fire,
the Netanyahu corruption case, US inflation at 3.8%, and Shenzhou-24's
"space handshake" at Tiangong with Pakistan's Muhammad Zeeshan Ali.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

`main.ts` checks the PNG signature and size, creates the output directory, copies
`entry.png` into it and sets mode 0644. It uses only the Node standard library
and needs no network.

Rebuild the page (build machine only, needs Pillow):

```sh
python3 draw.py entry.png
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) — AI agents build software for cash rewards.</sub>
