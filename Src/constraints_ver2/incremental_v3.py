from collections import defaultdict


def apply_incremental_v3(solver, new_limit):
    upper_bound = getattr(solver, 'current_check_limit', solver.horizon)
    if new_limit >= upper_bound:
        return

    if not hasattr(solver, 'killed_machines'):
        solver.killed_machines = set()
    if not hasattr(solver, '_incremental_excluded_pairs'):
        solver._incremental_excluded_pairs = set()

    # ── 1. CHAIN BLOCKING (Đòn đánh chí mạng mới) ────────────────────────
    for j_ids in solver.job_map:
        if not j_ids:
            continue
        n = len(j_ids)

        # Tính Suffix_min_p (thời gian tối thiểu còn lại của job từ k đến cuối)
        suffix = [0] * (n + 1)
        for k in range(n - 1, -1, -1):
            suffix[k] = suffix[k + 1] + solver.min_p[j_ids[k]]

        # Ép thời gian hoàn thành cho MỌI operation trong job
        for k in range(n):
            op_id = j_ids[k]
            # Op k bắt buộc phải XONG trước thời điểm: new_limit - suffix[k+1]
            latest_allowed_end = new_limit - suffix[k + 1]

            for mach, p in solver.ops[op_id]['machines']:
                if (op_id, mach) in solver.killed_machines:
                    continue

                m_var = solver.var_map.get(('M', op_id, mach))
                if m_var is None: continue

                t_start_blocked = latest_allowed_end - p + 1
                x_var = solver.get_x_bounded(op_id, t_start_blocked)
                solver.add_clause_smart([-m_var, solver.neg(x_var)])

    # ── 2. UNARY RE-EXCLUSION (Tương tự Model 10) ────────────────────────
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            if (i, m) in solver.killed_machines: continue

            wait_time = solver.horizon - solver.lst[i] - solver.min_p[i]
            if solver.est[i] + p + wait_time > new_limit:
                m_var = solver.var_map.get(('M', i, m))
                if m_var:
                    solver.add_clause_smart([-m_var])
                    solver.killed_machines.add((i, m))

    # ── 3. PAIRWISE RE-EXCLUSION (Tương tự Model 10) ─────────────────────
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            if (i, m) not in solver.killed_machines:
                mach_to_ops[m].append((i, p))

    for mach, ops_on_m in mach_to_ops.items():
        n_ops = len(ops_on_m)
        for a in range(n_ops):
            for b in range(a + 1, n_ops):
                i, p_i = ops_on_m[a]
                j, p_j = ops_on_m[b]

                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                pair_key = (min(i, j), max(i, j), mach)
                if pair_key in solver._incremental_excluded_pairs:
                    continue

                c_ij = max(solver.est[j], solver.est[i] + p_i) + p_j
                c_ji = max(solver.est[i], solver.est[j] + p_j) + p_i

                if min(c_ij, c_ji) > new_limit:
                    m_var_i, m_var_j = solver.var_map.get(('M', i, mach)), solver.var_map.get(('M', j, mach))
                    if m_var_i and m_var_j:
                        solver.add_clause_smart([-m_var_i, -m_var_j])
                        solver._incremental_excluded_pairs.add(pair_key)

    solver.current_check_limit = new_limit