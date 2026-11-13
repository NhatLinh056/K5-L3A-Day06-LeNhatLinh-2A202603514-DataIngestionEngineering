# Nhật ký chạy — 2026-11-13

- `python scripts/check_setup.py`: PostgreSQL 16.16, pgvector 0.8.7, `Setup OK`.
- `python -m scripts.check_corpus`: 61 chương hợp lệ, 20 câu benchmark; tất cả quote gold tìm thấy ở đúng chương.
- `python -m src.run`: chạy A/B/C với model embedding local 384 chiều, lưu 60 trace top-3 và `summary.json`.
- Chạy `python -m src.run` lần hai: số chunk trong PostgreSQL vẫn là A 971, B 1095, C 1095. Không nhân đôi.
- Kiểm tra 45 chunk test: URL nguồn, chương, metadata và text khớp văn bản sạch 45/45.
- Không gặp lỗi trích text, embedding, lưu vector hoặc truy xuất trong hai lần chạy. Kết quả thấp ở q19/q20 là lỗi truy xuất, đã phân tích trong báo cáo.
- Model tải lần đầu qua mạng; cache và database local không nằm trong repo. Raw text và các chương được tạo lại theo README.
