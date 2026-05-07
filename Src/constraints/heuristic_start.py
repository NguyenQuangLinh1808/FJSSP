def apply_heuristic_start(solver):
    num_jobs = len(solver.job_map)

    # Chỉ áp dụng Heuristic khi số lượng job <= số lượng machine
    if num_jobs > solver.num_machines:
        return

    for job_ids in solver.job_map:
        if not job_ids:
            continue

        op1_id = job_ids[0]

        # 1. Ép task 1 bắt đầu tại t=0 (Mapping với "S1 i, 1 = 1" của bạn)
        s_op1 = solver.get_var('S', op1_id, 0)
        solver.add_clause_smart([s_op1])  # Bơm Unit Clause: Ép True tuyệt đối

        if len(job_ids) >= 2:
            op2_id = job_ids[1]
            p1_min = solver.min_p[op1_id]

            # Tìm máy gia công task 1 có thời gian bằng đúng p1_min
            best_mach = -1
            for mach, p in solver.ops[op1_id]['machines']:
                if p == p1_min:
                    best_mach = mach
                    break

            if best_mach != -1:
                # 2. KHÓA CHẾT MÁY: Ép task 1 phải chạy trên máy nhanh nhất.
                # Nếu không có dòng này, solver chọn máy chậm hơn sẽ gây vỡ model.
                m_op1 = solver.get_var('M', op1_id, best_mach)
                solver.add_clause_smart([m_op1])

                # 3. Ép task 2 bắt đầu ngay lập tức khi task 1 vừa xong
                # Mapping với "task 2: Xm 2, p1_min"
                s_op2 = solver.get_var('S', op2_id, p1_min)
                solver.add_clause_smart([s_op2])