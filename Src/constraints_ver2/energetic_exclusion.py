def apply_energetic_exclusion(solver):
    """
    Tiền xử lý (Pre-processing): Chặn các tùy chọn máy không khả thi về mặt năng lực.
    Nếu tổng thời gian của các operation BẮT BUỘC phải chạy trên máy M
    cộng với thời gian của một operation TÙY CHỌN vượt quá Horizon
    -> Operation tùy chọn đó không thể chạy trên máy M.
    """
    # 1. Tính tổng tải bắt buộc trên từng máy
    mandatory_load = [0] * solver.num_machines
    for i in range(solver.num_ops):
        mach_list = solver.ops[i]['machines']
        if len(mach_list) == 1:
            m, p = mach_list[0]
            mandatory_load[m] += p

    # 2. Sinh Unit Clause loại bỏ các tùy chọn quá tải
    for i in range(solver.num_ops):
        mach_list = solver.ops[i]['machines']
        if len(mach_list) == 1:
            continue  # Op này là mandatory, bỏ qua

        for m, p in mach_list:
            if mandatory_load[m] + p > solver.horizon:
                m_var = solver.get_var('M', i, m)
                solver.add_clause_smart([-m_var])  # Unit clause: Chém đứt nhánh này ngay từ đầu