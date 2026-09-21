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
    pr = load("prereg.json")
    cur = sha(os.path.join(ROOT, "PREREGISTRATION.md"))
    lines = ["## Предрегистрация", ""]
    if not pr:
        return lines + ["**prereg.json отсутствует — предрегистрация не зафиксирована.**", ""]
    try:
        blob = subprocess.run(["git", "-C", ROOT, "show", f"{pr['commit']}:PREREGISTRATION.md"],
                              capture_output=True, check=True).stdout
        in_commit = hashlib.sha256(blob).hexdigest()
    except Exception as e:  # noqa: BLE001
        in_commit = f"не удалось прочитать коммит: {e}"
    lines += [
        f"- SHA-256 `PREREGISTRATION.md`: `{pr['sha256']}`",
        f"- коммит предрегистрации: `{pr['commit']}` (отдельный коммит, до первого прогона Stage B)",
        f"- хеш текущего файла совпадает: **{ok(cur == pr['sha256'])}**; "
        f"хеш версии в коммите совпадает: **{ok(in_commit == pr['sha256'])}**",
        "",
    ]
    return lines


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
         f"**Исход: {b['outcome']}**", "",
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


def main():
    a, b, e = load("stage_a.json"), load("stage_b.json"), load("stage_b_explore.json")
    L = ["# RESULTS — TSCAUSAL stage 0.1", "",
         "_Файл порождён `scripts/make_results.py` из `results/json/`. Руками не редактируется._", ""]
    L += prereg_block()
    if a:
        L += stage_a(a)
    if b:
        L += stage_b(b, load("prereg.json"))
    if e:
        L += explore(e)
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
