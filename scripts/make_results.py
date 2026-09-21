"""
Порождает RESULTS.md из results/json/*.json. Руками RESULTS.md не редактируется.
Проверяет SHA-256 PREREGISTRATION.md против results/json/prereg.json и против
версии файла в коммите предрегистрации.
"""
import hashlib
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = os.path.join(ROOT, "results", "json")


def load(name):
    p = os.path.join(J, name)
    return json.load(open(p)) if os.path.exists(p) else None


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def ok(b):
    return "ДА" if b else "НЕТ"


def prereg_block():
    prs = load("prereg.json")
    lines = ["## Предрегистрации", ""]
    if not prs:
        return lines + ["**prereg.json отсутствует — предрегистрация не зафиксирована.**", ""]
    lines += ["| стадия | файл | SHA-256 | коммит | файл совпадает | версия в коммите совпадает |",
              "|---|---|---|---|---|---|"]
    for pr in prs:
        cur = sha(os.path.join(ROOT, pr["file"]))
        try:
            blob = subprocess.run(["git", "-C", ROOT, "show", f"{pr['commit']}:{pr['file']}"],
                                  capture_output=True, check=True).stdout
            in_commit = hashlib.sha256(blob).hexdigest()
        except Exception as e:  # noqa: BLE001
            in_commit = f"ошибка: {e}"
        lines.append(f"| {pr['stage']} | `{pr['file']}` | `{pr['sha256']}` | `{pr['commit']}` | "
                     f"**{ok(cur == pr['sha256'])}** | **{ok(in_commit == pr['sha256'])}** |")
    lines += ["", "Каждая предрегистрация — отдельный коммит до первого прогона своей стадии.", ""]
    return lines


def architect_defects():
    return ["## Дефекты калибровки архитектора (зафиксированы по его указанию, PROMPT stage B.2)", "",
            "1. `causal_polytope_calib.py` заявлял точную рациональную арифметику, но использует "
            "`import cdd`, а в pycddlib 3.x это float-бэкенд: Fraction молча превращается во float. "
            "Точный режим — `cdd.gmp`; все перечисления проекта идут через `cdd.gmp` или `lrs`. "
            "Антивакуумный тест точности — в разделе Stage B.2. Сам скрипт архитектора не менялся.",
            "2. Критерий кандидата в `SPEC_TSCAUSAL_stage0.md` («класс, не переходящий в себя при "
            "обращении времени») отменён поправкой архитектора (отдельный коммит `c45a096`, старый "
            "текст зачёркнут, не удалён). Действующий критерий — приписываемость (Stage B.2). "
            "Исход Stage B «новый, но ненаправленный» сформулирован по отменённому критерию.", ""]


