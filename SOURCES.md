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

---

## Stage C: формализм временно-симметричных процесс-матриц (MH24, Sec. 3–4) и OCB (B15, Sec. IV)

**MH-22 (лаборатория: доход, исход, настройка), Sec. 1:**
> In the TSOPT developed in \cite{Hardy:2021fqs}, an additional classical variable called an ``income''---the time-reversed counterpart of an outcome---is available before the operation is performed. An income may be interpreted as the initial state of a measuring apparatus or the initial value of a classical ancilla.
>
> An income is distinguished from a \emph{setting}, which is some classical information that the agent, Alice, has free choice to determine at the time of the operation, independent of any external influences.

**MH-23 (u, v и процесс-матрица), Sec. 3.1:**
> The classical variables $u$ ad $v$, which we call the \emph{pre-selection and post-selection variables}, represent information that is available before and after the experiment. The process matrix can be thought of as a generalization of a density matrix since it determines probabilities in an analogous way
> p(a,b,x,y,u,v) = \Tr_{A_IA_OB_IB_O}[W_{u,v}^{A_IA_OB_IB_O}\cdot(M_{a,x}^{A_IA_O}\otimes M_{b,y}^{B_IB_O}) ].

**MH-24 (положительность и нормировка), ур. (positiveW), (sumtoone), (Wcons1)–(Wcons4):**
> W_{u,v}^{A_IA_OB_IB_O} \geq 0 \qquad \forall u,v.
>
> \sum_{u,v}\Tr_{A_IA_OB_IB_O}[W_{u,v}] &= d_Ad_B, [...] \sum_{u,v}{}_{B_IB_O[1-A_I][1-A_O]}W_{u,v}&=0, [...] \sum_{u,v}{}_{A_IA_O[1-B_I][1-B_O]}W_{u,v}&=0, [...] \sum_{u,v}{}_{[1-A_I][1-A_O][1-B_I][1-B_O]}W_{u,v}&=0.
>
> We adopt the notation of Ref.~\cite{Branciard_2016} to write ${}_{X}W \coloneq \frac{1}{d_X}\mathds{1}^X\otimes\Tr_X[W]$ as the ``trace part'' of an operator $W\in \mathcal{L}(\mathcal{H}^X)$. We also use ${}_{[1-X]}W \coloneq W - {}_{X}W$ to denote the ``traceless part'' of $W$.

**MH-25 (без постселекции / без предселекции), ур. (vcons1)–(ucons3):**
> Process matrices with the post-selection variable marginalized satisfy additional no-signalling constraints:
> \sum_v {}_{A_I[1-B_O]}W_{u,v} &= 0, [...] \sum_v {}_{B_I[1-A_O]}W_{u,v} &= 0, [...] \sum_v {}_{[1-A_O]}{}_{[1-B_O]}W_{u,v}&=0.
>
> Similarly, there are three constraints for a process matrix with the pre-selection variable marginalized:
> \sum_u {}_{A_O[1-B_I]}W_{u,v} &= 0, [...] \sum_u {}_{B_O[1-A_I]}W_{u,v} &= 0, [...] \sum_u {}_{[1-A_I]}{}_{[1-B_I]}W_{u,v}&=0.

**MH-26 (общий вид процесса и свойства слагаемых), ур. (genproc), (sigmaops) и текст:**
> The most general, physical bipartite process matrix can be written as a sum
> W_{u,v}^{A_IA_OB_IB_O} = \frac{1}{d_Ad_B}\bigg(p_0(u,v)\mathbb{1}^{A_IA_OB_IB_O} + \sigma_{u,v}^{TS} + \sigma_{u,v}^{TF} + \sigma_{u,v}^{TB} + \sigma_{u,v}^{ISO} \bigg)
>
> This of course must satisfy $\sum_{u,v}p_0(u,v) = 1$.
>
> \sigma_{u,v}^{ISO} &= \sum_{ij>0}\bigg(s_{ij}\sigma_i^{A_I}\sigma_j^{B_O} + t_{ij}\sigma_i^{A_O}\sigma_j^{B_I}\bigg).
>
> \sum_u \sigma_{u,v}^{TS} = \sum_v\sigma_{u,v}^{TS} = 0, [...] \sum_u\sigma_{u,v}^{TF} = 0. [...] \sum_v\sigma_{u,v}^{TB} = 0.
>
> The final operator $\sigma_{u,v}^{ISO}$ represents terms which may be found in an isolated process, that is, one that does not require pre-selection or post-selection.

**MH-27 (иерархия классов):**
> A sub-class (TF) is formed by the time-forward processes---those that do not involve post-selection. These processes may contain terms from $\sigma_{u,v}^{TF}$ and $\sigma_{u,v}^{ISO}$ and coincide with the known set of bipartite process matrices studied by Oreshkov, Costa, and Brukner \cite{Oreshkov:2011er}. [...] Finally, the smallest sub-class (ISO) is formed by the isolated processes. These lie at the intersection of the time-forward and time-backward processes and contain terms only from $\sigma_{u,v}^{ISO}$.

**MH-28 (TS-операция в базисе), Sec. 3.2:**
> M^{X_IX_O} = \frac{1}{d_X}\bigg( \mathbb{1}^{X_IX_O} + \sum_{ij>0}\mathcal{X}_{ij}\sigma_i^{X_I}\sigma_j^{X_O}\bigg).

