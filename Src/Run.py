import os
import sys
from runner import run_benchmark_tests


def get_latest_result_directory(results_base_path):
    if not os.path.exists(results_base_path):
        return None
    subdirs = [d for d in os.listdir(results_base_path) if os.path.isdir(os.path.join(results_base_path, d))]
    if not subdirs:
        return None
    return max(subdirs, key=lambda d: os.path.getmtime(os.path.join(results_base_path, d)))


if __name__ == "__main__":
    current_src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_src_dir)

    # 1. QUÉT DATASET CẤP 1
    ignore_dirs = {'.venv', 'LB_UB', 'Results', 'Src', 'Log', '.git', '__pycache__', '.idea', 'archive'}
    available_datasets = sorted([
        d for d in os.listdir(project_root)
        if os.path.isdir(os.path.join(project_root, d)) and d not in ignore_dirs
    ])

    if not available_datasets:
        print(">>> Lỗi nghiêm trọng: Không tìm thấy thư mục dataset nào.")
        sys.exit(1)

    print("========================================")
    print("DANH SÁCH BỘ DỮ LIỆU (DATASET GỐC):")
    for idx, ds in enumerate(available_datasets, 1):
        print(f"{idx}. {ds}")
    print("========================================")

    try:
        ds_input = input("Chọn bộ test (nhập 1 số hoặc nhiều số cách nhau dấu cách, vd: 1 2 4): ").strip()
        selected_indices = [int(x) for x in ds_input.split()]
        if any(idx < 1 or idx > len(available_datasets) for idx in selected_indices):
            raise ValueError
        selected_base_datasets = [available_datasets[idx - 1] for idx in selected_indices]
    except ValueError:
        print(">>> Lỗi: Lựa chọn không hợp lệ. Thoát hệ thống.")
        sys.exit(1)

    datasets_to_run = []

    # 2. KIỂM TRA PHÂN NHÁNH (CHỈ KÍCH HOẠT KHI CHỌN 1 DATASET CHÍNH XÁC)
    if len(selected_base_datasets) == 1:
        base_dataset_name = selected_base_datasets[0]
        base_dataset_path = os.path.join(project_root, base_dataset_name)
        subdirs = sorted([
            d for d in os.listdir(base_dataset_path)
            if os.path.isdir(os.path.join(base_dataset_path, d))
        ])

        dataset_rel_path = base_dataset_name
        if subdirs:
            print(f"\nBộ test [{base_dataset_name}] có chứa các nhánh con. CHỌN NHÁNH:")
            for idx, sub in enumerate(subdirs, 1):
                print(f"{idx}. {sub}")
            try:
                sub_choice = int(input(f"Chọn nhánh (1-{len(subdirs)}): ").strip())
                if sub_choice < 1 or sub_choice > len(subdirs):
                    raise ValueError
                dataset_rel_path = os.path.join(base_dataset_name, subdirs[sub_choice - 1])
            except ValueError:
                print(">>> Lỗi: Lựa chọn không hợp lệ. Thoát hệ thống.")
                sys.exit(1)
        datasets_to_run.append(dataset_rel_path)
    else:
        # User chọn chạy multi-dataset, bỏ qua nhánh con để đảm bảo luồng chạy tự động
        datasets_to_run = selected_base_datasets

    # 3. LỰA CHỌN CHẾ ĐỘ CHẠY & KHAI BÁO TÊN THƯ MỤC
    print("\n========================================")
    print("CHỌN CHẾ ĐỘ CHẠY MODEL:")
    print("1. Chạy ĐƠN")
    print("2. Chạy ĐA ")
    print("========================================")

    mode_choice = input("Lựa chọn chế độ (1 hoặc 2): ").strip()

    models_to_run = []
    run_folders = []

    if mode_choice == '1':
        try:
            m_choice = int(input("Nhập số thứ tự mô hình: ").strip())
            models_to_run.append(m_choice)
        except ValueError:
            print(">>> Lỗi: Vui lòng nhập số hợp lệ.")
            sys.exit(1)

        run_name_input = input("\nNhập tên THƯ MỤC kết quả (Để trống lấy thư mục mới nhất/default_run): ").strip()
        if not run_name_input:
            # Lấy dataset đầu tiên làm mốc dò tìm thư mục mới nhất
            results_base = os.path.join(project_root, 'Results', datasets_to_run[0])
            latest = get_latest_result_directory(results_base)
            run_folders.append(latest if latest else "default_run")
        else:
            run_folders.append(run_name_input)

    elif mode_choice == '2':
        try:
            m_input = input("Nhập các số thứ tự model muốn chạy (cách nhau bởi dấu cách, vd: 1 3 4): ").strip()
            models_to_run = [int(x) for x in m_input.split()]
        except ValueError:
            print(">>> Lỗi: Định dạng model không hợp lệ.")
            sys.exit(1)

        names_input = input("\nNhập tên THƯ MỤC KẾT QUẢ tương ứng (vd: x y z) hoặc Enter để dùng mặc định: ").strip()
        names_list = names_input.split()

        for i, m in enumerate(models_to_run):
            if i < len(names_list):
                run_folders.append(names_list[i])
            else:
                run_folders.append(f"model_{m}")
    else:
        print(">>> Lỗi: Lựa chọn không hợp lệ.")
        sys.exit(1)

    # 4. CHỌN TESTCASE
    print(f"\nChế độ chạy cho các bộ mục tiêu: {datasets_to_run}")
    print("1. Chạy TẤT CẢ các file")
    print("2. Chạy các file CỤ THỂ (nhập số thứ tự file)")

    choice = input("Nhập lựa chọn (1 hoặc 2): ").strip()

    selected_tests = None
    if choice == '2':
        try:
            tests_input = input("Nhập các số thứ tự file muốn chạy (cách nhau bởi dấu cách, vd: 1 3 6): ").strip()
            selected_tests = [int(x) for x in tests_input.split()]
        except ValueError:
            print(">>> Lỗi: Định dạng không hợp lệ.")
            sys.exit(1)

    # 5. THỰC THI CHUỖI BENCHMARK
    for dataset_rel_path in datasets_to_run:
        print(f"\n" + "*" * 80)
        print(f"BẮT ĐẦU CHẠY BENCHMARK CHO DATASET: [{dataset_rel_path}]")
        print("*" * 80)

        for idx, model_choice in enumerate(models_to_run):
            run_name = run_folders[idx]
            print(f"\n" + "=" * 70)
            print(f"CHẠY CHUỖI TEST - MODEL: {model_choice} | DATASET: {dataset_rel_path} | FOLDER: {run_name}")
            print("=" * 70)

            run_benchmark_tests(
                base_dir=current_src_dir,
                dataset_rel_path=dataset_rel_path,
                test_indices=selected_tests,
                run_name=run_name,
                model_choice=model_choice
            )