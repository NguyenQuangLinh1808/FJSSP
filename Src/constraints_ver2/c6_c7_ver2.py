from collections import defaultdict


def apply_c6_c7_ver2(solver):
    """
    FJSSP Overlap - Phiên bản tối ưu hóa cấu trúc sâu (Structural Optimization).

    Tích hợp:
    1.  Optimization 1-6 (Nén Overlap, Forced Ordering, Interval Check).
    2.  Mandatory Shortcut: Loại bỏ SM rác cho các thao tác chỉ có 1 máy.
    3.  Pairwise Capacity Check: Loại bỏ sớm các cặp (M_i, M_j) không thể cùng tồn tại trên một máy.
    4.  CSLB (Conditional Start Lower Bound): Ép biên thời gian ngay khi xác định dùng chung máy.
    """

    # ── Gom nhóm các op có thể chạy trên cùng một máy ────────────────────
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            mach_to_ops[m].append((i, p))

    sm_cache = {}  # (min(i,j), max(i,j), mach) → sm_var

    for mach, ops_on_m in mach_to_ops.items():
        n = len(ops_on_m)
        for a in range(n):
            for b in range(a + 1, n):
                i, p_i = ops_on_m[a]
                j, p_j = ops_on_m[b]

                # Bỏ qua cặp cùng job — precedence constraint đã lo phần này
                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                # ── Optimization 6: active-interval intersection check ────
                if solver.lst[i] + p_i <= solver.est[j]:
                    continue
                if solver.lst[j] + p_j <= solver.est[i]:
                    continue

                # ── Optimization 2-3: Forced ordering detection ──────────
                j_before_i = (solver.est[i] + p_i > solver.lst[j])
                i_before_j = (solver.est[j] + p_j > solver.lst[i])

                m_var_i = solver.get_var('M', i, mach)
                m_var_j = solver.get_var('M', j, mach)

                # ── Optimization 3: Conflict detection ───────────────────
                if j_before_i and i_before_j:
                    solver.add_clause_smart([-m_var_i, -m_var_j])
                    continue

                # ── NEW: Pairwise Capacity Check ────────────────────────
                # Nếu sắp xếp tối ưu nhất vẫn vượt quá horizon -> không thể cùng máy mach
                completion_i_before_j = max(solver.est[j], solver.est[i] + p_i) + p_j
                completion_j_before_i = max(solver.est[i], solver.est[j] + p_j) + p_i
                min_completion = min(completion_i_before_j, completion_j_before_i)

                if min_completion > solver.horizon:
                    solver.add_clause_smart([-m_var_i, -m_var_j])
                    continue

                # ── Optimization 1 & Mandatory Shortcut ──────────────────
                len_mach_i = len(solver.ops[i]['machines'])
                len_mach_j = len(solver.ops[j]['machines'])

                if len_mach_i == 1 and len_mach_j == 1:
                    sm_var_used = False
                elif len_mach_i == 1:
                    sm_var_used = m_var_j
                elif len_mach_j == 1:
                    sm_var_used = m_var_i
                else:
                    sm_key = (min(i, j), max(i, j), mach)
                    if sm_key not in sm_cache:
                        sm_var = solver.get_var('SM', i, j, mach)
                        sm_cache[sm_key] = sm_var
                        solver.add_clause_smart([-m_var_i, -m_var_j, sm_var])
                        solver.add_clause_smart([-sm_var, m_var_i])
                        solver.add_clause_smart([-sm_var, m_var_j])
                    sm_var_used = sm_cache[sm_key]

                # ── NEW: CSLB (Conditional Start Lower Bound) ──────────
                # Kích hoạt ngay khi xác định dùng chung máy, trước khi gán S
                if j_before_i:
                    # j trước i: i phải bắt đầu >= EST[j] + p_j
                    cslb_t = solver.est[j] + p_j
                    clause_cslb = [solver.get_x_bounded(i, cslb_t)]
                    if sm_var_used is not False: clause_cslb.append(-sm_var_used)
                    solver.add_clause_smart(clause_cslb)
                elif i_before_j:
                    # i trước j: j phải bắt đầu >= EST[i] + p_i
                    cslb_t = solver.est[i] + p_i
                    clause_cslb = [solver.get_x_bounded(j, cslb_t)]
                    if sm_var_used is not False: clause_cslb.append(-sm_var_used)
                    solver.add_clause_smart(clause_cslb)
                else:
                    # Không xác định thứ tự: disjunctive CSLB (3-literal)
                    x_i_lower = solver.get_x_bounded(i, solver.est[j] + p_j)
                    x_j_lower = solver.get_x_bounded(j, solver.est[i] + p_i)
                    clause_cslb = [x_i_lower, x_j_lower]
                    if sm_var_used is not False: clause_cslb.append(-sm_var_used)
                    solver.add_clause_smart(clause_cslb)

                # ── Chọn chiều và flag dựa trên forced ordering ──────────
                if j_before_i:
                    directions = [(i, j, p_i, p_j, False, True), (j, i, p_j, p_i, True, False)]
                elif i_before_j:
                    directions = [(i, j, p_i, p_j, True, False), (j, i, p_j, p_i, False, True)]
                else:
                    directions = [(i, j, p_i, p_j, False, False), (j, i, p_j, p_i, False, False)]

                # ── Sinh overlap clause theo từng chiều (Per-t) ───────────
                for (anchor, other, p_a, p_o, drop_left, drop_right) in directions:
                    est_o, lst_o = solver.est[other], solver.lst[other]

                    for t in range(solver.est[anchor], solver.lst[anchor] + 1):
                        t_left = t - p_o + 1
                        t_right = t + p_a

                        # Optimization 4: Tautology skip
                        if not drop_left and t_left > lst_o: continue
                        if not drop_right and t_right <= est_o: continue

                        # Build clause: [(-SM), -S_{anchor,t}, (¬X_left), (X_right)]
                        clause = [-solver.get_var('S', anchor, t)]
                        if sm_var_used is not False:
                            clause.append(-sm_var_used)

                        # Optimization 5: False-literal drop
                        if not drop_left and t_left > est_o:
                            clause.append(-solver.get_x_bounded(other, t_left))
                        if not drop_right and t_right <= lst_o:
                            clause.append(solver.get_x_bounded(other, t_right))

                        solver.add_clause_smart(clause)