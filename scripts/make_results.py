"""
Порождает RESULTS.md из results/json/*.json. Руками RESULTS.md не редактируется.
Проверяет SHA-256 PREREGISTRATION.md против results/json/prereg.json и против
версии файла в коммите предрегистрации.
"""
import hashlib
from fractions import Fraction

import numpy as np
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


def truth(b):
    """JSON с default=str превращает numpy-bool в строки 'True'/'False' — разбираем явно."""
    if isinstance(b, str):
        if b in ("True", "False"):
            return b == "True"
        raise ValueError(f"не булево значение: {b!r}")
    return bool(b)


def ok(b):
    return "ДА" if truth(b) else "НЕТ"


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


def f6(x):
    try:
        return f"{float(x):.6f}"
    except (TypeError, ValueError):
        return str(x)


def stage_c(c):
    d6, c1, c2 = c["D6"], c["C1"], c["C2"]
    fn = c["functionals"]
    L = ["## Stage C — нарушают ли N1 и N2 физически осмысленные процессы", "",
         f"**Исход: {c['outcome']}**", "",
         f"Режим: {'ОТЛАДОЧНЫЙ (мало стартов)' if c['fast_mode'] else 'полный'}; стартов see-saw: кубиты "
         f"{c['starts']['2']}, кутриты {c['starts']['3']}; солвер {c['solver']} (запасной — SCS). "
         f"Решений SDP: {c['solver_stats']['solves']}, повторов через SCS: {c['solver_stats']['fallback_scs']}, "
         f"отброшенных стартов: {c['solver_stats']['failed']}.", "",
         "### Главное", "",
         "- **Лемма D6.** При маргинализованных `u, v` любой процесс формализма MH24 сводится к ISO-матрице "
         "`(1/d_Ad_B)(1 + T_{A_O B_I} + S_{A_I B_O})`. Такая матрица всегда является смесью одностороннего канала "
         "A→B и одностороннего канала B→A. Значит, в сценарии Stage B ничто в формализме не нарушает ни одной "
         "фасеты основного многогранника TS, включая N1 и N2, при любых размерностях. Доказательство — "
         "PREREGISTRATION_C.md §2, численная проверка ниже.",
         "- **Обратная сторона.** Если разрешить предселекцию (статистика условна по u), N1 и N2 нарушает уже "
         "процесс с определённым порядком (схема z, ниже). Поэтому N1 и N2 не свидетельствуют о "
         "неопределённости ни в каком режиме формализма: без селекции их ничто не нарушает, с селекцией их "
         "нарушает и причинно-упорядоченное. Центральная гипотеза Stage C в этой постановке непроверяема.", "",
         "### C.0 Функционалы и масштаб", "",
         "Полная запись классов (`t = abxy`, веса 1; при p(a,b) = 1/4 это игры с успехом не выше 1/2):", ""]
    for k in ("N1", "N2"):
        L.append(f"- **{k}** ({fn[k]['size']} фасет): " + " + ".join(f"p({t})" for t in fn[k]["support"]) + " ≤ 1/2")
    for k in sorted(x for x in fn if x.startswith("cl")):
        L.append(f"- **{k}** (класс только классического замыкания, {fn[k]['size']} фасет): "
                 + " + ".join(f"{w}·p({t})" if w != "1" else f"p({t})" for t, w in fn[k]["support"].items())
                 + f" ≤ {fn[k]['rhs']}")
    L += ["", f"Классов замыкания, совпавших по канонической форме с классами TS: {c['closure_classes_matching_N1_N2']} "
          "(положительность, N1, N2).", "",
          "**Пять чисел** (точно; для N1 и N2 — в вероятностях игры). «Максимум 3 при границе 1» из B.2 был "
          "в единицах проекции на аффинную оболочку; в вероятностях это 3/4 при границе 1/2.", "",
          "| класс | граница | алгебр. max при U2 | F | B | F∩B | TS (Def-II) | классич. замыкание |",
          "|---|---|---|---|---|---|---|---|"]
    five = c["C0_five_numbers"]
    for k in [x for x in five if x != "U2_polytope_vertices"]:
        v = five[k]
        L.append(f"| {k} | {v['rhs']} | {v['algebraic_U2']} | {v['F']} | {v['B']} | {v['F_cap_B']} | {v['TS']} | {v['classical_closure']} |")
    L += ["", f"U2-многогранник (p ≥ 0, p(a,b) = p(x,y) = 1/4) имеет {five['U2_polytope_vertices']} вершины, это ¼ × "
          "перестановочные матрицы. Для N1 и N2 множества F, B и F∩B достигают U2-алгебраического максимума 3/4.", "",
          "Определения лаборатории, процесс-матрицы, условий допустимости и формулы для p — SOURCES.md, MH-22…MH-28; "
          "не цитатами являются D5 (множитель R-боксов ¼) и D6. Класс R зафиксирован в PREREGISTRATION_C.md §1 "
          "(коммит c9d9095) до расчётов.", "",
          "### Лемма D6: численная проверка", ""]
    for dd in ("d2", "d3"):
        x = d6[dd]
        L.append(f"- {dd}: буквальные отображения Wcons2–4, vcons1–3, ucons1–3 допускают {x['allowed_count']} "
                 f"базисных элементов (ожидалось {x['expected']}), типы {x['types']}; недиагональных откликов "
                 f"{x['non_diagonal_hits']}")
    L += [f"- классификатор различает классы: TF (без постселекции) — {d6['TF_no_post']['count']} элементов, "
          f"TB — {d6['TB_no_pre']['count']}, только Wcons — {d6['TS_only_Wcons']['count']}, OCB по B15 — "
          f"{d6['OCB_B15']['count']}; типы TF совпадают с OCB: **{ok(d6['TF_equals_OCB_types'])}** "
          "(утверждение MH-27 подтверждено на уровне типов членов)",
          f"- разложение W = qW₁ + (1−q)W₂ на 100 + 100 случайных W ∈ R на границе положительности (d = 2, 3): "
          f"**{ok(d6['decomposition_pass'])}** (худшие min eig W₁, W₂: {d6['decomposition']['d2']['psd_W1']:.1e}, "
          f"{d6['decomposition']['d3']['psd_W2']:.1e}; ошибка восстановления ≤ "
          f"{max(v['recon'] for v in d6['decomposition'].values()):.1e})", "",
          "### C.1 Калибровки", ""]
    mh = c1["mh_example"]
    L += [f"1. **Пример MH24 (MH-29): буквально НЕ пройден**, причина локализована в статье.",
          f"   - Операция Боба при β = 1 с множителем 1/2 из статьи нарушает ур. (2): невязка "
          f"{mh['literal_bobop']['bob_instrument_residual']}. С множителем 1/4 («maximally mixed state», как в тексте) — "
          f"{mh['bobop_beta1_factor_1/4']['bob_instrument_residual']}.",
          f"   - Буквальное ур. (9): {f6(mh['literal_bobop']['eq9_literal'])} вместо (2+√2)/4 = 0.853553; "
          f"буквальное ур. (11): {f6(mh['literal_bobop']['eq11_literal'])} вместо 1/2.",
          f"   - Перебор 36 назначений «чья догадка требуется при (α, β)»: значение статьи (2+√2)/4 даёт ровно одно — "
          f"{mh['readings_reproducing_fwd']} (догадка Боба при β = 1, Алисы при β = 0; это исходная игра OCB). "
          f"Значение 1/2 для обратной игры тоже даёт ровно одно — {mh['readings_reproducing_bwd']}. Точное совпадение "
          "с иррациональным числом при единственном прочтении подтверждает конвенции (CJ, порядок подсистем, операторы).",
          f"   - exampleW удовлетворяет Wcons и vcons и нарушает ucons ({f6(mh['constraint_residuals']['ucons1'])}): "
          "«requires pre-selection, but not post-selection» подтверждено. Аппарат: **"
          f"{ok(mh['machinery_pass'])}**.",
          f"2. **Нормировка D5** (эта калибровка может провалиться): для случайных W ∈ R и TS-операций "
          f"Σp = 1, p(a,b) = p(x,y) = 1/4 с отклонением {c1['normalization_D5']['worst_deviation_TS']:.1e}. Контроль: "
          f"операция Боба только с прямой причинностью (невязка обратной "
          f"{c1['normalization_D5']['control_bob_backward_residual']}) даёт отклонение p(x,y) на "
          f"{c1['normalization_D5']['control_forward_only_bob_pxy_deviation']}. **{ok(c1['normalization_D5']['pass'])}**"]
    b = c1["b15"]
    L += [f"3. **OCB (B15).** Точный пример: GYNI {b['wsimple']['GYNI']:.12f} (ожидание {b['wsimple']['GYNI_expected']:.12f}), "
          f"LGYNI {b['wsimple']['LGYNI']:.12f}. W_max из App. C с их инструментами: GYNI {b['W_max_appC']['GYNI']:.10f} "
          f"против наименьшего корня полинома {b['W_max_appC']['GYNI_expected_smallest_root']:.10f}. See-saw OCB на кубитах: "
          f"GYNI {b['seesaw']['GYNI']['best']:.6f} (ориентир 0.5694), LGYNI {b['seesaw']['LGYNI']['best']:.6f} (0.8194); "
          f"стартов {b['seesaw']['GYNI']['starts']}, упавших {b['seesaw']['GYNI']['failed_starts'] + b['seesaw']['LGYNI']['failed_starts']}. "
          f"**{ok(b['pass'])}**"]
    ps = c1["postselection"]
    L += [f"4. **Постселекция достигает максимума.** Процесс без связи между сторонами (приготовление входов = u, "
          f"измерение выходов = v; ΣᵥW удовлетворяет vcons: {ok(ps['sum_v_satisfies_vcons'])}, ΣᵤW удовлетворяет ucons: "
          f"{ok(ps['sum_u_satisfies_ucons'])}, Σᵤᵥ W ∈ R: {ok(ps['sum_uv_in_R'])}). Условно на событие (u, v): "
          f"N1 = {ps['N1']['value']}, N2 = {ps['N2']['value']}, это U2-алгебраический максимум 3/4, p(a,b) = 1/4 сохраняется. "
          "Утверждение статьи о полном классе воспроизведено, причём процессом без какой-либо связи между лабораториями.",
          f"5. **Солвер:** известная задача — ошибка {c1['solver']['known_problem_error']:.1e}; недопустимая — статус "
          f"`{c1['solver']['infeasible_status']}`, see-saw на ней падает: {ok(c1['solver']['seesaw_raises_on_infeasible'])}. "
          f"**{ok(c1['solver']['pass'])}**",
          f"6. **Классическое замыкание:** максимум каждого функционала на его вершинах равен границе: "
          f"**{ok(all(c1['classical_closure_max_equals_bound'].values()))}**", "",
          f"Ворота C.1 (по аппарату): **{ok(c1['pass'])}**; буквальная проверка примера MH24 — **НЕТ** (см. п. 1).", "",
          "### C.2 Иерархия процессов", "",
          f"P3 с общим контролем ∈ R: {ok(c['P3_membership']['common_in_R'])}. P3 с независимыми контролями ∈ R: "
          f"{ok(c['P3_membership']['independent_in_R'])}: ветви «вперёд/назад» дают члены A_O B_O и A_I B_I, невязки "
          f"vcons/ucons {max(c['P3_membership']['independent_residuals'].values())}; без селекции такой процесс невозможен. "
          "P2 = R ∩ OCB = R: все типы ISO разрешены и в OCB (D6), поэтому P2 совпадает с P4.", "",
          "| d | класс | граница | P1: A→B | P1: B→A | P3 (общий контроль) | P4 = R (= P2) |", "|---|---|---|---|---|---|---|"]
    for key, row in c2.items():
        dd, name = key.split("_", 1)
        g = lambda f: f6(row[f]["max"]) if f in row else "—"  # noqa: E731
        L.append(f"| {dd[1:]} | {name} | {fn[name]['rhs']} | {g('P1_AB')} | {g('P1_BA')} | {g('P3_common')} | {g('P4_R')} |")
    L += ["", f"Подтверждённые нарушения (mpmath, 50 знаков; W и инструменты допустимы): {c['violations'] or 'нет'}.",
          f"Превышения из see-saw, не подтверждённые пересчётом: {({k: v for k, v in c['unconfirmed_excess'].items() if v}) or 'нет'}.", ""]
    ver = [(k, f, v["verify"]) for k, row in c2.items() for f, v in row.items() if isinstance(v, dict) and v.get("verify")]
    if ver:
        L += ["Пересчёт свидетелей (явные W и инструменты — `results/json/stage_c_witnesses.json`):", ""]
        for k, f, v in ver:
            L.append(f"- {k} / {f}: значение (mpmath) {v['value_mp'][:14]}; сдвиг W при починке {v['W_repair_shift']:.1e}; "
                     f"невязка инструментов {v['instr_res']:.1e}; min eig инструментов {v['instr_min_eig']:.1e}; W ∈ R: {ok(v['W_in_R'])}")
        L.append("")
    tf = c["TF_pre"]
    L += ["### Вне R: диагностика режима с предселекцией", "",
          f"- **Схема z** с определённым порядком A≼B и предселекцией входа Алисы |0⟩: воспроизводит z точно — "
          f"{ok(tf['z_circuit']['reproduces_z'])}. W допустима по OCB (невязка {tf['z_circuit']['W_ocb_residual']}), не лежит в R "
          f"({ok(not tf['z_circuit']['W_in_R'])}); после маргинализации u лежит в R: {ok(tf['z_circuit']['u_marginal_W_in_R'])}. "
          f"Точку z отсекают {tf['z_cut_by_TS_facets']} фасет TS, это члены N1 и N2. **Процесс с определённым порядком нарушает "
          "N1 и N2, как только разрешена предселекция.**",
          f"- See-saw по классу OCB (TF) с TS-операциями: N1 до {f6(tf['seesaw_N1']['max'])}, N2 до {f6(tf['seesaw_N2']['max'])} "
          "(граница 1/2; вне U2-оболочки значение зависит от выбранного представителя класса).", "",
          "### C.3 Когерентность направления", "",
          "В R управляющий кубит нельзя ни приготовить в |+⟩ (это предселекция), ни спроецировать (это постселекция). "
          "Поэтому W̄_P3 = ½(W_f + W_b) тождественно совпадает с дефазированной смесью, и тест C.3 в R вырожден. "
          "Нарушения P3 в R нет, так что условие C.3 не наступило.", ""]
    rows = [
        ("C.0.2: U2-алг. максимум 3/4, TS = 1/2", "0.9", five["N1"]["algebraic_U2"] == "3/4" and five["N2"]["algebraic_U2"] == "3/4" and five["N1"]["TS"] == "1/2"),
        ("C.0.2: F, B, F∩B достигают 3/4", "0.5", all(five[k][x] == "3/4" for k in ("N1", "N2") for x in ("F", "B", "F_cap_B"))),
        ("D6(a): 19 и 129", "0.95", d6["d2"]["allowed_count"] == 19 and d6["d3"]["allowed_count"] == 129),
        ("D6(b): разложение", "0.97", d6["decomposition_pass"]),
        ("C.1.1: MH24 (2+√2)/4 и 1/2 буквально", "0.9", truth(mh["literal_pass"])),
        ("C.1.2: B15 точно и see-saw ±1e-3", "0.85", b["pass"]),
        ("C.1.4: постселекция даёт 3/4", "0.95", abs(ps["N1"]["value"] - 0.75) < 1e-12 and abs(ps["N2"]["value"] - 0.75) < 1e-12),
        ("C.1.5: солвер", "0.97", c1["solver"]["pass"]),
        ("C.2: N1, N2 не нарушаются в P1–P4 (d = 2, 3)", "0.95",
         not any(k.endswith(("N1", "N2")) for k in c["violations"])),
        ("C.2: P3 с независимыми контролями ∉ R", "0.85", not c["P3_membership"]["independent_in_R"]),
        ("C.2: P1 (квантовый) нарушает хотя бы один из cl3–cl6", "0.4",
         any(k.startswith("d2_cl") and any(f.startswith("P1") for f in v) for k, v in c["violations"].items())),
        ("TF-pre: N1, N2 нарушаются, в т.ч. схемой z", "0.95", tf["z_circuit"]["reproduces_z"] and tf["z_cut_by_TS_facets"] > 0),
        ("C.3: в R когерентный P3 = дефазированный", "0.95", True),
        ("итог: «P4 не нарушает» (N1, N2)", "0.95", not any(k.endswith(("N1", "N2")) for k in c["violations"])),
    ]
    L += ["### Прогнозы C и результат", "", "| прогноз исполнителя | уверенность | сбылся |", "|---|---|---|"]
    L += [f"| {a} | {b_} | {ok(r)} |" for a, b_, r in rows]
    n12 = any(k.endswith(("N1", "N2")) for k in c["violations"])
    L += ["", f"Прогнозы архитектора: P1 не нарушает — **{ok(not n12)}** (для N1 и N2; классы замыкания cl3–cl6 "
          "квантовый P1 нарушает, но это фасеты классического, а не Def-II-многогранника); P2 не нарушает N1 и N2 — "
          f"**{ok(not n12)}**; P3 нарушает хотя бы одно из N1, N2 без постселекции — **{ok(n12)}**; пункт о дефазировке — "
          "не наступил.", "",
          "### Отклонения от промпта", "",
          "- Кутриты: только N1 и N2 для P4 (⊇ P1, P2) и P3. Полный набор (6 функционалов × 3 семейства) потребовал бы "
          "часов, а лемма D6 закрывает вопрос для любых размерностей аналитически.",
          "- Солвер: при `optimal_inaccurate` шаг повторяется через SCS (eps 1e-9); если и там не `optimal`, старт отбрасывается. "
          "В предрегистрации было «падает на любом статусе, кроме optimal»; значения из неоптимальных решений "
          "по-прежнему не принимаются.",
          "- Нарушения засчитываются только после починки положительности (W сдвигается к 1/d², к инструментам "
          "подмешивается допустимый M₀ = 1/(2d)·1; обе операции сохраняют линейные условия) и пересчёта в mpmath.",
          "- Пример MH24 буквально не воспроизведён (см. C.1.1); причина локализована в статье, для калибровки "
          "аппарата добавлена независимая проверка D5, которая может провалиться.",
          "- «SDP по всему классу» (P4) нелинеен по (W, инструменты), поэтому see-saw даёт только нижние оценки. "
          "Верхнюю оценку «не выше границы» даёт лемма D6, а не численный расчёт.", ""]
    return L


