from collections import defaultdict


def apply_mclb(solver):
    """
    Machine-Chain Lower Bound:
    Nếu A bị ép phải xong trước khi B có thể xong (dựa vào EST/LST),
    thì chuỗi A->B->C kẹp chung máy sẽ ép C phải bắt đầu >= EST_A + p_A + p_B.
    """
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            if (i, m) not in getattr(solver, 'killed_machines', set()):
                mach_to_ops[m].append((i, p))

    for mach, ops_on_m in mach_to_ops.items():
        n = len(ops_on_m)
        forced_succ = defaultdict(list)

        # Xây dựng DAG các cạnh bắt buộc
        for a in range(n):
            for b in range(n):
                if a == b: continue
                i, p_i = ops_on_m[a]
                j, p_j = ops_on_m[b]

                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue
                # i forced before j
                if solver.est[j] + p_j > solver.lst[i]:
                    forced_succ[i].append((j, p_i, p_j))

        # Tìm các chuỗi A -> B -> C
        for a_id, p_a in ops_on_m:
            for b_id, _, p_b_on_mach in forced_succ.get(a_id, []):
                for c_id, _, p_c_on_mach in forced_succ.get(b_id, []):
                    if c_id == a_id: continue
                    if solver.ops[a_id]['job_idx'] == solver.ops[c_id]['job_idx']: continue

                    cslb_t = solver.est[a_id] + p_a + p_b_on_mach

                    if cslb_t <= solver.est[c_id]:
                        continue  # Đã bị chặn bởi EST cơ bản

                    m_a = solver.get_var('M', a_id, mach)
                    m_b = solver.get_var('M', b_id, mach)
                    m_c = solver.get_var('M', c_id, mach)

                    if cslb_t + p_c_on_mach > solver.horizon:
                        # Capacity overflow ngay trên mệnh đề M
                        solver.add_clause_smart([-m_a, -m_b, -m_c])
                    else:
                        # Ràng buộc MCLB
                        x_cslb = solver.get_x_bounded(c_id, cslb_t)
                        solver.add_clause_smart([-m_a, -m_b, -m_c, x_cslb])