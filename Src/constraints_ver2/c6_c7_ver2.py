from collections import defaultdict

def apply_c6_c7_ver2(solver):
    """
    Constraint 8 (Pure FJSSP): Chống Overlap trên cùng 1 máy.
    Công thức: M_{i,k} & M_{j,k} & S_{i,t} -> ~X_{j, t1+1} V X_{j, t2}
    với t1 = t - p_j (thời điểm muộn nhất j có thể bắt đầu trước i)
    và  t2 = t + p_i (thời điểm sớm nhất j có thể bắt đầu sau i)
    """
    # Gom nhóm các operation có thể chạy trên cùng một máy
    mach_to_ops = defaultdict(list)
    for i in range(solver.num_ops):
        for m, p in solver.ops[i]['machines']:
            mach_to_ops[m].append((i, p))

    for mach, ops_on_m in mach_to_ops.items():
        n_ops = len(ops_on_m)

        # Quét mọi cặp thao tác (i, j) có khả năng tranh chấp máy mach
        for idx1 in range(n_ops):
            for idx2 in range(idx1 + 1, n_ops):
                i, p_i = ops_on_m[idx1]
                j, p_j = ops_on_m[idx2]

                # Bỏ qua nếu i và j thuộc cùng một Job 
                # (Sự chồng chéo đã bị loại trừ tuyệt đối bởi ràng buộc Precedence C4)
                if solver.ops[i]['job_idx'] == solver.ops[j]['job_idx']:
                    continue

                m_var_i = solver.get_var('M', i, mach)
                m_var_j = solver.get_var('M', j, mach)

                # 1. Trường hợp thao tác i chạy trước, j chạy sau hoặc chạy trước đó hẳn
                for t in range(solver.est[i], solver.lst[i] + 1):
                    s_i_t = solver.get_var('S', i, t)

                    t1 = t - p_j
                    t2 = t + p_i

                    # Rút biến X an toàn nhờ cơ chế get_x_bounded
                    x_j_left = solver.get_x_bounded(j, t1 + 1)
                    x_j_right = solver.get_x_bounded(j, t2)

                    # Ép CNF: ~M_i V ~M_j V ~S_{i,t} V ~X_{j, t1+1} V X_{j, t2}
                    solver.add_clause_smart([
                        solver.neg(m_var_i),
                        solver.neg(m_var_j),
                        solver.neg(s_i_t),
                        solver.neg(x_j_left),
                        x_j_right
                    ])

                # 2. Trường hợp thao tác j chạy tại thời điểm t, i chạy sau hoặc chạy trước (Tính đối xứng)
                for t in range(solver.est[j], solver.lst[j] + 1):
                    s_j_t = solver.get_var('S', j, t)

                    t1 = t - p_i
                    t2 = t + p_j

                    x_i_left = solver.get_x_bounded(i, t1 + 1)
                    x_i_right = solver.get_x_bounded(i, t2)

                    # Ép CNF: ~M_j V ~M_i V ~S_{j,t} V ~X_{i, t1+1} V X_{i, t2}
                    solver.add_clause_smart([
                        solver.neg(m_var_j),
                        solver.neg(m_var_i),
                        solver.neg(s_j_t),
                        solver.neg(x_i_left),
                        x_i_right
                    ])