def stage_a(a):
    a1, a2, a3, a4 = a["A1"], a["A2"], a["A3"], a["A4"]
    f36 = a1["float_raw36_decomposition"]
    L = ["## Stage A — ворота", "",
         f"Итог ворот (A.1 и A.3 пройдены, A.2 подтверждён цитатой): **{ok(a['gate_pass'] and a2['pass'])}**", "",
         "### A.1 Калибровочный скрипт", "",
         "| величина | скрипт (как есть) | точно (cdd.gmp) | ожидание |", "|---|---|---|---|",
         f"| вершин | {a1['vertices']} | {a1['exact']['vertices']} | 112 |",
         f"| равенств (нормировка) | {a1['equalities']} | {a1['exact']['equalities']} | 4 |",
         f"| GYNI, причинный максимум | {a1['gyni']} | {a1['exact']['gyni_max']} | 1/2 |",
         f"| LGYNI, причинный максимум | {a1['lgyni']} | {a1['exact']['lgyni_max']} | 3/4 |",
         f"| «нетривиальных» по фильтру скрипта | {a1['raw_nontrivial']} | {a1['exact']['raw_nontrivial_script_filter']} | — |",
         "",
         f"Замечание о бэкенде: {a1['note_backend']} Число «сырых нетривиальных» зависит от того, "
         f"в какой записи cdd выдаёт неравенства положительности: во float-прогоне {f36['literal_positivity_rows_dropped_by_script']} "
         f"из 16 записаны буквально (и отфильтрованы), в GMP-прогоне — ни одной. Это артефакт представления.",
         "",
         "### A.2 Сверка с Branciard et al. (arXiv:1508.01704, цитаты B15-1…B15-6 в SOURCES.md)", "",
         "| величина | B15 | наше |", "|---|---|---|",
         f"| фасет всего | 48 | {a2['ours']['facets_total']} |",
         f"| тривиальных (p ≥ 0) | 16 | {a2['ours']['trivial_after_projection']} (после проекции) |",
         f"| нетривиальных | 32 | {a2['ours']['nontrivial_after_projection']} |",
         f"| семейств по переименованиям | 3 (2 нетривиальных) | {a4['classes']} (размеры {a4['class_sizes']}) |",
         "",
         f"Наши «36 сырых» из float-прогона: {f36['nontrivial']} нетривиальных + {f36['positivity_in_disguise']} "
         f"неравенства положительности, записанных через равенства нормировки (все 36 среди точных фасет: "
         f"{ok(f36['all_rows_among_exact_facets'])}). Счёт сходится с B15: **подтверждено цитатой**.",
         f"Каждая строка — фасета (ранг насыщающих вершин = dim−1): {ok(a2['ours']['every_row_is_facet'])}; "
         f"размерность многогранника {a2['ours']['polytope_dim']}.",
         "",
         "### A.3 lrs против pycddlib (cdd.gmp)", "",
         f"- фасет: cdd {a3['cdd_count']}, lrs {a3['lrs_count']}; равенств: cdd {a3['cdd_equalities']}, lrs {a3['lrs_equalities']}",
         f"- множества совпадают после проекции на аффинную оболочку: **{ok(a3['sets_equal_after_projection'])}** "
         f"(сырые записи тоже совпали: {ok(a3['raw_sets_equal_before_projection'])})",
         f"- отрицательный контроль (испорченная фасета обнаруживается сравнением): {ok(a3['negative_control_spoiled_set_detected'])}",
         "",
         "### A.4 Калибровка канонизатора (известный ответ: 3 класса по 16)", "",
         f"- группа переименований B15 порядка {a4['group_order']}, все генераторы — автоморфизмы: "
         f"{ok(all(a4['generators_are_automorphisms'].values()))}",
         f"- классов: **{a4['classes']}**, размеры {a4['class_sizes']}; класс GYNI {a4['gyni_class_size']}, "
         f"LGYNI {a4['lgyni_class_size']}, положительности {a4['positivity_class_size']}",
         f"- контроль «без проекции»: {a4['control_no_projection_classes']} классов (артефакт, ср. «7 классов» в спеке)",
         f"- контроль «тривиальная группа»: {a4['control_trivial_group_classes']} классов",
         f"- контроль «без условных переворотов выхода»: {a4['control_group_without_conditional_flips_classes']} классов",
         ""]
    return L


def fmt_support(sup):
    return " + ".join(f"p({s})" for s in sup)


