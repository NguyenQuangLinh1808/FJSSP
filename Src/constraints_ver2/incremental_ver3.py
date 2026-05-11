from collections import defaultdict

def apply_incremental_ver2(solver, new_limit):
    upper_bound = getattr(solver, 'current_check_limit', solver.horizon)
    if new_limit >= upper_bound:
        return

    # ── 1. Block last op timing (Ép tiến độ) ────────────────────────
    for j_ids in solver.job_map:
        if not j_ids:
            continue
        last_op_id = j_ids[-1]
        for mach, p in solver.ops[last_op_id]['machines']:
            m_var = solver.var_map.get(('M', last_op_id, mach))
            if m_var is None:
                continue
            t_start_blocked = new_limit + 1 - p
            x_var = solver.get_x_bounded(last_op_id, t_start_blocked)
            solver.add_clause_smart([-m_var, solver.neg(x_var)])

    # ── 2. Machine-pair re-exclusion (Cắt tỉa sức chứa động) ───────
    # Khi Limit siết lại, các tổ hợp máy trước đây hợp lệ giờ trở thành bất khả thi.
    if not hasattr(solver, '_excl_pairs'):
        solver._excl_pairs = set()

    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            mach_to_ops[m].append((i, p))

    for mach, ops_on_m in mach_to_ops.items():
        n = len(ops_on_m)
        for a in range(n):
            for b in range(a + 1, n):
                i, p_i = ops_on_m[a]
                j, p_j = ops_on_m[b]

                # Bỏ qua nếu cùng Job (đã bị ràng buộc Precedence xử lý)
                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                key = (min(i, j), max(i, j), mach)
                if key in solver._excl_pairs:
                    continue  # Đã cắt từ Limit trước, bỏ qua để tiết kiệm CPU

                # Tính toán Kịch bản hoàn thành sớm nhất nếu dùng chung máy mach
                c_ij = max(solver.est[j], solver.est[i] + p_i) + p_j
                c_ji = max(solver.est[i], solver.est[j] + p_j) + p_i

                # Nếu kịch bản lý tưởng nhất vẫn lố Limit mới -> Tuyệt đối không thể chung máy
                if min(c_ij, c_ji) > new_limit:
                    m_var_i = solver.var_map.get(('M', i, mach))
                    m_var_j = solver.var_map.get(('M', j, mach))
                    if m_var_i and m_var_j:
                        solver.add_clause_smart([-m_var_i, -m_var_j])
                        solver._excl_pairs.add(key)

    solver.current_check_limit = new_limit