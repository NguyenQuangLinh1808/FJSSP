from collections import defaultdict


def apply_incremental_v3(solver, new_limit):
    upper_bound = getattr(solver, 'current_check_limit', solver.horizon)
    if new_limit >= upper_bound:
        return

    if not hasattr(solver, 'killed_machines'):
        solver.killed_machines = set()
    if not hasattr(solver, '_incremental_excluded_pairs'):
        solver._incremental_excluded_pairs = set()

    # ── 1. CHAIN BLOCKING (Ép tiến độ toàn chuỗi) ────────────────────────
    for j_ids in solver.job_map:
        if not j_ids:
            continue
        n = len(j_ids)

        # suffix[k] = Tổng min_p từ vị trí k đến cuối job
        suffix = [0] * (n + 1)
        for k in range(n - 1, -1, -1):
            suffix[k] = suffix[k + 1] + solver.min_p[j_ids[k]]

        for k in range(n):
            op_id = j_ids[k]
            # Op k bắt buộc phải hoàn thành trước: new_limit - suffix[k+1]
            latest_allowed_end = new_limit - suffix[k + 1]

            for mach, p in solver.ops[op_id]['machines']:
                if (op_id, mach) in solver.killed_machines:
                    continue

                m_var = solver.var_map.get(('M', op_id, mach))
                if m_var is None:
                    continue

                t_start_blocked = latest_allowed_end - p + 1
                x_var = solver.get_x_bounded(op_id, t_start_blocked)
                solver.add_clause_smart([-m_var, solver.neg(x_var)])

    # ── 2. UNARY RE-EXCLUSION (Cắt tỉa từng máy) ────────────────────────
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            if (i, m) in solver.killed_machines:
                continue

            wait_time = solver.horizon - solver.lst[i] - solver.min_p[i]
            if solver.est[i] + p + wait_time > new_limit:
                m_var = solver.var_map.get(('M', i, m))
                if m_var:
                    solver.add_clause_smart([-m_var])
                    solver.killed_machines.add((i, m))

    # ── 3. PAIRWISE RE-EXCLUSION (Cắt tỉa theo cặp với Cache động) ───────
    if not hasattr(solver, '_mach_pair_cache'):
        # Build cache một lần duy nhất
        solver._mach_pair_cache = {}
        mach_to_ops = defaultdict(list)
        for i in range(solver.num_ops):
            for m, p in solver.ops[i]['machines']:
                mach_to_ops[m].append((i, p))

        for mach, ops_on_m in mach_to_ops.items():
            n_ops = len(ops_on_m)
            for a in range(n_ops):
                for b in range(a + 1, n_ops):
                    i, p_i = ops_on_m[a]
                    j, p_j = ops_on_m[b]

                    if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                        continue

                    c_ij = max(solver.est[j], solver.est[i] + p_i) + p_j
                    c_ji = max(solver.est[i], solver.est[j] + p_j) + p_i

                    key = (min(i, j), max(i, j), mach)
                    # Lưu kèm i, j, mach để check dead-state sau này
                    solver._mach_pair_cache[key] = (
                        min(c_ij, c_ji),
                        i, j, mach,
                        solver.var_map.get(('M', i, mach)),
                        solver.var_map.get(('M', j, mach))
                    )

    # Tiêu thụ Cache
    for key, data in solver._mach_pair_cache.items():
        if key in solver._incremental_excluded_pairs:
            continue

        min_comp, i, j, mach, m_var_i, m_var_j = data

        # DEAD-CHECK: Không xử lý nếu 1 trong 2 máy đã chết từ Unary Re-exclusion
        if (i, mach) in solver.killed_machines or (j, mach) in solver.killed_machines:
            continue

        if min_comp > new_limit and m_var_i and m_var_j:
            solver.add_clause_smart([-m_var_i, -m_var_j])
            solver._incremental_excluded_pairs.add(key)

    solver.current_check_limit = new_limit