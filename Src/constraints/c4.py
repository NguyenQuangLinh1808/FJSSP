def apply_c4(solver):
    # Constraint 4: Ràng buộc hoàn thành (Precedence)
    for j_ids in solver.job_map:
        for k in range(len(j_ids)):
            i = j_ids[k]
            is_last_op = (k == len(j_ids) - 1)
            next_i = j_ids[k + 1] if not is_last_op else None

            min_p = solver.min_p[i]

            # --- TỐI ƯU HÓA: Base case (Máy nhanh nhất) ---
            # S[i,t] -> X[next_i, t + min_p] (Không kẹp biến M)
            if not is_last_op:
                for t in range(solver.est[i], solver.lst[i] + 1):
                    finish_min = t + min_p
                    x_next_target = solver.get_x_bounded(next_i, finish_min)
                    solver.add_clause_smart([-solver.get_var('S', i, t), x_next_target])

            # --- TỐI ƯU HÓA: Differential case (Xử lý phần chênh cho các máy chậm hơn) ---
            for mach, p in solver.ops[i]['machines']:
                m_var = solver.get_var('M', i, mach)

                # Tính giới hạn t cực đại NẾU chạy trên máy này
                max_start_m = solver.lst[i] + min_p - p

                # Máy quá chậm, cấm chọn
                if max_start_m < solver.est[i]:
                    solver.add_clause_smart([-m_var])
                    continue

                # Nếu thời gian chạy dài hơn máy nhanh nhất, ép giới hạn thực tế tại điểm t+p
                # Tính chất tích lũy của X sẽ tự động lo phần từ t+min_p đến t+p-1
                if not is_last_op and p > min_p:
                    for t in range(solver.est[i], max_start_m + 1):
                        finish = t + p
                        x_next_target = solver.get_x_bounded(next_i, finish)
                        solver.add_clause_smart([-m_var, -solver.get_var('S', i, t), x_next_target])

                # Cấm ghép máy chậm với thời điểm bắt đầu trễ
                for t in range(max_start_m + 1, solver.lst[i] + 1):
                    solver.add_clause_smart([-m_var, -solver.get_var('S', i, t)])