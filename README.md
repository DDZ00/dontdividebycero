# Don't Divide by Cero!

> A gamified, self-checking Python notebook for teaching **data analysis with pandas**.
> Students "free a hijacked network" by computing real statistics — there are no answers to copy, only calculations to run.

A teaching resource for data analysis, designed for **Year 11 / GCSE-level** learners (approx. ages 15–16) and easily scaled up or down. Part of my EdTech portfolio, with a focus on **pedagogical innovation** and **responsible, ethical use of AI and data**.

---

## The idea in one paragraph

An "AI agentic maths tutor divided by zero and went insane," hijacking the school network. To take it back, students must prove they know their statistics. The data — 1,000 rows of synthetic network logs — hides three secret numbers in **every cycle**. Each number is the *result of a statistical operation* (a median, a mode, a count of unique values, an outlier). Students compute the three numbers, use them to decrypt a hidden message, and the message tells them what to do next. Three cycles, one final truth.

**Why it works:** the secret numbers are never written in the data. You cannot search, `Ctrl-F`, or "ask an AI" your way through it — if you don't run the calculation, you don't get the number, and a wrong calculation decrypts to gibberish. The exercise **validates itself**, so students get instant, honest feedback without an answer key.

---

## Learning objectives

By completing the three cycles, students practise:

- **Boolean filtering** — single and compound conditions (`&`, `|`)
- **Measures of central tendency** — `mean`, `median`, `mode` over filtered subgroups
- **Frequency analysis** — `value_counts`, unique vs. repeated values, least/most frequent
- **Counting distinct values** — `nunique`
- **Outlier detection** — distance from the mean
- **Selecting extreme rows** — maximum value, most recent timestamp
- **Applying functions row-by-row** — `apply` with a hashing function, then hash-matching
- **Reading and trusting your own analysis** — wrong stats produce an unreadable message

---

## Syllabus — pandas cheatsheet

Every pandas command used across the three cycles, what it does, and where it appears. This is the explicit content being taught.

### Loading and inspecting data

| Command | What it does | Cycle |
|---|---|---|
| `pd.read_csv('network_logs.csv')` | Load a CSV file into a DataFrame (a table). | 1, 2, 3 |
| `df.head()` | Show the first 5 rows to preview the data. | 1, 2, 3 |
| `len(df)` | Count how many rows there are. | 1, 3 |

### Filtering rows (boolean conditions)

| Command | What it does | Cycle |
|---|---|---|
| `df[df['col'] == value]` | Keep only the rows where a column equals a value. | 1, 2, 3 |
| `df[(cond1) & (cond2)]` | Combine conditions with **AND** — both must be true. | 1 |
| `df['col'].isin(list)` | Test whether each value is in a list; used to keep matching rows. | 2 |
| `df['col'].str.startswith('ENC:', na=False)` | Keep rows whose text starts with a given prefix. | 1, 2 |
| `df.copy()` | Make an independent copy before adding columns (avoids warnings). | 3 |

### Descriptive statistics

| Command | What it does | Cycle |
|---|---|---|
| `series.mean()` | The **mean** (average) of a column. | 3 |
| `series.median()` | The **median** (middle value when sorted). | 1, 2 |
| `series.mode()` | The **mode** (most frequent value). | 1, 2, 3 |
| `series.abs()` | Absolute value — distance ignoring the sign. | 3 |

### Frequencies and uniqueness

| Command | What it does | Cycle |
|---|---|---|
| `series.value_counts()` | Count how many times each value appears. | 2, 3 |
| `series.nunique()` | Count how many **distinct** values there are. | 1 |
| `counts[counts == 1]` | Filter a counts table to values that appear exactly once. | 2 |
| `counts[counts >= 2]` | Filter a counts table to values that appear two or more times. | 3 |
| `(series == 1).sum()` | Count how many entries meet a condition (True counts as 1). | 2 |

### Selecting specific rows and values

| Command | What it does | Cycle |
|---|---|---|
| `series.iloc[0]` | Get a value by **position** (here, the first one). | 1, 2, 3 |
| `df.loc[row, 'col']` | Get a value by **label/index** and column name. | 1 |
| `series.idxmax()` | The index (label) of the **maximum** value. | 1 |
| `series.idxmin()` | The index (label) of the **minimum** value. | 3 |
| `df.sort_values('col', ascending=False)` | Sort rows by a column — used to find the largest or most recent. | 3 |

### Transforming data

| Command | What it does | Cycle |
|---|---|---|
| `df['new_col'] = ...` | Create a new column. | 3 |
| `series.apply(func)` | Run a function on every value (here, hashing each timestamp). | 3 |
| `series - value` | Vectorised arithmetic — operate on a whole column at once. | 3 |

---

## What makes it innovative

| Principle | How the game delivers it |
|---|---|
| **No "copy the answer"** | Keys are emergent statistics, never literals in the dataset. |
| **AI-resistant by design** | A chatbot can't shortcut it without actually doing the data work. |
| **Self-validating feedback** | Correct maths gives a readable message; wrong maths gives noise. No marking required. |
| **Narrative and motivation** | A light cyber-mystery turns "calculate the median" into "find patient zero." |
| **Progressive scaffolding** | All three cycles are guided fill-in-the-blanks with one-line hints, building from simpler to harder statistics. |
| **Reusable and remixable** | Change one seed to get a fresh dataset; same gameplay, no two classes identical. |

