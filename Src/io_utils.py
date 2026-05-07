# import os
# import json
#
# def save_result_to_file(filepath, result_data):
#     with open(filepath, 'w', encoding='utf-8') as f:
#         json.dump(result_data, f, indent=4)
#
# def load_result_from_file(filepath):
#     if not os.path.exists(filepath): return None
#     try:
#         with open(filepath, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except Exception:
#         return None
#
# def parse_brandimarte_file(file_path):
#     with open(file_path, 'r') as f:
#         content = f.read().strip().split('\n')
#     first = content[0].split()
#     if not first: return [], 0
#     jobs = []
#     for line in content[1:]:
#         if not line.strip(): continue
#         tok = list(map(int, line.split()))
#         idx = 1
#         job = []
#         for _ in range(tok[0]):
#             nalt = tok[idx]
#             idx += 1
#             alts = []
#             for _ in range(nalt):
#                 alts.append((tok[idx], tok[idx + 1]))
#                 idx += 2
#             job.append(alts)
#         jobs.append(job)
#     return jobs, int(first[1])

import os
import json

def save_result_to_file(filepath, result_data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=4)

def load_result_from_file(filepath):
    if not os.path.exists(filepath): return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def parse_fjssp_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read().strip().split('\n')
    first = content[0].split()
    if not first: return [], 0
    jobs = []
    for line in content[1:]:
        if not line.strip(): continue
        tok = list(map(int, line.split()))
        idx = 1
        job = []
        for _ in range(tok[0]):
            nalt = tok[idx]
            idx += 1
            alts = []
            for _ in range(nalt):
                alts.append((tok[idx], tok[idx + 1]))
                idx += 2
            job.append(alts)
        jobs.append(job)
    return jobs, int(first[1])