**MH-29 (пример MH24: процесс, операции, значения), Sec. 4.1, ур. (exampleW), (aliceop), (bobop):**
> W^{A_IA_OB_IB_O} = \frac{1}{4}\bigg[ \mathds{1}^{A_IA_OB_IB_O} + \frac{1}{\sqrt{2}}\bigg( \sigma_z^{A_O}\sigma_z^{B_I} + \sigma_z^{A_I}\sigma_x^{B_I}\sigma_z^{B_O}\bigg)\bigg],
>
> This process matrix requires pre-selection, but not post-selection.
>
> M^{A_IA_O}_{a,x} = \frac{1}{4}[\mathds{1}+(-1)^x\sigma_z]^{A_I}\otimes [\mathds{1}+(-1)^a\sigma_z]^{A_O}.
>
> M^{B_IB_O}_{b,y}[\beta] &= \frac{1}{2}\beta [\mathds{1}+(-1)^y\sigma_z]^{B_I}\otimes \mathds{1}^{B_O} \nonumber \\ &\qquad + \frac{1}{4}(\beta\oplus 1)[\mathds{1}+(-1)^y\sigma_x]^{B_I}\otimes [\mathds{1}+(-1)^{b+y}\sigma_z]^{B_O}.
>
> p_\text{LGYNI} = \frac{2+\sqrt{2}}{4} > \frac{3}{4} [...] \tilde{p}_\text{LGYNI} = \frac{1}{2} < \frac{3}{4},

**MH-30 (обращение времени процесса):**
> To take the time-reversal of a process matrix, one must swap operators on the following Hilbert spaces: $A_O \leftrightarrow B_I$ and $A_I \leftrightarrow B_O$.

**B15-8 (OCB: инструменты, вероятности, допустимость W), Sec. IV A, ур. (eq:valid_instrument), (eq:probw), (eq:valid_W):**
> M_{a|x}^{A_IA_O} \geq 0 \quad \forall \, a \mathand \tr_{A_O} \sum_a M_{a|x}^{A_IA_O} = \id^{A_I}
>
> p(a,b|x,y) = \tr\big[ (M_{a|x}^{A_IA_O} \otimes M_{b|y}^{B_IB_O}) \cdot W\big]
>
> W \ge 0 \, , [...] \tr W = d_{A_O} \, d_{B_O} \, , [...] {}_{B_IB_O}W = {}_{A_OB_IB_O}W \, , [...] {}_{A_IA_O}W = {}_{A_IA_OB_O}W \, , [...] W = {}_{B_O}W + {}_{A_O}W - {}_{A_OB_O}W \, ,

**B15-9 (явный пример и see-saw-максимумы для кубитов), Sec. IV B и App. C:**
> W = \frac{1}{4} \left[ \id^{\otimes 4} + \frac{Z^{A_I} Z^{A_O} Z^{B_I} \id^{B_O} + Z^{A_I} \id^{A_O} X^{B_I} X^{B_O}}{\sqrt{2}} \right] \, ,
>
> M_{0|0}^{A_IA_O} &= M_{0|0}^{B_IB_O} = 0 \, , [...] M_{1|0}^{A_IA_O} &= M_{1|0}^{B_IB_O} = 2 \, \proj{\Phi^+} \, , [...] M_{0|1}^{A_IA_O} &= M_{0|1}^{B_IB_O} = \proj{0} \otimes \proj{0} \, , [...] M_{1|1}^{A_IA_O} &= M_{1|1}^{B_IB_O} = \proj{1} \otimes \proj{0} \, ,
>
> p_{\text{GYNI}} &\, = \, \frac5{16}\Big(1+\frac1{\sqrt{2}}\Big) \, \approx \, 0.5335 [...] p_{\text{LGYNI}} &\, = \, \frac5{16}\Big(1+\frac1{\sqrt{2}}\Big) + \frac14 \, \approx \, 0.7835
>
> From our numerical results, we thus conjecture that the maximal violations of our causal inequalities achievable with qubit systems are
> p_{\text{GYNI}}^{\text{max}, d=2} & \, \approx \, 0.5694 \, > \, \frac12 \,, \\ p_{\text{LGYNI}}^{\text{max}, d=2} & \, \approx \, 0.8194 \,=\, p_{\text{GYNI}}^{\text{max}, d=2} + \frac14 \, > \, \frac34 \,.
>
> our maximal probability $p_{\text{GYNI}}^{\text{max}, d=2}$ of winning the GYNI game with qubits is then found to be the smallest real root of the polynomial
> 1\,769\,472 \,x^4 - 2\,884\,032 \,x^3 + 1\,630\,800 \,x^2 - 380\,052 \,x + 34\,087,

(B15-9: see-saw — нижние оценки, авторы называют их гипотезой: «we thus conjecture».)

### D5. Совместная вероятность в сценарии без настроек (вывод, не цитата)
По MH-23 `p = Tr[W (M⊗M)]`, а по MH-1 для каждого дохода `Tr_{A_O} Σ_x M_{a,x} = 1^{A_I}`.
Тогда при `Tr W = d_A d_B` сумма `Σ_{a,b,x,y} Tr[W(M⊗M)] = N_a N_b`, а не 1. Нормировку восстанавливает
множитель R-боксов на проводах доходов (MH-2): `p(a,b,x,y) = (1/(N_a N_b)) Tr[W (M_{a,x}⊗M_{b,y})]`.
Проверка: с этим множителем пример MH-29 должен дать `(2+√2)/4`. Это калибровка C.1.

### D6. Лемма об изолированных процессах (вывод, не цитата; доказательство — в PREREGISTRATION_C.md)
При маргинализованных `u, v` статистика задаётся матрицей `Σ_{u,v} W_{u,v}`. По MH-26 в ней
обнуляются σ^TS, σ^TF и σ^TB и остаётся `(1/(d_A d_B))(1 + σ^ISO)`. σ^ISO содержит только
двухчастичные члены типов `A_I B_O` и `A_O B_I`, и такая матрица — выпуклая смесь одностороннего
канала A→B и одностороннего канала B→A.
