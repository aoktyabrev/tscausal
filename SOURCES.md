# SOURCES — дословные цитаты

Правило 0: каждое внешнее число, определение или формула ниже подтверждено дословной
цитатой из выгруженного источника. Выгрузки лежат в `sources/<arXiv-id>/`
(`src/` — LaTeX-исходник из `https://arxiv.org/e-print/<id>`, `paper.pdf` и `paper.txt` —
PDF и его текст, `abs.html` — страница аннотации). Цитаты взяты из LaTeX-исходника
(это авторский текст); номера уравнений сверены с PDF (`paper.txt`).

---

## [B15] Branciard, Araújo, Feix, Costa, Brukner — arXiv:1508.01704

`abs.html`: `citation_title` = "The simplest causal inequalities and their violation";
авторы Branciard, Cyril; Araújo, Mateus; Feix, Adrien; Costa, Fabio; Brukner, Časlav.
Выгружена версия v1 (e-print от 10.08.2015). Нотация B15: входы `x, y`, выходы `a, b`,
координаты `p(a,b|x,y)` — **противоположна** нотации Mrini–Hardy (там `a, b` — доходы,
`x, y` — исходы).

**B15-1 (число вершин и фасет), Sec. III A, `causal_polytope.tex` стр. 114:**
> We generated the list of its $112$ deterministic vertices (see Appendix~\ref{app:characterization}), and enumerated its $48$ facets using the software \texttt{lrs}~\cite{lrs}.

**B15-2 (тривиальные и два семейства), стр. 116–117:**
> 16 of these facets are trivial, corresponding to the nonnegativity constraints $p(ab|xy) \ge 0$.
> By relabeling the inputs and outputs, the 32 remaining, non-trivial facets can be grouped in two non-equivalent families of causal inequalities: 16 facets are relabelings of the inequality

**B15-3 (GYNI), ур. (4) в PDF (`\label{eq:gyni0}`):**
> \frac{1}{4} \sum_{x,y,a,b} \delta_{a,y} \, \delta_{b,x}\ p(a,b|x,y) \ \le \ \frac12 \,,

**B15-4 (LGYNI), ур. (5) в PDF (`\label{eq:LGYNI0}`):**
> while the last 16 facets are relabelings of the inequality
> \frac{1}{4} \sum_{x,y,a,b} \delta_{x(a \oplus y),0} \, \delta_{y(b \oplus x),0}\ p(a,b|x,y) \ \le \ \frac34 \,,

**B15-5 (три семейства и явный вид переименований), App. A, стр. 379–390:**
> we obtained 48 facets, which can be grouped into 3 families of equivalent facets (up to relabelings of inputs and outputs). Explicitly, these are
> \item 16 trivial facets of the form $p(a,b|x,y) \ge 0$ for all $x,y,a,b = 0,1$;
> \item 16 facets of the GYNI type, [...] $p(a \oplus \alpha_1 x \oplus \alpha_0 = y, b \oplus \beta_1 y \oplus \beta_0 = x) \ \le \ \frac{1}{2}$, for all $\alpha_0, \alpha_1, \beta_0, \beta_1 = 0,1$;
> \item 16 facets of the LGYNI type, [...] $p \big( (x \oplus \alpha_1)(a \oplus \alpha_0 \oplus y)=0, (y \oplus \beta_1)(b \oplus \beta_0 \oplus x) = 0 \big) \, \le \, \frac{3}{4}$, for all $\alpha_0, \alpha_1, \beta_0, \beta_1 = 0,1$.

(`[...]` — опущен вставной оборот "which can be written (in the same form as~\eqref{eq:gyni}, implicitly assuming uniform input bits) as".)

**B15-6 (112 = 64 + 64 − 16), App. A, стр. 377:**
> The 12-dimensional causal polytope thus has $64 + 64 - 16 = 112$ different vertices.

Вывод для Stage A.2: у B15 для сценария «2 входа, 2 выхода, всё бинарное» —
**32 нетривиальные фасеты, 2 нетривиальных класса (3 с классом положительности)**.
Наши «36 сырых» — это 32 нетривиальные + 4 замаскированные неравенства положительности
(см. RESULTS.md, Stage A). **Подтверждено цитатой.**

