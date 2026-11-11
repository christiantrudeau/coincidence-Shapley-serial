# The dynamic program for the Shapley value

This note describes the algorithm in [`src/shapdp.py`](../src/shapdp.py) (function `shapley_opt_div`).
It computes the exact Shapley value of the optimistic cost function in scheduling problems with
discretely divisible jobs, in $O(n^3k)$ operations, where $n$ is the number of agents and $k$ the number
of servers. Section 6.1 of the paper summarizes it in one paragraph; this note gives the derivation, the
algorithm, its cost, how it is checked, and a worked example.

## 1. What is computed

We set $w_0 = 1$, since the Shapley value is proportional to $w_0$. Number the agents so that
$l_1 \le l_2 \le \dots \le l_n$, with ties broken by index. Coalition costs do not depend on how ties
are broken, because jobs of equal length are interchangeable. For a coalition $S$ and a member $t$ of
$S$, let

```math
L_t(S) = \sum_{s \in S,\ s \le t} l_s
```

be the total length of the members of $S$ up to and including $t$ (written $l_{S_{\le t}}$ in the
paper). When $S$ is served alone, its tasks fill the $k$ servers period by period, shortest jobs
first, and agent $t$ finishes at the end of period $\lceil L_t(S)/k \rceil$. The optimistic cost is
therefore (Table 1 of the paper)

```math
C(S) = \sum_{t \in S} \left\lceil \frac{L_t(S)}{k} \right\rceil .
```

The Shapley value of agent $i$ is

```math
Sh_i = \sum_{S \subseteq N \setminus \lbrace i \rbrace} \pi(|S|)\,\bigl(C(S \cup \lbrace i \rbrace) - C(S)\bigr),
\qquad \pi(s) = \frac{s!\,(n-s-1)!}{n!}.
```

Equivalently, $Sh_i$ is the expected increase in cost when agent $i$ joins the agents who precede it in
a uniformly random order. Summing over coalitions takes $2^{n-1}$ terms per agent, about $6 \times 10^{29}$
with the 100 agents of the largest problems in the study.

## 2. The idea

The marginal cost of agent $i$ depends on the coalition $S$ only through a few summaries:

- how many members of $S$ have shorter jobs than $i$, and their total length;
- for each member $t$ of $S$ with a longer job, the remainder of $L_t(S)$ modulo $k$.

The algorithm groups coalitions by these summaries, counts how many coalitions fall in each group, and
weights each group by its probability. The counting is done one agent at a time, which is the dynamic
program.

## 3. Step 1: splitting the marginal cost

Fix agent $i$ and a coalition $S$ that does not contain $i$. Split $S$ into the members with shorter
jobs, $A = S \cap \lbrace 1, \dots, i-1 \rbrace$, and the members with longer jobs,
$S \cap \lbrace i+1, \dots, n \rbrace$. Adding $i$ changes nothing for the members of $A$, which are
served before $i$. Agent $i$ itself finishes at the end of period $\lceil (L(A) + l_i)/k \rceil$, where
$L(A)$ is the total length of $A$. Each member $t$ with a longer job is served after $i$, and its tasks
are pushed back by $l_i$ units of work. Hence

```math
C(S \cup \lbrace i \rbrace) - C(S)
= \underbrace{\left\lceil \frac{L(A) + l_i}{k} \right\rceil}_{\text{own term}}
+ \underbrace{\sum_{t \in S,\ t > i} \left( \left\lceil \frac{L_t(S) + l_i}{k} \right\rceil - \left\lceil \frac{L_t(S)}{k} \right\rceil \right)}_{\text{delay term}} .
```

## 4. Step 2: only remainders matter

**Delay term.** Write $x = qk + r$ with $0 \le r < k$. Then $\lceil x/k \rceil = q + \mathbf{1}[r > 0]$
and $\lceil (x + l_i)/k \rceil = q + \lceil (r + l_i)/k \rceil$, so

```math
\left\lceil \frac{x + l_i}{k} \right\rceil - \left\lceil \frac{x}{k} \right\rceil
= \delta_i(r) := \left\lceil \frac{r + l_i}{k} \right\rceil - \mathbf{1}[r > 0] .
```

The delay that agent $i$ imposes on a member $t$ depends on $L_t(S)$ only through its remainder
$r = L_t(S) \bmod k$, that is, through how many of the $k$ slots of agent $t$'s last period are used.
This is the packing effect of Remark 3 in the paper: it vanishes when every length is a multiple of $k$.

**Own term.** For any integer $y \ge 0$, $\lceil y/k \rceil = \bigl(y + ((-y) \bmod k)\bigr)/k$. The own
term is a linear part, $(L(A) + l_i)/k$, plus a part that depends on $L(A)$ only through its remainder
modulo $k$.