---

## Ethics and AI-literacy angle

This resource is built to teach *with* AI responsibly, not to outsource thinking to it:

- **Synthetic data only.** Every row is generated — there is **no real personal data, no real IPs, no PII**. Safe to share and reuse.
- **AI as a cautionary character, not an oracle.** The "tutor that broke" frames AI as a tool that can fail, inviting discussion about over-reliance and verification.
- **Effort-honest assessment.** Because the puzzle can't be solved by prompting a chatbot for the answer, it rewards genuine understanding.
- **Toy cryptography, clearly labelled.** The RSA here is deliberately tiny and *educational only* — a hook for curiosity about how encryption works, never presented as secure.

---

## What's in the repository

| File | Audience | Purpose |
|---|---|---|
| `cycle_1.ipynb` | Student | **The Fallen User** — first challenge (fill the blanks); introduces the core pattern. |
| `cycle_2.ipynb` | Student | **The Busy IP** — guided practice (fill the blanks). |
| `cycle_3.ipynb` | Student | **The Zeta Outlier** — final challenge (fill the blanks). |
| `tutor_tools.py` | Student | Helper module: `decrypt_message()` (toy RSA) and `sha256_hex()` (hashing). Imported by every notebook. |
| `network_logs.csv` | Student | The dataset: 1,000 rows of synthetic logs (incl. ~100 decoy/"trap" rows). |
| `generate_csv.py` | **Teacher** | Regenerates the dataset from the spec. Lets you remix difficulty. |
| `walkthrough.json` | **Teacher** | The authoritative spec and **answer key** — exact rule for every `p`, `q`, `e` and every message. |

> **For teachers:** `walkthrough.json` is the answer key and `generate_csv.py` reveals how values are planted. This repository is intended as a **teacher resource**. If you hand the game to students, share only `cycle_*.ipynb`, `tutor_tools.py`, and `network_logs.csv`.

---

## Step-by-step: running the game

### Requirements
- Python 3.10+ with **Jupyter** (Jupyter Lab/Notebook, VS Code, or Google Colab)
- Packages: `pandas`, `sympy` (each notebook installs them in its first cell)

### Option A — Run locally
```bash
git clone git@github.com:DDZ00/dontdividebycero.git
cd dontdividebycero
pip install pandas sympy jupyterlab
jupyter lab        # then open cycle_1.ipynb
```

### Option B — Google Colab (no install)
1. Upload `cycle_1.ipynb`, `tutor_tools.py`, and `network_logs.csv` to the same Colab session.
2. Run the first cell (`!pip install pandas sympy`).
3. Play. Repeat with `cycle_2` and `cycle_3`.

### How a student plays
1. **Open `cycle_1.ipynb`** and run the setup cells (install, load the CSV, import the helpers).
2. Work through each step: compute `p`, `q`, and `e` from the statistical clue.
3. Run the decrypt cell to get a readable **message** with instructions for the next cycle.
4. **Carry the clue forward:** Cycle 1 reveals an *IP* (use it in Cycle 2); Cycle 2 reveals a *server and timestamp* (use them in Cycle 3).
5. Finish Cycle 3 to reveal the final message and free the network.

> Each notebook is **self-contained** (its own setup) and ends by telling students exactly what to take into the next one.

---

## Teacher notes

- **Suggested flow:** work through `cycle_1.ipynb` together as a class to establish the pattern, then let students attempt `cycle_2` and `cycle_3` in pairs.
- **Answer key:** all expected values and messages are in `walkthrough.json`.
- **Remix for a fresh run / anti-plagiarism:** edit `walkthrough.json`, then regenerate:
  ```bash
  python generate_csv.py
  ```
  - Change `random_seed` for a different-looking dataset with identical gameplay (great for a new cohort).
  - Change `rows_trap` for more/fewer decoys to tune difficulty.
  - Change the primes or `plain_message` (the generator re-encrypts and validates that each statistic still produces the declared key).
- **Differentiation:** stronger students can be asked to *explain why* each statistic is robust to the trap rows; others can lean on the in-cell hints and the class walkthrough of Cycle 1.

---

## Curriculum links

- **Data handling and statistics:** averages (mean/median/mode), frequency, outliers, distinct counts.
- **Computing / data science:** pandas, filtering, functions, hashing, introduction to encryption concepts.
- **Cross-curricular:** logical reasoning, evidence-based conclusions, digital and AI literacy.

Aligned to Year 11 / GCSE Computer Science and Maths data-handling outcomes; adaptable for KS5 or introductory undergraduate data analysis.

---

## License

This work is licensed under a
[**Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**](https://creativecommons.org/licenses/by-nc-sa/4.0/).

You are free to **share** and **adapt** this material for **non-commercial** purposes, provided you give appropriate **credit** and distribute your contributions under the **same license**. See [`LICENSE`](LICENSE) for details.

---

## Author

Created by **Diego De Zela**.
Feedback, forks, and classroom stories are welcome.