def stage_b(b, prereg):
    v, cr, g, fa, gr, cl = (b["vertices"], b["vertex_crosscheck"], b["gates"], b["facets"],
                            b["group"], b["classes"])
    L = ["## Stage B — временно-симметричный многогранник (Def-II, без настроек)", "",
         f"**Исход: {b['outcome']}** _(по критерию, отменённому поправкой архитектора; действующая "
         "классификация — Stage B.2)_", "",
         "Определения — PREREGISTRATION.md §1 (ур. (3)–(7) MH24 + D1: `p(a,b) = p(x,y) = 1/4`), "
         "координаты `p(a,b,x,y)`, порядок строк `abxy`.", "",
         "### B.2 Вершины и ворота", "",
         f"- вершин: `P_AB` {v['P_AB']}, `P_BA` {v['P_BA']}, общих {v['common']}, `P_TS` {v['P_TS_union']}; "
         f"знаменатели {v['denominators']}; аффинная размерность {b['affine_dim']} "
         f"(оболочка = нормировка + D1: {ok(b['hull_equals_norm_plus_D1'])})",
         f"- ворота: GYNI {g['values']['GYNI']}, обратное GYNI {g['values']['GYNI_reversed']}, "
         f"LGYNI {g['values']['LGYNI_fwd']}, обратное LGYNI {g['values']['LGYNI_bwd']} — **{('пройдены' if g['pass'] else 'ПРОВАЛ')}**",
         f"- GYNI и обратное GYNI — один и тот же функционал (D3): {ok(g['GYNI_equals_GYNI_reversed_as_functional'])}",
         f"- буквальная форма ур. (9) при `N_α = 1`: настройка 1 → максимум {g['MH9_literal_alpha1_max']} "
         f"(GYNI, граница 3/4 нежёсткая); настройка 0 → {g['MH9_literal_alpha0_max']} (> 3/4, неравенство ложно). Отсюда D2.",
         "",
         "**Перекрёстная проверка «детерминированных вершин».** Детерминированные классические TS-схемы "
         "(биекции (доход, вход) ↔ (исход, выход), провода размерности 2):",
         ""]
    for k in ("anc1", "anc2", "anc4"):
        c = cr[k]
        L.append(f"- анцилла {k[3:]}: {c['distinct_distributions']} распределений, все внутри `P_AB`: "
                 f"{ok(c['all_inside_P_AB'])}, вершин `P_AB` достигнуто: {c['vertices_of_P_AB_realized']} из {v['P_AB']}")
    L += ["",
          f"{v['P_AB'] - cr['anc4']['vertices_of_P_AB_realized']} вершин `P_AB` не достигаются. Пример: `y = a ⊕ x·¬b` при "
          "равномерном `x`. Для неё Бобу нужны и `a`, и `x`, а биекция Алисы не может передать оба: если выход `o` "
          "определяет `(a, x)`, то `(x, o)` принимает не больше `d` значений вместо `2d`. То есть ур. (3)–(4) вместе с D1 — "
          "необходимые, но не достаточные условия для классически реализуемых корреляций A≼B. По предрегистрации "
          "это не стоп: основной объект — многогранник, заданный ур. (3)–(7) (MH-13). Классическое замыкание "
          "разобрано ниже, в разведке.", "",
          "### Антивакуумные тесты группы", "",
          f"G порядка {gr['order_G']} (обмен сторон, обращение времени, 4 переворота); G без TR — порядка {gr['order_G_without_TR']}.", "",
          "| генератор | нетождественен | автоморфизм | сдвигает известные | образ валиден |", "|---|---|---|---|---|"]
    for k, t in gr["generator_action_on_known"].items():
        L.append(f"| {k} | {ok(gr['generators_nontrivial'][k])} | {ok(gr['generators_automorphisms'][k])} | "
                 f"{', '.join(t['moves']) or '—'} | {ok(t['image_valid_same_bound'])} |")
    L += ["",
          "Отрицательные контроли (должны быть отвергнуты): "
          + ", ".join(f"{k}: {'отвергнут' if v_ else 'ПРИНЯТ'}" for k, v_ in gr["negative_controls_rejected"].items()) + ".",
          f"Полная группа локальных автоморфизмов (биекции пар (a,x), (b,y) и обмен, 1152 кандидата) имеет порядок "
          f"{gr['full_local_automorphism_group_order']}; G ⊆ ней: {ok(gr['G_subset_of_local'])}. Классы по полной группе: "
          f"{cl['count_full_local_group']}. Тест направленности откалиброван: LGYNI_fwd направлен — "
          f"{ok(cl['directional_test_control']['LGYNI_fwd_directional'])}, GYNI направлен — "
          f"{ok(cl['directional_test_control']['GYNI_directional'])}.", "",
          "### B.3 Фасеты", "",
          f"- cdd.gmp {fa['cdd']}, lrs {fa['lrs']}; совпадают после проекции: **{ok(fa['cdd_equals_lrs_after_projection'])}**",
          f"- все валидны: {ok(fa['all_valid'])}; все — фасеты (ранг насыщающих вершин = dim−1): {ok(fa['all_are_facets'])}",
          f"- время: cdd {fa['seconds_cdd']} с, lrs {fa['seconds_lrs']} с; процесс целиком {b['resources']['seconds_total']} с, "
          f"пик RSS {b['resources']['max_rss_MB']} МБ",
          "",
          "### B.4–B.5 Классы и сопоставление с известными", "",
          f"Классов по G: **{cl['count_G']}**; из них вне K: **{cl['new_classes']}**, направленных вне K: "
          f"**{cl['new_directional_classes']}**. Фасет в K: {cl['facets_in_K']}, вне K: {cl['facets_not_in_K']}.", "",
          "Читаемая форма: `Σ_{t ∈ S} p(t) ≤ 1/2`, где `t = abxy`; при `p(a,b) = 1/4` это «игра» с успехом не выше 1/2. "
          "Каждая форма отдельно проверена: максимум на вершинах 1/2, грань размерности 8.", "",
          "| # | размер | в K | направленный | инвариантен к | S (веса 1), правая часть 1/2 |", "|---|---|---|---|---|---|"]
    for i, c in enumerate(cl["list"], 1):
        df = c["display_form"]
        what = "p(0000) ≥ 0 (положительность)" if c["positivity"] else fmt_support(df["support_abxy_weight1"])
        L.append(f"| {i} | {c['size']} | {('да: ' + '+'.join(c['K_readings'])) if c['in_K'] else 'нет'} | "
                 f"{ok(c['directional'])} | {', '.join(df['invariant_under']) or '—'} | {what} |")
    kf = cl["known_face_dim(facet = dim-1)"]
    L += ["",
          f"**Известные неравенства — не фасеты `P_TS`.** Их максимумы достигаются (ворота), но размерность "
          f"граней GYNI {kf['GYNI']}, LGYNI_fwd {kf['LGYNI_fwd']}, LGYNI_bwd {kf['LGYNI_bwd']} при размерности "
          f"фасеты {b['affine_dim'] - 1}. Из {cl['K_size_distinct']} различных элементов K все валидны на `P_TS` "
          f"({ok(cl['K_all_valid_on_P_TS'])}), фасетами являются {cl['K_elements_that_are_facets_of_P_TS']} (только положительность).",
          "",
          f"**Отделяющая точка** z: `{cl['separating_point_z']}`. Удовлетворяет всем элементам K: "
          f"{ok(cl['z_satisfies_all_K'])}; лежит в `P_TS`: {ok(cl['z_in_P_TS'])}. Отсюда `P_TS` строго меньше "
          "пересечения прямого и обратного многогранников B15, и существование фасет вне K следует без перебора.",
          ""]
    # прогнозы
    L += ["### Прогнозы и результат", "",
          "| величина | прогноз исполнителя | диапазон | получено | в диапазоне |", "|---|---|---|---|---|"]
    rows = [("вершин P_AB", 12, (12, 60), v["P_AB"]), ("вершин P_TS", 20, (20, 120), v["P_TS_union"]),
            ("аффинная размерность", 9, (7, 9), b["affine_dim"]), ("фасет P_TS", 40, (10, 500), fa["distinct"]),
            ("классов по G", 5, (3, 20), cl["count_G"])]
    for n, pt, (lo, hi), got in rows:
        L.append(f"| {n} | {pt} | {lo}–{hi} | {got} | {ok(lo <= got <= hi)} |")
    L += [f"| исход | класс вне K есть (P≈0.9); направленный (P≈0.5) | — | вне K: {cl['new_classes']}, "
          f"направленных: {cl['new_directional_classes']} | — |", "",
          "Прогноз архитектора («новых классов не будет, всё уложится в четыре известных неравенства») "
          f"**не подтвердился**: {cl['new_classes']} класса вне K, а GYNI и LGYNI вообще не являются фасетами. "
          "Критерий промпта для кандидата в Stage C (класс вне K **и** не переходящий в себя при обращении времени) "
          "**не выполнен**: все новые классы ненаправленные. Решение о Stage C — за архитектором.", ""]
    d1 = b["def_I"]
    L += ["### Контроль чувствительности: Def-I (ур. (3)–(6) без D1)", "",
          f"- вершин `P_AB` {d1['P_AB']}, `P_TS` {d1['P_TS_union']}, аффинная размерность {d1['affine_dim']}, "
          f"фасет {d1['facets']}, классов {d1['classes_G_restricted_to_automorphisms']}",
          f"- условная форма ур. (8) на смесях порядков: найдено значение {d1['max_conditional_GYNI_eq8_found_on_mixtures']} "
          f"> 1/2: {ok(d1['eq8_violated_by_causally_separable_mixture'])}. Без D1 собственное неравенство (8) MH24 "
          "нарушается причинно-разделимой смесью, поэтому Def-I не согласуется с MH24. Это подтверждает выбор D1 "
          "(предсказано в предрегистрации, п. 6(iii)).", ""]
    return L