## 5. Step 3: probabilities that depend only on sizes

Use the random-order form of the Shapley value. Let $\mathrm{Pred}_i$ be the set of agents who precede
$i$ in a uniformly random order.

**Own term.** It depends on $S = \mathrm{Pred}_i$ only through $A$. For a given set
$A \subseteq \lbrace 1, \dots, i-1 \rbrace$ with $|A| = a$, the probability that the agents of
$\lbrace 1, \dots, i-1 \rbrace$ who precede $i$ are exactly those of $A$ depends only on the relative order of
agents $1, \dots, i$. Agent $i$ is in position $a+1$ among them with probability $1/i$, and the $a$
agents before it are then a uniformly random subset of size $a$. Hence

```math
\alpha_i(a) = \frac{1}{i\binom{i-1}{a}} = \frac{a!\,(i-1-a)!}{i!} .
```

**Delay term.** The delay imposed on a longer job $t > i$ depends on $\mathrm{Pred}_i$ only through two
things: whether $t$ precedes $i$, and the set $A'$ of agents of $\lbrace 1, \dots, t-1 \rbrace \setminus \lbrace i \rbrace$
who precede $i$. In that case $L_t(\mathrm{Pred}_i) = L(A') + l_t$. Among the $t$ agents
$\lbrace 1, \dots, t \rbrace$, the probability that the agents preceding $i$ are exactly
$A' \cup \lbrace t \rbrace$, with $|A'| = a$, is

```math
\beta_t(a) = \frac{1}{t\binom{t-1}{a+1}} = \frac{(a+1)!\,(t-2-a)!}{t!} .
```

As a check, $\sum_a \binom{t-2}{a}\beta_t(a) = 1/2$, the probability that $t$ precedes $i$.

Combining Steps 1 to 3,

```math
Sh_i = \sum_{A \subseteq \lbrace 1,\dots,i-1 \rbrace} \alpha_i(|A|) \left\lceil \frac{L(A) + l_i}{k} \right\rceil
+ \sum_{t = i+1}^{n} \ \sum_{A' \subseteq \lbrace 1,\dots,t-1 \rbrace \setminus \lbrace i \rbrace} \beta_t(|A'|)\ \delta_i\bigl((L(A') + l_t) \bmod k\bigr) .
```

The code computes the same weights as sums of Shapley weights,
$\alpha_i(a) = \sum_b \binom{n-i}{b}\pi(a+b)$ and $\beta_t(a) = \sum_b \binom{n-t}{b}\pi(a+1+b)$, which
average over the agents that do not matter (arrays `V` and `W`). Both forms are equal.

## 6. Step 4: counting subsets by size and remainder

Apart from the linear part of the own term, both sums depend on the subsets only through their size and
the remainder of their total length modulo $k$. For a set $G$ of agents, let

```math
D_G[a][r] = \#\lbrace A \subseteq G : |A| = a,\ L(A) \equiv r \pmod k \rbrace ,
\qquad 0 \le a \le n-1,\ 0 \le r \le k-1 .
```

This table is built one agent at a time. Start from $D_\emptyset[0][0] = 1$ and zeros elsewhere. Adding
an agent $j$ of length $l_j$ either leaves a subset unchanged or adds $j$ to it:

```math
D_{G \cup \lbrace j \rbrace}[a][r] = D_G[a][r] + D_G[a-1]\bigl[(r - l_j) \bmod k\bigr] .
```

Each update takes $O(nk)$ operations. Writing $\Lambda_i = l_1 + \dots + l_{i-1}$ and using that each
shorter agent belongs to $\binom{i-2}{a-1}$ of the subsets of size $a$, the two parts of $Sh_i$ become

```math
\text{own}_i = \sum_{a=0}^{i-1} \alpha_i(a) \left[ \frac{\binom{i-2}{a-1}\Lambda_i + \binom{i-1}{a} l_i}{k}
+ \sum_{r=0}^{k-1} D_{\lbrace 1,\dots,i-1 \rbrace}[a][r]\,\frac{(-r-l_i) \bmod k}{k} \right],
```

```math
\text{delay}_i = \sum_{t=i+1}^{n} \sum_{a=0}^{t-2} \beta_t(a) \sum_{r=0}^{k-1}
D_{\lbrace 1,\dots,t-1 \rbrace \setminus \lbrace i \rbrace}[a][r]\ \delta_i\bigl((r + l_t) \bmod k\bigr),
```

with $\binom{i-2}{a-1} = 0$ when $a = 0$. Moving from $t$ to $t+1$ adds agent $t$ to the counted set, so
the delay term needs one update per longer job.

## 7. The algorithm

```
sort the agents by length (ties by index)
for each agent i = 1, ..., n:
    D <- table of {1, ..., i-1}          (i-1 updates);  Lambda <- l_1 + ... + l_{i-1}
    own <- formula of Step 4 with alpha_i
    delay <- 0
    for t = i+1, ..., n:
        delay <- delay + sum over a, r of beta_t(a) * D[a][r] * delta_i((r + l_t) mod k)
        D <- D with agent t added
    Sh_i <- w0 * (own + delay)
```

**Cost.** For each agent, at most $n$ updates and $n$ weighted sums over the table, each $O(nk)$. This
gives $O(n^2k)$ per agent and $O(n^3k)$ in total, with $O(nk)$ memory. The lengths enter only through
$\Lambda_i$ and their remainders modulo $k$, so the running time does not depend on how long the jobs
are. It grows linearly with $k$, not with its logarithm, so the algorithm is pseudo-polynomial. This is
consistent with the #P-completeness result of Aziz and Banerjee (2025) cited in the paper. Run times are
in [`machine_and_run_times.md`](machine_and_run_times.md): about 0.35 s per problem with 100 agents.

The serial rule needs only the $n$ total costs $C(N, \underline{\theta}^q)$ (function `serial_div`).

## 8. Numerical accuracy and checks

The counts $D[a][r]$ can be very large, up to $\binom{n-1}{a}$, about $5 \times 10^{28}$ when $n = 100$.
Counts above $2^{53} \approx 9 \times 10^{15}$ are not stored exactly in double precision, but each is
rounded with a relative error of only about $10^{-16}$. The weights $\alpha_i(a)$ and $\beta_t(a)$ are of
the order of their inverses, so the products are of moderate size, and since every term of the sums is
non-negative, no cancellation magnifies the rounding. To rule out rounding problems, the same algorithm
is also implemented in exact rational arithmetic in [`tests/shapdp_exact.py`](../tests/shapdp_exact.py).
The checks are:

| Check | Where |
| --- | --- |
| 400 random problems with up to 11 agents, against the definition by brute force; largest difference about $7 \times 10^{-14}$ (Section 6.1) | `python src/shapdp.py` |
| Exact algorithm against exact brute force; floating-point against exact values on grid problems with up to 50 agents | `tests/test_numerical.py` |
| Shares add up to the total cost; the rules coincide when every length is a multiple of $k$ | `tests/test_numerical.py` |
| Efficiency on all 78,480 problems; 1,080 problems in exact arithmetic | `tests/audit_full_grid.py` |

## 9. Worked example

Take the running example of the paper: $k = 2$ and $l = (2, 3, 6)$. We compute $Sh_2$, with $l_2 = 3$.

- **Own term.** The shorter agents are $\lbrace 1 \rbrace$, so $A = \emptyset$ or $\lbrace 1 \rbrace$, with
  $\alpha_2(0) = \alpha_2(1) = 1/2$. Agent 2 finishes at $\lceil 3/2 \rceil = 2$ or
  $\lceil 5/2 \rceil = 3$, so the own term is $\tfrac12 \cdot 2 + \tfrac12 \cdot 3 = 5/2$.
- **Delay term.** The only longer job is agent 3, and $A' \subseteq \lbrace 1 \rbrace$. If
  $A' = \emptyset$, then $L_3 = 6$, so $r = 0$, the delay is $\delta_2(0) = \lceil 3/2 \rceil = 2$ and
  the weight is $\beta_3(0) = 1/6$. If $A' = \lbrace 1 \rbrace$, then $L_3 = 8$, again $r = 0$ and a
  delay of $2$, with weight $\beta_3(1) = 1/3$. The delay term is $\tfrac16 \cdot 2 + \tfrac13 \cdot 2 = 1$.

So $Sh_2 = 5/2 + 1 = 7/2$. Together with $Sh_1 = 2$ and $Sh_3 = 9/2$, this is the optimistic Shapley value
of Table 2 in the paper, which `python src/shapdp.py` also prints.

## 10. From the formulas to the code

| In this note | In `src/shapdp.py` |
| --- | --- |
| Agents in order of length, $l_1 \le \dots \le l_n$ | `order`, `ls` |
| Agent $i$ (positions from 1) | `ii` (positions from 0), so $i$ = `ii + 1` |
| $\alpha_i(a)$ | `V[n-1-ii][a]` |
| $\beta_t(a)$ | `W[n-1-t][a]`, with `t` counted from 0 |
| $D_G[a][r]$ and its update | `D`, `add_agent` |
| $\Lambda_i$ | `Lam` |
| $\delta_i(r)$ | `delta[r]` |
| $((-r - l_i) \bmod k)/k$ | `modterm[r]` |
| $\delta_i((r + l_t) \bmod k)$ | `rot[r]` |
