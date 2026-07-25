"""
_add_queries_v2.py -- Thêm 18 câu golden (q33..q50) nâng golden set 32 -> 50.
Bám đúng convention nhãn (relevant_grades 0/1/2 + full_relevant_ids + ground_truth_answer).
Tự VALIDATE mọi chunk_id với corpus trước khi ghi.
Chạy: .venv/Scripts/python.exe sample_model/golden/_add_queries_v2.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "golden" / "queries.json"
DOCS = ROOT / "index" / "docs.json"


def g(grades):  # helper: grades dict -> (grades, full_relevant_ids list)
    return grades, list(grades.keys())


NEW = []

def add(qid, qtype, query, grades, gt, **extra):
    gr, full = g(grades)
    obj = {"query_id": qid, "query_type": qtype, "query": query,
           "relevant_grades": gr, "full_relevant_ids": full,
           "ground_truth_answer": gt, "expect_fallback": qtype == "FALLBACK"}
    obj.update(extra)
    NEW.append(obj)


# ---------------- FACTUAL (+5) ----------------
add("q33", "FACTUAL",
    "Trong Vợ chồng A Phủ, Mị đã được giải thoát như thế nào?",
    {"vo_chong_a_phu_tomtat": 2, "vo_chong_a_phu_nhanvat": 1, "vo_chong_a_phu_chude": 1},
    "Mị từ thân phận con dâu gạt nợ bị đày đọa ở nhà thống lí Pá Tra đã cắt dây trói cứu A Phủ, rồi cùng A Phủ bỏ trốn khỏi Hồng Ngài, tự giải phóng và đi theo cách mạng.")

add("q34", "FACTUAL",
    "Nhân vật Xuân Tóc Đỏ trong Số đỏ là người như thế nào?",
    {"so_do_nhanvat": 2, "so_do_tomtat": 2, "so_do_noidung": 1, "so_do_chude": 1},
    "Xuân Tóc Đỏ vốn là kẻ lưu manh, hạ lưu, nhờ gặp thời và xã hội 'Âu hóa' lố lăng mà leo lên thành 'nhà cải cách', 'anh hùng cứu quốc' — qua đó Vũ Trọng Phụng châm biếm sự giả dối của xã hội thượng lưu thành thị.")

add("q35", "FACTUAL",
    "Chiếc lược ngà trong truyện cùng tên có ý nghĩa gì?",
    {"chiec_luoc_nga_tomtat": 2, "chiec_luoc_nga_chude": 2, "chiec_luoc_nga_nhanvat": 1},
    "Chiếc lược ngà là kỷ vật ông Sáu tự tay làm cho con gái bé Thu nơi chiến trường; nó là biểu tượng cho tình cha con sâu nặng và thiêng liêng không thể bị chiến tranh hủy diệt.")

add("q36", "FACTUAL",
    "Bài thơ Tây Tiến viết về đoàn quân nào và trong hoàn cảnh ra sao?",
    {"tay_tien_tomtat": 2, "tay_tien_boicanh": 2, "tay_tien_chude": 1},
    "Tây Tiến của Quang Dũng viết về đoàn binh Tây Tiến — những người lính chủ yếu là thanh niên Hà Nội hành quân, chiến đấu ở vùng núi rừng miền Tây Bắc Bộ và Lào trong kháng chiến chống Pháp, khắc họa vẻ hào hùng mà bi tráng, lãng mạn.")

add("q37", "FACTUAL",
    "Huấn Cao trong Chữ người tử tù là người như thế nào?",
    {"chu_nguoi_tu_tu_nhanvat": 2, "chu_nguoi_tu_tu_tomtat": 2, "chu_nguoi_tu_tu_chude": 1},
    "Huấn Cao là người tử tù có tài viết chữ đẹp và khí phách hiên ngang, 'thiên lương' trong sáng; dù bị giam cầm vẫn giữ cốt cách, cuối cùng cho chữ viên quản ngục để đáp lại tấm lòng biệt nhỡn liên tài.")

# ---------------- AUTHOR (+4) ----------------
add("q38", "AUTHOR",
    "Vũ Trọng Phụng có những tác phẩm nào trong thư viện?",
    {"so_do_tomtat": 2, "giong_to_tomtat": 2,
     "so_do_nhanvat": 1, "so_do_chude": 1, "so_do_noidung": 1,
     "giong_to_nhanvat": 1, "giong_to_chude": 1},
    "Trong thư viện, Vũ Trọng Phụng có hai tác phẩm: Số đỏ và Giông tố — đều là những sáng tác hiện thực trào phúng phê phán xã hội thành thị trước Cách mạng.",
    stability_group="vu_trong_phung_works")

add("q39", "AUTHOR",
    "Kim Lân viết những truyện nào trong thư viện?",
    {"vo_nhat_tomtat": 2, "lang_kim_lan_tomtat": 2, "vo_nhat_tacgia": 2,
     "vo_nhat_nhanvat": 1, "vo_nhat_chude": 1,
     "lang_kim_lan_nhanvat": 1, "lang_kim_lan_chude": 1},
    "Kim Lân có hai truyện ngắn trong thư viện: Vợ nhặt và Làng — đều viết về người nông dân Việt Nam, tình người trong nạn đói và lòng yêu làng, yêu nước.")

add("q40", "AUTHOR",
    "Huy Cận có những bài thơ nào trong thư viện?",
    {"trang_giang_tomtat": 2, "doan_thuyen_danh_ca_tomtat": 2,
     "trang_giang_chude": 1, "doan_thuyen_danh_ca_chude": 1},
    "Huy Cận có hai bài thơ trong thư viện: Tràng giang — nỗi buồn cô đơn của cái tôi trước thiên nhiên rộng lớn, và Đoàn thuyền đánh cá — khúc ca lao động tươi vui của con người làm chủ biển khơi.")

add("q41", "AUTHOR",
    "Trong thư viện có những cuốn nào do Vũ Trọng Phụng viết?",
    {"so_do_tomtat": 2, "giong_to_tomtat": 2,
     "so_do_nhanvat": 1, "so_do_chude": 1, "so_do_noidung": 1,
     "giong_to_nhanvat": 1, "giong_to_chude": 1},
    "Vũ Trọng Phụng có hai tác phẩm trong thư viện là Số đỏ và Giông tố.",
    stability_group="vu_trong_phung_works")

# ---------------- SEMANTIC (+4) ----------------
add("q42", "SEMANTIC",
    "Bài thơ nào viết về người lính và tình đồng đội trong kháng chiến?",
    {"dong_chi_tomtat": 2, "dong_chi_chude": 2, "tay_tien_tomtat": 2,
     "tay_tien_chude": 1, "xe_khong_kinh_chude": 1},
    "Tiêu biểu có Đồng chí của Chính Hữu — tình đồng đội keo sơn của người lính nông dân, và Tây Tiến của Quang Dũng — vẻ hào hùng bi tráng của đoàn binh Tây Tiến; ngoài ra Bài thơ về tiểu đội xe không kính của Phạm Tiến Duật cũng ca ngợi người lính lái xe Trường Sơn.")

add("q43", "SEMANTIC",
    "Tác phẩm nào ca ngợi vẻ đẹp lao động và thiên nhiên vùng biển?",
    {"doan_thuyen_danh_ca_tomtat": 2, "doan_thuyen_danh_ca_chude": 2,
     "doan_thuyen_danh_ca_boicanh": 1, "que_huong_te_hanh_chude": 1,
     "que_huong_te_hanh_tomtat": 1},
    "Đoàn thuyền đánh cá của Huy Cận ca ngợi khí thế lao động hăng say và vẻ đẹp tráng lệ của biển khơi; bài Quê hương của Tế Hanh cũng khắc họa vẻ đẹp của làng chài và người dân miền biển.")

add("q44", "SEMANTIC",
    "Truyện nào viết về tình cha con sâu nặng?",
    {"chiec_luoc_nga_tomtat": 2, "chiec_luoc_nga_chude": 2,
     "chiec_luoc_nga_nhanvat": 1, "lao_hac_chude": 1},
    "Chiếc lược ngà của Nguyễn Quang Sáng là tác phẩm tiêu biểu về tình cha con thắm thiết giữa ông Sáu và bé Thu trong chiến tranh; ngoài ra tình phụ tử cũng thể hiện qua Lão Hạc của Nam Cao khi lão hi sinh tất cả vì con.")

add("q45", "SEMANTIC",
    "Có tác phẩm thiếu nhi nào viết về thế giới loài vật không?",
    {"de_men_tomtat": 2, "de_men_nhanvat": 2, "de_men_chude": 1},
    "Dế Mèn phiêu lưu ký của Tô Hoài là tác phẩm thiếu nhi tiêu biểu viết về thế giới loài vật: qua cuộc phiêu lưu của chú Dế Mèn, tác giả gửi gắm bài học về lòng dũng cảm, tình bạn và khát vọng sống đẹp.")

# ---------------- MULTI_TURN (+3) ----------------
add("q46", "MULTI_TURN",
    "Cuốn Số đỏ ấy châm biếm điều gì?",
    {"so_do_chude": 2, "so_do_noidung": 2, "so_do_tomtat": 1},
    "Số đỏ của Vũ Trọng Phụng châm biếm sâu cay xã hội thượng lưu thành thị 'Âu hóa' lố lăng, giả dối trước Cách mạng, qua bước đường thăng tiến nực cười của Xuân Tóc Đỏ.",
    history=[{"role": "user", "content": "Vũ Trọng Phụng có những tác phẩm nào trong thư viện?"},
             {"role": "assistant", "content": "Vũ Trọng Phụng có hai tác phẩm: Số đỏ và Giông tố. Bạn muốn tìm hiểu cuốn nào?"}])

add("q47", "MULTI_TURN",
    "Bài thơ đó do ai sáng tác và viết về đoàn quân nào?",
    {"tay_tien_tomtat": 2, "tay_tien_boicanh": 2},
    "Bài thơ Tây Tiến do Quang Dũng sáng tác, viết về đoàn binh Tây Tiến hoạt động ở vùng núi rừng miền Tây trong kháng chiến chống Pháp.",
    history=[{"role": "user", "content": "Gợi ý một bài thơ hào hùng về người lính trong kháng chiến chống Pháp"},
             {"role": "assistant", "content": "Tiêu biểu là Tây Tiến của Quang Dũng — khắc họa đoàn binh Tây Tiến vừa bi tráng vừa lãng mạn. Bạn muốn biết thêm gì về bài thơ này?"}])

add("q48", "MULTI_TURN",
    "Cuốn Tôi thấy hoa vàng trên cỏ xanh của nhà văn ấy kể về điều gì?",
    {"hoa_vang_co_xanh_tomtat": 2, "hoa_vang_co_xanh_chude": 1},
    "Tôi thấy hoa vàng trên cỏ xanh của Nguyễn Nhật Ánh kể về tuổi thơ nơi làng quê nghèo miền Trung, xoay quanh hai anh em Thiều và Tường cùng những rung động trong trẻo đầu đời và bài học về tình thân, lòng vị tha.",
    history=[{"role": "user", "content": "Nguyễn Nhật Ánh có những tác phẩm nào trong thư viện?"},
             {"role": "assistant", "content": "Nguyễn Nhật Ánh có Mắt biếc và Tôi thấy hoa vàng trên cỏ xanh. Bạn muốn tìm hiểu cuốn nào?"}])

# ---------------- FALLBACK (+2) ----------------
add("q49", "FALLBACK",
    "Tóm tắt tiểu thuyết Trăm năm cô đơn của Gabriel García Márquez",
    {},
    "Hệ thống từ chối lịch sự vì đây là tác phẩm văn học nước ngoài không có trong thư viện, không bịa nội dung.")

add("q50", "FALLBACK",
    "Công thức tính diện tích hình tròn là gì?",
    {},
    "Hệ thống từ chối lịch sự vì câu hỏi nằm ngoài phạm vi văn học Việt Nam của thư viện.")


# ---------------- validate + ghi ----------------
def main():
    docs = json.load(open(DOCS, encoding="utf-8"))
    valid = {d["chunk_id"] for d in docs}
    data = json.load(open(GOLDEN, encoding="utf-8"))
    existing_ids = {q["query_id"] for q in data["queries"]}

    errors = []
    for q in NEW:
        if q["query_id"] in existing_ids:
            errors.append(f"{q['query_id']}: TRÙNG id")
        for cid in q["full_relevant_ids"]:
            if cid not in valid:
                errors.append(f"{q['query_id']}: chunk_id không tồn tại -> {cid}")
    if errors:
        print("❌ LỖI validate:")
        for e in errors:
            print("  ", e)
        raise SystemExit(1)

    data["queries"].extend(NEW)
    json.dump(data, open(GOLDEN, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    c = Counter(q["query_type"] for q in data["queries"])
    print(f"✅ Đã thêm {len(NEW)} câu. Tổng golden = {len(data['queries'])}.")
    print("Phân bố:", dict(c))


if __name__ == "__main__":
    main()