def explore(e):
    c = e["classical_closure"]
    L = ["## Разведка (НЕ предрегистрирована): классически реализуемое замыкание", "",
         "Распределение любой детерминированной классической TS-схемы A≼B имеет вид "
         "`Σ μ(tA,tB) · ¼ · [a = tA(x)] · [y = tB(b)]`. Здесь `tA` задаёт доход Алисы как функцию её исхода, "
         "`tB` задаёт исход Боба как функцию его дохода, а веса μ удовлетворяют `E|tA| = E|tB| = 1`. "
         "Замыкание по всем размерностям — образ многогранника таких μ. Редукция откалибрована: на размерностях 2 "
         "она совпала с прямым перебором биекций "
         f"({', '.join(k + ': ' + ok(v['equal']) for k, v in e['reduction_calibration'].items())}).", "",
         "| размеры (dA, анцилла, dB) | распределений | накоплено крайних точек A≼B |", "|---|---|---|"]
    for k, v in e["circuits"].items():
        L.append(f"| {k} | {v['distinct']} | {v['cumulative_extreme_points_AB']} |")
    L += ["",
          f"- замыкание A≼B: {c['AB_extreme_points']} вершин. Усечённый перебор достигает из них {c['AB_extreme_points_realized_by_truncated_search']}, "
          f"все его точки лежат в замыкании: {ok(c['truncated_points_inside_closure'])}. Замыкание лежит в `P_AB` (Def-II): "
          f"{ok(c['AB_closure_inside_Def_II_P_AB'])}; вершин Def-II в замыкании {c['Def_II_P_AB_vertices_in_closure']} из 18",
          f"- `P_TS^cl`: {c['TS_vertices']} вершин, размерность {c['affine_dim']}, {c['facets']} фасет "
          f"(cdd = lrs: {ok(c['cdd_equals_lrs'])}; все валидны: {ok(c['all_valid'])}; все фасеты: {ok(c['all_are_facets'])}); "
          f"TR — автоморфизм: {ok(c['generators_automorphisms']['TR'])}",
          f"- классов по G: **{c['classes_G']}**, вне K: **{c['new_classes']}**, направленных: **{c['new_directional']}**; "
          f"грани GYNI/LGYNI_fwd/LGYNI_bwd имеют размерности {c['known_face_dim(facet = dim-1)']['GYNI']}/"
          f"{c['known_face_dim(facet = dim-1)']['LGYNI_fwd']}/{c['known_face_dim(facet = dim-1)']['LGYNI_bwd']} "
          "(фасетами не являются)",
          "",
          "Качественный вывод тот же, что для Def-II: новые классы есть, направленных нет. Квантовые TS-схемы "
          "могут занимать что-то между `P_TS^cl` и Def-II; это не исследовалось.", ""]
    return L


