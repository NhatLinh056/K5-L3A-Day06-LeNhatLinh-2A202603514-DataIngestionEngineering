# Báo cáo cá nhân — Day 06

**Học viên:** Lê Nhật Linh · **MSSV:** 2A202603514 · **Lớp:** L3A

## Dữ liệu và pipeline

Corpus là *Pride and Prejudice* của Jane Austen, Project Gutenberg eBook #1342. File raw ghi lần cập nhật 01/09/2026; SHA-256, URL và 61 ID chương nằm trong [manifest](../../data/manifest.json). Project Gutenberg ghi văn bản thuộc phạm vi công cộng tại Mỹ; trước khi công khai file gốc cần kiểm tra quyền sử dụng tại nơi nộp bài và điều khoản Project Gutenberg. Không dùng nội dung mở đầu, mục lục, chú thích ảnh, dòng nhà in hoặc giấy phép để truy xuất.

Mỗi chương là một đơn vị nguồn có ID `chapter_01` đến `chapter_61`. Quy tắc tính: ít nhất 1.500 ký tự sau chuẩn hóa Unicode NFC, gộp dòng trong đoạn và bỏ minh họa. Cả 61 chương đạt; chương ngắn nhất 3.930 ký tự. Mỗi chunk giữ `document_id`, URL `source`, số chương ở `page`, và metadata `chapter` lấy trực tiếp từ tên file chương. Không có trang PDF; số chương là vị trí truy vết tương đương. Script kiểm tra lỗi ở [check_corpus.py](../../starter/scripts/check_corpus.py).

Embedding local: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, Sentence Transformers 5.7.0, vector 384 chiều, cùng model cho document và query. Store: PostgreSQL 16.16 + pgvector 0.8.7, psycopg 3.3.8; cosine exact, một bảng chung với khóa `(strategy, chunk_id)`. Chi phí API 0 USD; thời gian CPU và điện chưa quy đổi thành tiền. Lệnh cài/chạy trong [README](../../README.md). Pipeline báo lỗi khi model hoặc database không hoạt động; không dùng vector mock.

## Cấu hình và benchmark

| Strategy | Chunking | Filter |
|---|---|---|
| A | Cửa sổ 800 ký tự, overlap 80 | Không |
| B | Gom đoạn, tối đa 800 ký tự | Không |
| C | Giống hệt B | `chapter` khi câu hỏi cung cấp chương |

A–B thay cách chunk. B–C chỉ thay filter. C dùng lại vector của B nên thời gian ingest C không bao gồm embedding. Tập [benchmark](../../benchmark/questions.jsonl) gồm 20 câu có đáp án và quote nguồn, 15 dev/5 test; 3 câu có filter, trong đó 1 câu test. `check_corpus.py` xác nhận toàn bộ quote nằm đúng chương sau chuẩn hóa. Bộ câu hỏi rải qua nhiều chương, nhưng tập test chỉ có 5 câu và thiên về các chương cuối; kết quả không đại diện cho truy xuất sách nói chung.

Tiêu chí chọn đã ghi trước khi xem test: Evidence Hit@3 trên dev cao nhất, sau đó Hit@1 trên dev, sau đó ít chunk hơn. Kết quả test không dùng để đổi lựa chọn.

## Kết quả truy xuất

Chạy ngày 13/11/2026. Hit yêu cầu cùng source/chương và **đủ quote bằng chứng trong một chunk**. Đây là kiểm tra khớp quote; trường hợp bằng chứng tương đương nhưng khác chữ cần người chấm xem trace. [Trace đầy đủ](../../results/traces.jsonl) có 60 lượt hỏi, mỗi lượt top-3 với text, score, metadata và nhãn hit.

| Strategy | Split | Hit@1 | Evidence Hit@3 | Chunk count | Ingest (giây) | API cost |
|---|---|---:|---:|---:|---:|---:|
| A | dev | 4/15 | 7/15 | 971 | 15,379 | 0 USD |
| A | test | 0/5 | 2/5 | 971 | — | 0 USD |
| B | dev | 4/15 | 7/15 | 1.095 | 19,798 | 0 USD |
| B | test | 0/5 | 2/5 | 1.095 | — | 0 USD |
| C | dev | 4/15 | 7/15 | 1.095 | 0,318 (tái dùng B) | 0 USD |
| C | test | 0/5 | 3/5 | 1.095 | — | 0 USD |