---

## [MH24] Mrini, Hardy — arXiv:2406.18489

`abs.html`: `citation_title` = "Indefinite Causal Structure and Causal Inequalities with
Time-Symmetry"; авторы Mrini, Luke; Hardy, Lucien. Выгружена версия v1 (e-print от 27.06.2024).
Нотация: `a, b` — доходы (incomes), `x, y` — исходы (outcomes), `α, β` — настройки,
`u, v` — пред- и постселекция.

**MH-1 (двойная причинность), ур. (2):**
> \Tr_{A_O}\sum_x M_{a,x}^{A_IA_O} = \mathbb{1}^{A_I}, \qquad \frac{1}{N_a}\Tr_{A_I}\sum_aM_{a,x}^{A_IA_O} = \frac{1}{N_x}\mathbb{1}^{A_O}.
>
> We call the first condition here \emph{forward causality}, and the second \emph{backward causality}.

**MH-2 (R-боксы: равномерность), текст перед Fig. 3:**
> The boxes labeled with an `$\mathsf{R}$' indicate the transmission of random information such that each possible value for the classical variable is equally probable. In particular, a readout box $x$ sandwiched between two $\mathsf{R}$ boxes (see Fig.~\ref{readsan}) results in a circuit with a constant probability $1/N_x$.

(Рисунок `abprocess.png`, Fig. «The most general process where $B$ is in the causal future of
$A$ ($A \preceq B$)»: каждый провод `a, b, x, y, u, v` заканчивается R-боксом.)

**MH-3 (порядок A ≼ B, вперёд), ур. (3):**
> p^{A\preceq B}(a,b,x,u|\alpha,\beta) = \frac{1}{N_b}p^{A\preceq B}(a,x,u|\alpha), \qquad \forall a,b,x,u,\alpha,\beta.

**MH-4 (порядок A ≼ B, назад), ур. (4):**
> p^{A\preceq B}(b,x,y,v|\alpha,\beta) = \frac{1}{N_x}p^{A\preceq B}(b,y,v|\beta), \qquad \forall b,x,y,v,\alpha,\beta.

**MH-5 (порядок B ≼ A, вперёд), ур. (5):**
> p^{B\preceq A}(a,b,y,u|\alpha,\beta) = \frac{1}{N_a}p^{B\preceq A}(b,y,u|\beta), \qquad \forall a,b,y,u,\alpha,\beta,

**MH-6 (порядок B ≼ A, назад), ур. (6):**
> p^{B\preceq A}(a,x,y,v|\alpha,\beta) = \frac{1}{N_y}p^{B\preceq A}(a,x,v|\alpha), \qquad \forall a,x,y,v,\alpha,\beta,

**MH-7 (причинная разделимость), ур. (7):**
> p(a,b,x,y,u,v|\alpha,\beta) &= q\, p^{A\preceq B}(a,b,x,y,u,v|\alpha,\beta) \nonumber \\ &\qquad + (1-q)\, p^{B\preceq A}(a,b,x,y,u,v|\alpha,\beta)

**MH-8 (GYNI), ур. (8):**
> \frac{1}{N_aN_b}\sum_{a,b,x,y}\delta_{x,b}\,\delta_{y,a}\,p(x,y|\alpha,\beta,a,b,u,v) \leq \frac{1}{2}.

**MH-9 (LGYNI), ур. (9):**
> \frac{1}{N_\alpha N_\beta N_a N_b}\sum_{\alpha,\beta, a,b,x,y}\delta_{\alpha(y\oplus a),0}\,\delta_{\beta(x\oplus b),0}\,p(x,y|\alpha,\beta,a,b,u,v) \leq \frac{3}{4}.
>
> [...] a modified game where a player is only required to guess their neighbor's income if their own setting is equal to one, otherwise they are free to produce any outcome they desire.

**MH-10 (обращённое GYNI), ур. (10):**
> \frac{1}{N_xN_y}\sum_{a,b,x,y}\delta_{x,b}\,\delta_{y,a}\,p(a,b|\alpha,\beta,x,y,u,v) \leq \frac{1}{2},

**MH-11 (обращённое LGYNI), ур. (11):**
> \frac{1}{N_\alpha N_\beta N_x N_y}\sum_{\alpha,\beta, a,b,x,y}\delta_{\beta(y\oplus a),0}\,\delta_{\alpha(x\oplus b),0}\,p(a,b|\alpha,\beta,x,y,u,v) \leq \frac{3}{4}.

**MH-12 (оговорка о настройках), после ур. (11):**
> Note that Eqn.~(\ref{LGYNI}) and Eqn.~(\ref{LGYNIr}) are valid in these forms only up to two settings each, i.e. $1\leq N_\alpha, N_\beta \leq 2$.

**MH-13 (открытый вопрос), Sec. Discussion:**
> It would also be interesting to computationally generate an exhaustive list characterizing the facets of the causal polytope \cite{Giarmatzi2019} determined by Eqns.~(\ref{ABforward}-\ref{convex}). There may exist exotic causal inequalities beyond those presented here, perhaps some that cannot naturally be associated to a particular time direction but rather mix the forward and backward directions.

**MH-14 (ICOTD), аннотация и Sec. 3:**
> Chiribella and Liu study this same class of processes in Appendix D of Ref.~\cite{liu2024tsirelson}, referrring to them as processes with ``Indefinite Causal Order and Time Direction'' (ICOTD). [...] In particular, they show that these classical ICOTD processes can achieve the algebraic maximum of every causal inequality.

---

## Что НЕ является цитатой (наши выводы и переводы — помечены явно)

**D1. Равномерность маргиналов доходов и исходов при маргинализованных u, v.**
В MH24 нет отдельного уравнения `p(a,b) = 1/(N_a N_b)`. Мы выводим его теми же
правилами, которыми MH24 выводят ур. (3): в схеме Fig. `abprocess` при суммировании по
`v, y, x, u` верхний блок, Боб и Алиса по прямой причинности (MH-1, первое условие)
сводятся к R-боксам на проводах `a`, `b` и I-боксам, а «readout box sandwiched between two
R boxes» даёт `1/N` (MH-2). Итог: `p(a,b) = 1/4`. Симметрично (обратная причинность,
суммирование по `u, a, b, v`): `p(x,y) = 1/4`. Это выполняется в обоих порядках.
Без D1 условные формы (8)–(11) нелинейны по `p(a,b,x,y)`; проверка того, что без D1
смесь порядков нарушает (8), вынесена в Stage B как контроль чувствительности.

**D2. LGYNI без настроек.** При `N_α = N_β = 1` формы MH-9/MH-11 вырождены: если
единственное значение настройки 0, левая часть тождественно равна 1 (> 3/4, неравенство
ложно); если 1, получается GYNI с нежёсткой границей 3/4. Поэтому «LGYNI» и «обратное
LGYNI» в сценарии без настроек мы берём в форме B15-4, где роль входов B15 играют доходы
(вперёд) или исходы (назад):
- LGYNI_fwd: `Σ p(a,b,x,y) [a(x⊕b)=0 ∧ b(y⊕a)=0] ≤ 3/4` — B15-4 при замене
  (B15: x→a, y→b, a→x, b→y); совпадает с функционалом в `causal_polytope_calib.py`;
- LGYNI_bwd: образ LGYNI_fwd при обращении времени a↔x, b↔y:
  `Σ p [x(a⊕y)=0 ∧ y(b⊕x)=0] ≤ 3/4`.
Это перевод, а не цитата.

**D3. GYNI и обратное GYNI как линейные функционалы.** При D1 имеем
`p(x,y|a,b) = 4 p(a,b,x,y)` и `p(a,b|x,y) = 4 p(a,b,x,y)`, поэтому левые части (8) и (10)
обе равны `Σ_{x=b, y=a} p(a,b,x,y)`. В сценарии без настроек GYNI и обратное GYNI —
**один и тот же** функционал (условие `x=b, y=a` инвариантно относительно a↔x, b↔y).
Следствие алгебры, не цитата.

---

## Stage B.2: какие из ур. (3)–(6) MH24 выражают прямую, а какие обратную причинность

**MH-15 (вывод ур. (3): маргинализация постселекции и исхода Боба), текст перед ур. (3):**
> Marginalizing over the post-selection variable $v$ and Bob's outcome $y$, the circuit reduces to that of Fig.~\ref{marg} (i). This computation goes through by applying the identity of Fig.~\ref{sumread}, followed by the identity Fig.~\ref{readsan}, and finally by applying double causality Fig.~\ref{dubcausbox} twice.

**MH-16 (смысл ур. (3)), после ур. (3):**
> This equation states that Bob cannot signal to Alice unless there is post-selection---either in the post-selection variable $v$ or in Bob's outcome $y$.

**MH-17 (ур. (4) — обращение (3)), после ур. (4):**
> Now, we repeat the analysis by marginalizing over the pre-selection variable $u$ and Alice's income $a$. [...]
> This constraint is the time-reversal of Eqn.~(\ref{ABforward}), stating that Alice cannot signal to Bob unless there is pre-selection---either in the pre-selection variable $u$ or in Alice's income $a$. This inability to signal forward in time seems unfamiliar, [...]

**MH-18 (ур. (5) и (6)), после каждого из них:**
> stating no-signalling from Alice to Bob without post-selection, and
>
> stating no-signalling from Bob to Alice without pre-selection.

**MH-19 (прямые неравенства опираются только на прямую причинность), перед ур. (8):**
> Following the analysis of Branciard et al. Ref.~\cite{Branciard_2016}, we arrive at a set of causal inequalities that are necessarily satisfied by causally separable correlations. This derivation relies only on forward causality (the first condition in Fig.~\ref{dubcausbox}) and is therefore associated with the time-forward perspective.

**MH-20 (обратные неравенства — только обратная причинность), после ур. (9):**
> With time-symmetry, there is automatically a time-reversed counterpart for each of the causal inequalities. They are derived using only backwards causality (the second condition in Fig.~\ref{dubcausbox}) and are associated to the time-backward perspective.

**MH-21 (приложение, Fig. `nops`):**
> With $v$ and $y$ marginalized, Bob cannot signal backward in time to Alice. In either definite causal order, $A\preceq B$ or $B\preceq A$, applying the double causality rules shows that Alice's output must be ignored.

**B15-7 (вершины временно-прямых многогранников детерминированные), arXiv:1508.01704, Sec. II:**
> in Appendix~\ref{app:characterization} we show that these correspond to deterministic correlations compatible with either causal order (or both, in the case of nonsignaling correlations).

### D4. Приписывание (вывод, не цитата)
Одной фразой вида «ур. (3) следует из прямой причинности» в статье это не сказано. Приписывание
выведено из цитат и рисунков:
- ур. (3) и (5) получаются маргинализацией **будущих** переменных: постселекции `v` и исхода
  (MH-15, MH-18: «without post-selection»). На Fig. `marg`(i) (`abreduction.png`) это делается
  правилом, где I-бокс стоит на выходе и R-бокс на исходе. Это левое условие Fig. `dubcausbox`,
  которое MH-1 называет *forward causality*;
- ур. (4) и (6) получаются маргинализацией **прошлых** переменных: предселекции `u` и дохода
  (MH-17, MH-18: «without pre-selection»). На Fig. `marg`(ii) это правое условие, *backward causality*;
- согласованность: прямые неравенства (8), (9), выводимые по B15 из запрета сигнала в
  прошлое, «relies only on forward causality» (MH-19).

Итог: **F ← {(3), (5)}**, **B ← {(4), (6)}**. Ловушка терминологии: ур. (3) запрещает сигнал
**назад** во времени (MH-16, MH-21), но выводится из **прямой** причинности. «F» здесь
означает условия, следующие из прямой причинности, то есть временно-прямую картину B15/OCB.
