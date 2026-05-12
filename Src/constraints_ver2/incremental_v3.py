from collections import defaultdict
from constraints_ver2.mvcc import apply_mvcc


def apply_incremental_v3(solver, new_limit):
    upper_bound = getattr(solver, 'current_check_limit', solver.horizon)
    if new_limit >= upper_bound:
        return

    if not hasattr(solver, 'killed_machines'):
        solver.killed_machines = set()
    if not hasattr(solver, '_incremental_excluded_pairs'):
        solver._incremental_excluded_pairs = set()

    # ── 1. TÍNH TOÁN LST ẢO (Dynamic LST) & ÉP TIẾN ĐỘ CHAIN BLOCKING ────
    dynamic_lst = [0] * solver.num_ops
    for j_ids in solver.job_map:
        t_budget = new_limit
        for op_id in reversed(j_ids):
            t_budget -= solver.min_p[op_id]
            dynamic_lst[op_id] = t_budget

            # Chain Blocking: Ép tiến độ thông qua biến X
            for mach, p in solver.ops[op_id]['machines']:
                if (op_id, mach) in solver.killed_machines:
                    continue
                m_var = solver.var_map.get(('M', op_id, mach))
                if m_var:
                    # t_blocked = Earliest thời điểm thao tác bị cấm bắt đầu
                    t_blocked = t_budget + solver.min_p[op_id] - p + 1
                    x_var = solver.get_x_bounded(op_id, t_blocked)
                    solver.add_clause_smart([-m_var, solver.neg(x_var)])

    # ── 2. GỌI LẠI MVCC VỚI LST MỚI (Tái kích hoạt Xung đột Năng lượng) ────
    # Khi LST bị siết, Năng lượng bắt buộc tăng vọt. Mệnh đề [-M_A, -M_B, -M_C] sẽ nổ ra.
    apply_mvcc(solver, dynamic_lst=dynamic_lst)

    # ── 3. UNARY RE-EXCLUSION (Cắt tỉa từng máy) ───────────────────────────
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

    # ── 4. PAIRWISE RE-EXCLUSION (Dùng Cache O(1) + Dead Check) ────────────
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