Chọn **A** theo tiêu chí dev đã chốt: ba cấu hình hòa Hit@3 và Hit@1, A có ít chunk hơn. C tốt hơn A trên test (3/5 so với 2/5); đây là quan sát sau chọn, không dùng để chọn lại. Chạy lại pipeline cho đúng số bản ghi 971/1.095/1.095, không nhân đôi; mỗi lần nạp thay trọn bộ chunk của chiến lược trong một transaction nên chunk cũ được xóa khi dữ liệu đổi.

## Audit năm khía cạnh

Các file [coherence](../../results/coherence_audit.csv), [metadata](../../results/metadata_audit.csv) và [grounding](../../results/grounding_audit.csv) được AI hỗ trợ tạo bản nháp. Học viên Lê Nhật Linh xác nhận đã đọc và duyệt nhãn. Đây là đánh giá có AI hỗ trợ, không phải chấm độc lập không dùng AI.

| Strategy | Coherence TB /2 (10 vị trí) | Metadata đúng/đủ (test top-3) | Filter tuân thủ (câu test có filter) | Grounding 0/1/2; TB /2 |
|---|---:|---:|---:|---|
| A | 1,0 | 15/15 | 0/1 | 3/0/2; 0,8 |
| B | 1,7 | 15/15 | 0/1 | 3/0/2; 0,8 |
| C | 1,7 | 15/15 | 1/1 | 2/0/3; 1,2 |

Coherence dùng cùng 10 vị trí: ký tự 100–140 của 10 chương đầu, xác định trước khi xem điểm. Chunk A tại các vị trí này đều dừng giữa câu/từ nên chấm 1. B/C giữ trọn đoạn ở 7/10 vị trí; ba đoạn dài vẫn bị cắt tại giới hạn 800. Metadata của 45 chunk test được đối chiếu bằng code với URL nguồn, số chương, `chapter` và text trong chương sạch: 45/45 khớp. Trường `chapter` giúp giới hạn tìm kiếm khi người dùng nêu chương; nó không giúp câu không có thông tin chương. Grounding chỉ đo bằng chứng truy xuất, không đo độ chính xác câu trả lời của LLM.

## Phân tích và kết luận

- **A–B:** B cải thiện coherence từ 1,0 lên 1,7/2 nhưng không tăng Hit@1 hay Hit@3 trên bộ câu hỏi này. B tạo thêm 124 chunk và mất thêm khoảng 4,42 giây ingest trong lần đo cuối. Đo thời gian một lần chịu ảnh hưởng cache và tải máy.
- **B–C:** C chỉ đổi filter. Với q18 ở test, A/B lấy ba chunk từ chương 48, thiếu quote về thư nhanh từ ông Gardiner. C lọc chương 49 và lấy đúng bằng chứng ở hạng 2. Test Evidence Hit@3 tăng từ 2/5 lên 3/5, nhưng chỉ một câu test có filter.
- **Lỗi:** q19 (Bingley đến một mình) và q20 (Bingley và Jane đi chậm) không có đủ bằng chứng trong top-3 của cả ba cấu hình. q19 trả về những chương khác về gia đình Bennet; q20 trả về đoạn liên quan đi bộ nhưng sai sự kiện. Không coi các đoạn có điểm cosine khá cao là câu trả lời đúng.
- **Giới hạn:** Câu hỏi tiếng Việt trên nguồn tiếng Anh phụ thuộc năng lực đa ngữ của model. Nhiều câu dev/test còn dễ hoặc có nhắc chương; gold kiểm tra quote chính xác nên có thể bỏ sót bằng chứng diễn đạt tương đương. Tập test 5 câu có sai số lớn; nhãn audit có AI hỗ trợ nên vẫn có nguy cơ thiên lệch. Chi phí 0 USD chỉ nói về API, không bao gồm máy local.

Nếu làm lại, mở rộng bộ test theo chương/chủ đề và thêm câu diễn đạt lại khó hơn. Có thể thử hybrid search sau khi giữ nguyên tập test mới. Công cụ AI được dùng để hỗ trợ code, tạo câu hỏi nháp và nhãn audit; quote và metadata đã được đối chiếu bằng script, học viên đã xác nhận các nhãn ý nghĩa.
