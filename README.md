# Day 06 · Data Ingestion Engineering

**Lab cá nhân** · **4 giờ** · **Dữ liệu tự chọn**

Biến tài liệu thành kho tri thức có thể truy xuất cho AI agent, rồi đo xem cách chuẩn bị dữ liệu nào hiệu quả nhất.

| 📄 Dữ liệu | 🧩 Chiến lược | 🎯 Benchmark |
|---|---|---|
| Tối thiểu **30 trang nội dung** | Tối thiểu **3 cấu hình** | Tối thiểu **20 câu hỏi** |

## Bắt đầu nhanh

Dùng [starter PostgreSQL + pgvector](starter/README.md) để dựng database và hoàn thiện các hàm TODO, hoặc tự chọn vector store tương đương. Starter chỉ là khung: **bạn tự hiện thực pipeline và benchmark**.

## 1. Xây pipeline

![Đọc tài liệu, chuẩn hóa, chia chunk, tạo vector, lưu và kiểm tra](assets/ingestion-pipeline.svg)

Chọn tài liệu được phép sử dụng; giữ **ID tài liệu, nguồn, trang/vị trí** và metadata phù hợp. Dùng embedding model thật qua API hoặc chạy local; lưu và truy xuất bằng pgvector, Qdrant, Chroma hoặc một store tương đương.

## 2. So sánh và đánh giá

![Ba chiến lược được đánh giá trên cùng corpus và benchmark dev/test](assets/benchmark-workflow.svg)

Dùng cùng dữ liệu, model và câu hỏi cho cả ba cấu hình. Tách **15 câu dev / 5 câu test** trước khi chạy; chọn cấu hình trên dev, rồi đánh giá test sau khi cố định. Mỗi câu hỏi cần có đoạn bằng chứng và trang nguồn; thiết kế bộ câu hỏi và đánh giá theo [BENCHMARK.md](BENCHMARK.md).

Đánh giá theo năm khía cạnh: **độ chính xác truy xuất**, **tính mạch lạc của chunk**, **tính hữu dụng của metadata**, **chất lượng grounding** và **tác động của chiến lược dữ liệu**. Giải thích lựa chọn bằng kết quả, ví dụ lỗi và các đánh đổi.

## 3. Chuẩn bị bài nộp

1. Chạy pipeline và lưu cấu hình, kết quả top-3, trace cùng nhãn đánh giá thủ công.
2. Điền [thông tin học viên](STUDENT.md), [nhật ký thí nghiệm](artifacts/experiment_log.csv) và bản sao [mẫu báo cáo cá nhân](report/individual/MSSV_HoTen.md).
3. Kiểm tra mã nguồn, cách chạy, manifest dữ liệu và checklist trong [SUBMISSION.md](SUBMISSION.md).

## Tài liệu hướng dẫn

| Bạn cần tìm | Tài liệu |
|---|---|
| Setup baseline PostgreSQL + pgvector | [starter/README.md](starter/README.md) |
| Các bước làm và cách tính chỉ số | [GUIDE.md](GUIDE.md) |
| Tiến độ trong 4 giờ | [CHECKPOINTS.md](CHECKPOINTS.md) |
| Năm tiêu chí benchmark và bộ câu hỏi | [BENCHMARK.md](BENCHMARK.md) |
| Tiêu chí chấm điểm | [RUBRIC.md](RUBRIC.md) |
| Quy tắc sử dụng dữ liệu, AI và API | [RULES.md](RULES.md) |
| Cách nộp bài | [SUBMISSION.md](SUBMISSION.md) |

[data/format-example.json](data/format-example.json) chỉ minh họa định dạng, không phải corpus đủ điều kiện. Phần xử lý và benchmark do bạn tự hiện thực; không bắt buộc xây chatbot.

## Chạy bài làm trong repo này

Corpus hiện dùng *Pride and Prejudice* (Project Gutenberg eBook #1342). Nguồn, quy tắc đếm và 61 chương hợp lệ ghi tại [data/manifest.json](data/manifest.json); 20 câu hỏi và gold evidence ở [benchmark/questions.jsonl](benchmark/questions.jsonl). Kiểm tra quyền tại nơi sử dụng trước khi chia sẻ lại file gốc.

Trong PowerShell, từ thư mục `starter/`:

Tải bản Plain Text UTF-8 từ https://www.gutenberg.org/ebooks/1342, lưu tại `starter/data/pride_and_prejudice_raw.txt`. File raw và các chương được bỏ qua khi commit; người chấm có thể tải lại từ URL và chạy lệnh tách dưới đây. Chỉ chia sẻ lại văn bản khi đã kiểm tra quyền tại nơi sử dụng.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe scripts/split_chapters.py
.\.venv\Scripts\python.exe -m scripts.build_manifest
docker compose -p day6_student_starter up -d --wait
.\.venv\Scripts\python.exe scripts/check_setup.py
.\.venv\Scripts\python.exe -m scripts.check_corpus
.\.venv\Scripts\python.exe -m src.run
.\.venv\Scripts\python.exe -m scripts.prepare_audit
```

`src.run` dùng cùng model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và pgvector cosine exact cho A (800 ký tự, overlap 80), B (theo đoạn, tối đa 800 ký tự), C (như B, lọc `chapter` khi câu hỏi cung cấp). Lần đầu chạy cần mạng để tải model. Kết quả nằm trong `results/summary.json` và `results/traces.jsonl`; ba file `results/*_audit.csv` chứa nhãn AI hỗ trợ đã được học viên xác nhận. `starter/.env` và `starter/.venv` không được commit.

Nếu lệnh `python` trên Windows trỏ nhầm tới WindowsApps, dùng đường dẫn tới Python 3.11–3.14 đã cài để tạo `.venv`. Trên máy làm lab này, Python ở `C:\Users\lun19\AppData\Local\Python\bin\python.exe`.