def stage_b2(d, pt):
    i1, i2, i3, i4 = d["item1"], d["item2"], d["item3"], d["item4"]
    c = i1["calibration"]
    L = ["## Stage B.2 — приписываемость, происхождение вершин, чувствительность, замыкание", "",
         f"**Исход: {d['outcome']['text']}**", "",
         "| класс | смешанный (U2) | пережил U1 | класс фасет классического замыкания |", "|---|---|---|---|"]
    for r in d["outcome"]["table"]:
        L.append(f"| {r['class']} | {ok(r['mixed'])} | {ok(r['survives_U1'])} | {ok(r['in_closure'])} |")
    L += ["", "По промпту дальше идут литчек и письмо авторам MH24, до любых заявлений о новизне. "
          "Stage C запускает архитектор.", ""]
    if pt:
        L += ["### Точность", "",
              f"Треугольник с вершиной (1/3, 1), путь V→H→V: cdd.gmp — {ok(pt['cdd_gmp']['pass'])}, "
              f"lrs — {ok(pt['lrs']['pass'])} (ровно `1/3`). Контроль через float `cdd`: вернул "
              f"`{pt['float_cdd_control']['vertices'][2][0]}`, тест провален, как и требуется "
              f"({ok(not pt['float_cdd_control']['pass'])}). Ворота точности: **{ok(pt['gate_pass'])}**.", ""]
    L += ["### П. 1 Приписываемость (U2)", "",
          "Приписывание (SOURCES.md, D4): F ← ур. (3), (5) (прямая причинность), B ← ур. (4), (6) "
          "(обратная). Ловушка терминологии: ур. (3) запрещает сигнал **назад** во времени, но выводится "
          "из **прямой** причинности.", "",
          f"- F: {i1['F_vertices']} вершин, {i1['F_facets']} фасет; B: {i1['B_vertices']} вершин, {i1['B_facets']} фасет; "
          f"размерности {i1['F_B_affine_dim']}. Обмен и перевороты сохраняют F и B: "
          f"{ok(all(v['F'] and v['B'] for k, v in i1['symmetries_preserve_F_B'].items() if k != 'TR'))}; "
          f"TR переводит F в B: {ok(i1['TR_maps_F_to_B'])}",
          f"- F∩B: {i1['F_cap_B_vertices']} вершин (cdd = lrs: {ok(i1['F_cap_B_vertices_lrs_equal'])}), "
          f"TS ⊆ F∩B: {ok(i1['TS_inside_F_cap_B'])}, TS = F∩B: {ok(i1['TS_equals_F_cap_B'])}; "
          f"вершин F∩B вне TS: {i1['F_cap_B_vertices_outside_TS']}",
          f"- точка z (`x = a, y = a⊕b`): в F — {ok(i1['z']['in_F'])} (через F_AB: {ok(i1['z']['in_F_AB'])}), "
          f"в B — {ok(i1['z']['in_B'])} (через B_BA: {ok(i1['z']['in_B_BA'])}), вершина F∩B — "
          f"{ok(i1['z']['vertex_of_F_cap_B'])}, в TS — {ok(i1['z']['in_TS'])}. Её отсекают "
          f"{i1['witness_z_first'][0]['cut_by_n_TS_facets']} фасет TS; одна из них: "
          f"веса {{t: w}} = {{{', '.join(t + ':' + str(w) for t, w in i1['witness_z_first'][0]['one_cutting_facet_nicest']['weights'].items() if w)}}}, "
          f"правая часть {i1['witness_z_first'][0]['one_cutting_facet_nicest']['rhs']}.",
          "- смысл: z причинна вперёд в порядке A≼B и причинна назад в порядке B≼A. TS требует, чтобы "
          "один и тот же порядок был причинен в обе стороны, поэтому z отсекается.", "",
          "**Калибровка теста** (может провалиться):", "",
          f"- все 48 фасет K_fwd выполняются на F: {ok(c['K_fwd_all_hold_on_F'])}; их типы: {c['K_fwd_kinds']}",
          f"- «направленные вперёд» среди K_fwd есть: {ok(c['K_fwd_forward_directional_exists'])}; их образы "
          f"при TR — «направленные назад»: {ok(c['TR_images_backward'])}",
          f"- LGYNI_fwd: {c['LGYNI_fwd']['kind']} (max на F {c['LGYNI_fwd']['max_F']}, на B "
          f"{c['LGYNI_fwd']['max_B']} в целочисленной записи, где граница 3)",
          f"- положительность: {c['positivity']}",
          f"- контроль из промпта (GYNI): **{c['GYNI_prompt_control']['kind']}**, как и предсказано: при U2 "
          "GYNI ≡ обратное GYNI (D3), поэтому на B оно нарушаться не может. Контроль промпта не способен "
          "показать направленность и заменён калибровкой через K_fwd (отклонение из предрегистрации).",
          f"- ворота калибровки: **{ok(c['pass'])}**", "",
          "| # | размер | тип класса | типы членов | max на F | max на B | граница |", "|---|---|---|---|---|---|---|"]
    for k, cl in enumerate(i1["classes"], 1):
        L.append(f"| {k} | {cl['size']} | {cl['class_kind']}{' (положительность)' if cl['positivity'] else ''} | "
                 f"{cl['member_kinds']} | {'–'.join(dict.fromkeys(cl['max_F_range']))} | "
                 f"{'–'.join(dict.fromkeys(cl['max_B_range']))} | {cl['rhs']} |")
    L += ["", "(максимумы в примитивной целочисленной записи проекции; нумерация классов как в Stage B: "
          "1 = N1 [32], 3 = N2 [16].)", "",
          "### П. 2 Происхождение вершин", "",
          f"- Stage B: {i2['stage_B_method']}.",
          f"- Независимый пересчёт через lrs (H→V): A≼B {i2['lrs_AB']}, B≼A {i2['lrs_BA']}; совпадает с cdd.gmp: "
          f"{ok(i2['cdd_equals_lrs'])}; объединение = вершины Stage B: {ok(i2['union_equals_stage_B_vertices'])}. "
          "Основной многогранник Stage B подтверждён.",
          f"- Дробные вершины в Stage B были с самого начала (знаменатели 1, 4, 8 указаны в RESULTS Stage B). "
          f"По максимальному знаменателю: {i2['AB_vertex_max_denominator_histogram']}, носители размера "
          f"{i2['AB_vertex_support_sizes']}; максимальная координата {i2['max_coordinate_any_vertex']}. "
          "При U2 любая точка имеет p(a,b) = 1/4, так что координат больше 1/4 и вершин 0/1 быть не может. "
          "4 вершины равномерны на 4 точках (`x=a⊕c1, y=b⊕c2`), 14 — равномерны на 8 точках.", "",
          "### П. 3 Чувствительность к равномерности", "",
          "| вариант | вершин A≼B | вершин TS | размерность | фасет | группа | классов | смешанных классов | z ∈ TS |",
          "|---|---|---|---|---|---|---|---|---|"]
    L.append(f"| U2 | 18 | 32 | 9 | {i1['TS_facets']} | 64 | {len(i1['classes'])} | "
             f"{sum(1 for x in i1['classes'] if x['class_kind'] == 'смешанное')} | НЕТ |")
    for u in ("U1", "U0"):
        x = i3[u]
        L.append(f"| {u} | {x['V_AB']} | {x['V_TS']} | {x['affine_dim']} | {x['facets']} | {x['group_order']} | "
                 f"{x['classes']} | {x['mixed_classes']} | {ok(x['z_in_TS'])} |")
    L += ["", "Выживание новых классов U2:", ""]
    for u in ("U1", "U0"):
        for name, v in i3[u]["survival_of_U2_new_classes"].items():
            L.append(f"- {u}: {name} — пережил: **{ok(v['survives'])}** ({v['n_facets']} фасет), "
                     f"приписываемость в {u}: {v.get('attribution_in_' + u)}")
    L += ["", "Ни один новый класс не помечается как «следствие допущения U2».",
          f"- U1: TR — автоморфизм: {ok(i3['U1']['generators_automorphisms']['TR'])} (группа порядка "
          f"{i3['U1']['group_order']}). Линейная форма (8) при U1: max {i3['U1']['eq8_linear_max']}. "
          f"Условная форма (10) на 4000 случайных смесях: max {i3['U1']['eq10_conditional_max_found']}, "
          f"нарушение не найдено (это не доказательство справедливости). Прогноз «нарушается» не подтвердился.",
          f"- U0: условная форма (8) воспроизводит {i3['U0']['eq8_conditional_max_found']} > 1/2.", "",
          "### П. 4 Замыкание классических схем", "",
          f"- Все {i4['closure_TS_vertices']} вершин замыкания лежат в TS (Def-II): **{ok(i4['all_closure_vertices_inside_TS'])}** "
          f"(вне: {i4['n_outside']}). Вершинами TS из них являются {i4['closure_vertices_that_are_TS_vertices']}; "
          f"остальные — дробные точки внутри TS (знаменатели {i4['closure_vertex_denominators']}).",
          f"- Проверка построения: для каждой из {i4['explicit_circuits']['n']} вершин многогранника μ собрана явная "
          f"схема с биекциями размерности N ∈ {i4['explicit_circuits']['N_values']}. Прямой прогон совпал с образом μ: "
          f"{ok(i4['explicit_circuits']['all_equal_image'])}; ур. (3), (4) и U2 выполняются: "
          f"{ok(i4['explicit_circuits']['all_satisfy_eq3_eq4_U2'])}. Значит, замыкание построено верно, "
          "а (3)–(6) на классических схемах действительно необходимы.",
          f"- Откуда рост числа вершин (48 против 32): замыкание — строго меньший многогранник внутри TS. "
          f"Оно отрезает 16 классически нереализуемых вершин TS (по 8 на порядок) и получает на их месте "
          f"новые дробные вершины. Фасет {i4['closure_facets']} (cdd = lrs: {ok(i4['cdd_equals_lrs'])}), "
          f"аффинная оболочка та же, что у TS: {ok(i4['same_affine_hull_as_TS'])}.",
          f"- Приписываемость классов замыкания (те же F, B; по B15-7 временно-прямые корреляции "
          f"детерминированны, так что H-вариант F_AB совпадает с классически реализуемым временно-прямым множеством, на которое наложено U2): смешанных "
          f"{i4['mixed_classes']} из {len(i4['classes']) - 1} непозитивных; типы: "
          + ", ".join(f"{x['size']}:{'/'.join(x['kinds'])}" for x in i4["classes"]) + ".",
          f"- Классы N1 и N2 являются также классами фасет замыкания: {i4['TS_new_classes_also_closure_classes']}.", ""]
    cls = i1["classes"]
    mixed_new = [c["class_kind"] == "смешанное" for c in cls if not c["positivity"]]
    surv = [v["survives"] for v in i3["U1"]["survival_of_U2_new_classes"].values()]
    rows = [
        ("точность: exact = 1/3, float-контроль проваливается", "0.99", ok(pt and pt["gate_pass"])),
        ("z ∈ F, z ∈ B, TS ⊊ F∩B", "0.95", ok(i1["z"]["in_F"] and i1["z"]["in_B"] and not i1["TS_equals_F_cap_B"])),
        ("оба новых класса смешанные", "0.9", ok(all(mixed_new))),
        ("положительность и GYNI — общие", "0.95", ok(i1["calibration"]["positivity"] == "общее"
                                                     and i1["calibration"]["GYNI_prompt_control"]["kind"] == "общее")),
        ("есть K_fwd, нарушаемый на B", "0.8", ok(i1["calibration"]["K_fwd_forward_directional_exists"])),
        ("z — вершина F∩B", "0.7", ok(i1["z"]["vertex_of_F_cap_B"])),
        ("вершин F∩B: 40 (33–300)", "—", f"{i1['F_cap_B_vertices']} ({ok(33 <= i1['F_cap_B_vertices'] <= 300)})"),
        ("п.2: lrs = Stage B; 14 вершин с 1/8, 4 с 1/4", "0.97", ok(i2["pass"] and i2["AB_vertex_max_denominator_histogram"] == {"4": 4, "8": 14})),
        ("U1: TR не автоморфизм, группа 32", "0.85", ok(not i3["U1"]["generators_automorphisms"]["TR"] and i3["U1"]["group_order"] == 32)),
        ("хотя бы один новый класс переживает U1", "0.6", ok(any(surv))),
        ("условная (10) нарушается в U1", "0.6", ok(i3["U1"]["eq10_violated"])),
        ("U0 воспроизводит 227/390", "0.97", ok(i3["U0"]["eq8_conditional_max_found"] == "227/390")),
        ("все 48 вершин замыкания внутри TS", "0.95", ok(i4["all_closure_vertices_inside_TS"])),
        ("новые вершины замыкания дробные, знаменатели кратны 3", "0.8", ok(12 in i4["closure_vertex_denominators"])),
        ("≥1 класс замыкания смешанный / все 6", "0.95 / 0.5", f"{ok(i4['mixed_classes'] >= 1)} / {ok(i4['mixed_classes'] == 6)}"),
        ("N1 или N2 — класс замыкания", "0.5", ok(any(i4["TS_new_classes_also_closure_classes"].values()))),
        ("исход «кандидат»", "0.35", ok(d["outcome"]["text"].startswith("КАНДИДАТ"))),
    ]
    L += ["### Прогнозы B.2 и результат", "", "| прогноз исполнителя | уверенность | сбылся |", "|---|---|---|"]
    L += [f"| {a} | {b_} | {c_} |" for a, b_, c_ in rows]
    L += ["", "Прогнозы архитектора: TS ⊊ F∩B — "
          f"**{ok(not i1['TS_equals_F_cap_B'] and i1['z']['in_F'] and i1['z']['in_B'])}**; хотя бы один новый "
          f"класс смешанный — **{ok(any(mixed_new))}**; хотя бы один переживает U2 → U1 — **{ok(any(surv))}**.", "",
          "### Отклонения от промпта", "",
          "- Калибровка через GYNI заменена калибровкой через K_fwd: при U2 GYNI совпадает с обратным GYNI, "
          "поэтому нарушиться на B не может (предрегистрировано).",
          "- «Подтверждён в обоих построениях» понимается так: канонический вид класса совпадает с классом "
          "фасет классического замыкания (определение из предрегистрации). Для замыкания U1 ≡ U2: "
          "у классических схем p(x,y) = 1/4 выполняется автоматически, поэтому «пережил U1» проверяется "
          "только для H-построения.",
          "- Найден и исправлен дефект парсера lrs. При переполнении lrs перезапускается в 128-битной "
          "арифметике и печатает вывод заново. Парсер теперь берёт последний полный блок, а на "
          "нечисловую строку падает, а не пропускает её. В Stage A и B перезапусков не было: счёты "
          "lrs совпадали с cdd. Всё пересчитано заново через `run_all.sh`.",
          "- Условная форма (10) в U1 проверялась только случайным поиском; вывод о её справедливости не делается.",
          "- `SOURCES.md` (цитаты D4) закоммичен вместе с предрегистрацией B.2 — тоже до прогона.", ""]
    return L