def stage_d(D):
    def mx(tab, pref):
        """максимум по порядкам: {cl: {d: max}}"""
        r = {}
        for k, v in tab.items():
            name, order, d = k.split("_")
            r.setdefault(name, {}).setdefault(d, []).append((v["max"], order, v))
        return r
    L = ["## Stage D — квантово-классический разрыв на cl3–cl6", "",
         f"Режим: {'ОТЛАДОЧНЫЙ' if D['fast'] else 'полный'}; стартов see-saw (D.4): {D['starts']}; решений SDP "
         f"{D['solver_stats']['solves']}, повторов через SCS {D['solver_stats']['fallback_scs']}, отброшено стартов "
         f"{D['solver_stats']['failed']}; время {D['seconds']} с.", "",
         "### Главное: разрыв — это CHSH и граница Цирельсона в переобозначенных ролях", "",
         "Вывод D8 (PREREGISTRATION_D.md §2, записан до расчётов) проверен численно. TS-процесс с определённым "
         "порядком без селекции эквивалентен Белловскому сценарию на максимально запутанном состоянии:",
         "- «вход» Алисы — её **исход** x, «результат» — её **доход** a;",
         "- у Боба вход — доход b, результат — исход y;",
         "- на маргиналы наложены условия `P(a|0)+P(a|1)=1`, `P(y|0)+P(y|1)=1`.",
         "",
         "Ур. (3) и (4) MH24 — это отсутствие сигнала в этих ролях. Def-II P_AB — NS-множество, классическое "
         "замыкание — локальное множество, 8 «нереализуемых» вершин P_AB — PR-ящики. Обратная нормировка "
         "запрещает передавать по каналу информацию об x, и канал работает как запутанный ресурс без сигнала.", ""]
    d8 = D["D8"]
    L += [f"- Сведение TS ↔ (σ, F) ↔ Белл на случайных точках (d = 2, 3, 4, комплексные и вещественные): худшее "
          f"отклонение {max(d8['random'].values()):.1e}. На свидетелях Stage C: "
          f"{sum(1 for v in d8['stage_c_witnesses'].values() if v['p_error'] < 1e-8)} из {len(d8['stage_c_witnesses'])} "
          f"воспроизведены (ошибка p < 1e-8). Остальные — смеси порядков (P4, P3), для них сведение по одному "
          "порядку неприменимо, см. таблицу в JSON.",
          f"- PR-ящики: вершин Def-II P_AB вне классического замыкания {D['PR_boxes']['n_outside_closure']}, все "
          f"PR-ящики: **{ok(D['PR_boxes']['all_PR'])}**.", ""]
    ch = D["D01_chsh"]
    L += ["### D.0.1 Классы cl3–cl6 как CHSH", "",
          "Для каждого класса и порядка — проверка, равен ли функционал на aff(P_порядка) α·CHSH_c + β, "
          "где CHSH_c означает выигрыш при a ⊕ y = (x⊕c₁)(b⊕c₂) ⊕ c₃ (точная арифметика).", "",
          "| класс | порядок | CHSH (c₁,c₂,c₃) | α | β |", "|---|---|---|---|---|"]
    for k, v in ch.items():
        name, order = k.split("_")
        L.append(f"| {name} | {order} | {tuple(v['chsh']) if v else 'не CHSH'} | {v['alpha'] if v else '—'} | {v['beta'] if v else '—'} |")
    L += ["", "Там, где стоит «не CHSH», класс на этом порядке не нарушается ничем: NS-максимум (Def-II) равен "
          "классической границе, см. D.3. Разрыв есть ровно на тех порядках, где класс — переименованный CHSH.",
          "", "Если класс на порядке равен α·CHSH + β, то его классическая граница, квантовый максимум и NS-максимум — "
          "это образы 3/4, (2+√2)/4 и 1 при отображении t ↦ αt + β (CHSH здесь — вероятность выигрыша со "
          "множителем ¼).", ""]
    an = D["D02_analytic"]
    L += ["### D.0.2 Минимальный свидетель (кубиты, аналитически)", ""]
    for k, v in an.items():
        L.append(f"- **{k}** ({v['order']}): значение **{v['value_exact']}** ≈ {v['value_float']:.10f} при границе {v['rhs']}; "
                 f"TS-форма в mpmath: {v['ts_value_mp'][:16]}; невязки: сведённая {v['reduced_residual']:.1e}, "
                 f"инструменты {v['ts_instrument_residual']:.1e}.")
    L += ["",
          "Словами (тождественный канал A_O→B_I):",
          "- **Алиса** отбрасывает свой вход. Исход x равновероятен (это «монета» Алисы). Она готовит собственное "
          "состояние Z-базиса при x = 0 или X-базиса при x = 1, а значение бита задаёт доход a (с переименованием, "
          "зависящим от x).",
          "- **Канал** передаёт кубит Бобу.",
          "- **Боб** измеряет вдоль (Z ± X)/√2, знак выбирает доход b; результат — исход y. На выход он отдаёт "
          "максимально смешанное состояние.",
          "",
          "Обратная нормировка выполнена, потому что при усреднении по a состояние Алисы максимально смешано для "
          "каждого x. Поэтому x не передаётся — передаётся только связь a с x. Это BB84-подобная схема, где базис — "
          "исход, а не настройка.", ""]
    L += ["### D.1 Полнота классического замыкания", "",
          "**Доказательство** — вывод D7 (PREREGISTRATION_D.md §1). Классические TS-схемы A≼B любой размерности — "
          "это ровно локальные модели `¼ E_λ q_λ(a|x) r_λ(y|b)` с усреднёнными условиями на маргиналы. Их множество "
          "есть образ многогранника M из Stage B; вершины M рациональны и реализуются при N ≤ 4. Граница cl3–cl6 "
          "доказана для всех размерностей.", "", "Численный контроль (see-saw с диагональными σ и F):", ""]
    for name, dims in mx(D["D1_classical"], "").items():
        L.append(f"- {name}: " + ", ".join(f"d={d[1:]}: {max(v for v, _, _ in lst):.6f}" for d, lst in sorted(dims.items()))
                 + f" (граница {dims[next(iter(dims))][0][2]['rhs']})")
    L += [""]
    fw = D["D2_forward"]
    L += ["### D.2 Контроль: чисто прямой сценарий", "",
          "Операции только с прямой нормировкой, порядок A≺B, p(a,b) = 1/4. Функционалы перенесены буквально "
          "(те же веса на p(a,b,x,y)); отдельно показан классический максимум с фильтром p(x,y) = 1/4 (F_AB).", "",
          "| класс, порядок | граница TS | классич. max (буквально) | классич. max с U2 | схема «передать a» | квантовый see-saw | разрыв |",
          "|---|---|---|---|---|---|---|"]
    for k, v in fw.items():
        q = "все старты упали" if v["quantum_seesaw_max"] is None else f"{v['quantum_seesaw_max']:.6f}"
        g = "—" if v["gap"] is None else f"{v['gap']:.1e}"
        L.append(f"| {k} | {v['rhs']} | {v['classical_max_literal']} | {v['classical_max_with_U2_filter']} | "
                 f"{v['circuit_send_a_value']:.6f} | {q} (упало {v['failed_starts']}) | {g} |")
    gaps = [v["gap"] for v in fw.values() if v["gap"] is not None]
    if len(gaps) < len(fw):
        L.append("")
        L.append(f"Для {len(fw) - len(gaps)} строк квантовый see-saw не дал ни одного оптимального решения. Для них "
                 "разрыв численно не проверен, но аргумент ниже (квантовое множество лежит внутри классического "
                 "многогранника) от численного расчёта не зависит.")
    L += ["", f"Максимальный разрыв «квант − классика» в прямом сценарии: {max(gaps):.1e}. "
          f"**Разрыва {'нет' if max(gaps) < 1e-6 else 'ЕСТЬ'}.** Причина: в прямом сценарии классический канал "
          "неограниченной размерности передаёт a и реализует любую вершину временно-прямого многогранника "
          "(B15-7: вершины детерминированы). Квантовое множество лежит внутри этого многогранника, так что "
          "превзойти классику не может. Калибровка «передать a» насыщает квантовый максимум.", ""]
    np_ = D["D3_npa"]
    cal = np_["calibration_CHSH"]
    L += ["### D.3 Верхняя граница: NPA", "",
          f"Калибровка (NPA08): CHSH без условий на маргиналы — уровень 1+AB {cal['level_1+AB']:.9f}, уровень 2 "
          f"{cal['level_2']:.9f}, граница Цирельсона {cal['tsirelson']:.9f}: **{ok(cal['pass'])}**.", "",
          "| класс, порядок | классич. (LP) | NPA 1+AB | NPA 2 | NPA без условий | NS (Def-II) | в [классич., NS] |",
          "|---|---|---|---|---|---|---|"]
    for k, v in np_.items():
        if k == "calibration_CHSH":
            continue
        L.append(f"| {k} | {v['local_constrained']} | {v['npa_1+AB']:.9f} | {v['npa_2']:.9f} | "
                 f"{v['npa_1+AB_without_marginal_constraints']:.9f} | {v['NS_constrained(DefII)']} | {ok(v['between_local_and_NS'])} |")
    L += ["", "NPA ограничивает сверху все квантовые Белловские корреляции (любые состояния и размерности), "
          "а по D8 квантовые TS-корреляции с определённым порядком — их подмножество. По лемме D6 смеси порядков "
          "линейный функционал не увеличивают. Если NPA совпадает с see-saw, оптимум найден.", ""]
    L += ["### D.4 Размерность и вещественность", "",
          "| класс | d | комплексные (max по порядкам) | вещественные |", "|---|---|---|---|"]
    cx, rl = mx(D["D4_complex"], ""), mx(D["D4_real"], "")
    for name in sorted(cx):
        for d in sorted(cx[name]):
            L.append(f"| {name} | {d[1:]} | {max(v for v, _, _ in cx[name][d]):.9f} | {max(v for v, _, _ in rl[name][d]):.9f} |")
    ver = [(k, v["verify"]) for tab in ("D4_complex", "D4_real") for k, v in D[tab].items() if v.get("verify")]
    worst = max((abs(float(v["ts_value_mp"]) - D[t][k]["max"]) for t in ("D4_complex", "D4_real")
                 for k, v2 in D[t].items() for v in [v2.get("verify")] if v), default=0)
    real_imag = max((v["verify"]["real_max_imag"] for v in D["D4_real"].values() if v.get("verify")), default=0)
    L += ["", f"Все превышения пересчитаны в TS-форме в mpmath ({len(ver)} свидетелей); наибольшее расхождение "
          f"с see-saw {worst:.1e}. Мнимые части вещественных свидетелей: ≤ {real_imag:.1e}.",
          "При d = 3 максимум ниже, чем при d = 2 и 4. Сведение D8 фиксирует максимально запутанное состояние "
          "размерности d, и кубитная CHSH-стратегия в нечётную размерность целиком не вкладывается; при d = 4 "
          "значение возвращается к 3+√2. Значение сверх 3+√2 не найдено ни при одной размерности, что согласуется с NPA.", ""]
    L += ["### D.5 «Повёрнуто-классические» операции", "",
          "Поворот U⊗V операции Алисы поглощается каналом и мерой Боба, поэтому «повёрнуто-классическая» Алиса — "
          "это диагональные σ при произвольных канале и F. Смеси таких операций дают совместно измеримые "
          "`A_{a|x}`, а совместно измеримые измерения одной стороны порождают только локальные корреляции.", ""]
    for tab, lab in (("D5_alice_classical", "Алиса классическая, Боб квантовый"), ("D5_bob_classical", "Боб классический, Алиса квантовая")):
        L.append(f"- {lab}: " + "; ".join(f"{name} {max(v for dd_ in dims.values() for v, _, _ in dd_):.6f}"
                                           for name, dims in mx(D[tab], "").items()))
    L += ["", "Наблюдение: разрыв требует несовместимых измерений у **обеих** сторон, как в CHSH.", ""]
    # --- исход и прогнозы
    viol_orders = [k for k, v in np_.items() if k != "calibration_CHSH" and float(Fraction(v["NS_constrained(DefII)"])) > float(Fraction(v["local_constrained"]))]
    npa_q = {k: np_[k]["npa_1+AB"] for k in viol_orders}
    ss_q = {}
    for k in viol_orders:
        name, order = k.split("_")
        ss_q[k] = max(D["D4_complex"][f"{name}_{order}_d{d}"]["max"] for d in (2, 3, 4))
    npa_match = all(abs(npa_q[k] - ss_q[k]) < 1e-6 for k in viol_orders)
    d1_num = all(v["max"] <= v["rhs"] + 1e-6 for v in D["D1_classical"].values())
    fw_gaps = [v["gap"] for v in D["D2_forward"].values() if v["gap"] is not None]
    d2_nogap = bool(fw_gaps) and max(fw_gaps) < 1e-6
    tsir = {k: (float(Fraction(np_[k]["local_constrained"])) + (np.sqrt(2) - 1) *
                (float(Fraction(np_[k]["NS_constrained(DefII)"])) - float(Fraction(np_[k]["local_constrained"]))))
            for k in viol_orders}
    tsir_match = all(abs(npa_q[k] - tsir[k]) < 1e-6 for k in viol_orders)
    grow = any(D["D4_complex"][f"{k.split('_')[0]}_{k.split('_')[1]}_d{d}"]["max"] > ss_q[k] + 1e-6 for k in viol_orders for d in (3, 4))
    real_ok = all(abs(max(D["D4_real"][f"{k.split('_')[0]}_{k.split('_')[1]}_d{d}"]["max"] for d in (2, 3, 4)) - npa_q[k]) < 1e-6
                  for k in viol_orders)
    d5 = all(v["max"] <= v["rhs"] + 1e-6 for t in ("D5_alice_classical", "D5_bob_classical") for v in D[t].values())
    chsh_ok = all(D["D01_chsh"][k] is not None for k in viol_orders)
    outcome = ("ГРАНИЦА ТИПА ЦИРЕЛЬСОНА: D.1 доказана, в D.2 разрыва нет, D.3 совпала (NPA = see-saw)"
               if (d1_num and d2_nogap and npa_match) else "не все условия исхода выполнены — см. таблицу")
    L = L[:2] + [f"**Исход: {outcome}.** Оговорка: по D8 и D.0.1 это буквально граница Цирельсона для CHSH в "
                 "переобозначенных ролях, а не новый эффект (литчек: темпоральный CHSH — Fritz 2010, Brukner et al. 2004).",
                 ""] + L[2:]
    L += ["### Прогнозы D и результат", "", "| прогноз исполнителя | уверенность | сбылся |", "|---|---|---|"]
    rows = [
        ("D8: сведение численно точное (≤ 1e-10) на случайных точках", "0.95", max(d8["random"].values()) < 1e-10),
        ("D8: 8 вершин вне замыкания — PR-ящики", "0.9", D["PR_boxes"]["all_PR"] and D["PR_boxes"]["n_outside_closure"] == 8),
        ("D.0.1: cl_k на нарушаемом порядке = переименованный CHSH", "0.7", chsh_ok),
        ("D.0.2: кубитный BB84/CHSH-свидетель даёт ровно 3+√2 (cl3)", "0.75", D["D02_analytic"]["cl3"]["value_exact"] == "sqrt(2) + 3"),
        ("D.1: классика ≤ границы при d = 2…6", "0.97", d1_num),
        ("D.2: разрыва в прямом сценарии нет", "0.95", d2_nogap),
        ("D.3: NPA = Цирельсон-образ (3+√2; 7/2+√2)", "0.85", tsir_match),
        ("D.4.1: d = 3, 4 не растёт", "0.9", not grow),
        ("D.4.2: вещественная КМ достигает оптимума", "0.9", real_ok),
        ("D.5: повёрнуто-классическая сторона — нет разрыва", "0.95", d5),
        ("итог: «граница типа Цирельсона»", "0.8", outcome.startswith("ГРАНИЦА")),
    ]
    L += [f"| {a} | {b_} | {ok(r)} |" for a, b_, r in rows]
    L += ["", "Прогнозы архитектора: D.1 (замыкание полное, граница доказывается) — **ДА** (D7); "
          f"D.2 (разрыва нет) — **{ok(d2_nogap)}**; D.3 (3+√2 — оптимум по всем размерностям) — **{ok(npa_match and tsir_match)}**; "
          f"D.4.1 (не растёт) — **{ok(not grow)}**; D.4.2 (вещественная КМ достигает) — **{ok(real_ok)}**.", "",
          "### Интерпретация", "",
          "Гипотеза архитектора («разрыв создаёт временная симметрия операций, в прямой картине его нет») "
          "формально подтверждается: в D.2 разрыва нет. Механизм, однако, стандартный. Обратная нормировка "
          "запрещает каналу нести информацию об исходе x, и схема с определённым порядком становится "
          "Белловским сценарием без сигнала на максимально запутанном ресурсе (D8), а разрыв — нелокальностью CHSH. "
          "Эквивалентность последовательных (темпоральных) корреляций синглетным известна: BTCV04, FR10. "
          "Новым может быть только оформление: TS-операции с доходами и исходами, где исход Алисы играет "
          "роль настройки. Такой формулировки литчек не нашёл, но это переформулировка, а не новое неравенство. "
          "Лемма D6 в общем двустороннем виде не найдена; ближайший однослотовый аналог — AB26 "
          "(arXiv:2602.00856), его надо цитировать.", "",
          "### Отклонения от промпта", "",
          "- D.3: вместо «prepare-and-measure-иерархии» использован NPA для эквивалентного Белловского сценария (D8). "
          "Это строже: NPA ограничивает все квантовые корреляции любых размерностей, а калибровка на CHSH "
          "(граница Цирельсона) подтверждена цитатой NPA08.",
          "- D.4: see-saw проведён в сведённой форме (σ, F), эквивалентной TS-форме по D8 (эквивалентность проверена "
          "численно в обе стороны). Каждое превышение переведено обратно в TS-форму (W, инструменты) и "
          "пересчитано в mpmath.",
          "- D.2: функционалы перенесены буквально (те же веса); вне U2-оболочки их значение зависит от "
          "выбранного представителя класса. Отдельно показан вариант с фильтром p(x,y) = 1/4.",
          "- D.1: вместо численного перебора классических схем размерности 5, 6 основным аргументом служит "
          "доказательство D7. Численный контроль — классический see-saw при d = 2…6.",
          f"- Время по разделам (с): {D.get('timing', {})}.", ""]
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
    c = load("stage_c.json")
    if c:
        L += stage_c(c)
    dd = load("stage_d.json")
    if dd:
        L += stage_d(dd)
    L += ["## Литчек", "",
          "`sources/litcheck/REPORT.md`: среди 8 работ, проверенных в полном тексте (все цитирующие MH24 по "
          "Semantic Scholar, 2508.02463, 2603.12283, 2403.02749 и др.), перечисления фасет временно-симметричного "
          "многогранника не найдено (на 2026-09-21). Оговорки — в отчёте. Это необходимое, но не достаточное "
          "условие для заявления о новизне.", "",
          "## Не делалось", "",
          "Stage D не запускался (по промпту). Письмо авторам и литчек перед заявлениями о новизне отложены "
          "решением архитектора (PROMPT stage C).", ""]
    with open(os.path.join(ROOT, "RESULTS.md"), "w") as fh:
        fh.write("\n".join(L))
    print("RESULTS.md записан")


if __name__ == "__main__":
    main()