def main():
    a, b, e = load("stage_a.json"), load("stage_b.json"), load("stage_b_explore.json")
    L = ["# RESULTS — TSCAUSAL stage 0.1", "",
         "_Файл порождён `scripts/make_results.py` из `results/json/`. Руками не редактируется._", ""]
    L += prereg_block()
    L += architect_defects()
    if a:
        L += stage_a(a)
    if b:
        L += stage_b(b, load("prereg.json"))
    if e:
        L += explore(e)
    b2, pt = load("stage_b2.json"), load("precision.json")
    if b2:
        L += stage_b2(b2, pt)
    L += ["## Литчек", "",
          "`sources/litcheck/REPORT.md`: среди 8 работ, проверенных в полном тексте (все цитирующие MH24 по "
          "Semantic Scholar, 2508.02463, 2603.12283, 2403.02749 и др.), перечисления фасет временно-симметричного "
          "многогранника не найдено (на 2026-09-21). Оговорки — в отчёте. Это необходимое, но не достаточное "
          "условие для заявления о новизне.", "",
          "## Не делалось", "",
          "Stage C и D не запускались (по промпту).", ""]
    with open(os.path.join(ROOT, "RESULTS.md"), "w") as fh:
        fh.write("\n".join(L))
    print("RESULTS.md записан")


if __name__ == "__main__":
    main()
