# Chúc mừng sinh nhật Thu Huệ

Trang web tặng sinh nhật: màn mở quà, bộ 12 ảnh, 5 đoạn phim, lá thư và phần thổi nến, có nhạc nền.

HTML/CSS/JS thuần, không cần build. Toàn bộ font, ảnh, video và nhạc nằm trong `assets/`, không gọi dịch vụ bên ngoài. Trang gắn `noindex` để công cụ tìm kiếm không lập chỉ mục.

## Đưa lên mạng bằng GitHub Pages

1. Vào **Settings → Pages** của repo.
2. Ở **Build and deployment**, chọn **Source: Deploy from a branch**, **Branch: `main`**, thư mục **`/ (root)`**, rồi **Save**.
3. Sau khoảng một phút, trang chạy tại `https://tuong06.github.io/sn/`.

## Xem trên máy

```sh
python3 -m http.server 8000
```

Mở http://localhost:8000. Mở thẳng file `index.html` cũng được, nhưng một số trình duyệt chặn font khi chạy từ `file://`.

## Nhạc nền

`assets/audio/happy-birthday.mp3` là bản *Happy Birthday to You* (giai điệu đã thuộc phạm vi công cộng) phối kiểu hộp nhạc, nhịp waltz. Bản nhạc được tổng hợp bằng `assets/audio/make_music.py` (Python + NumPy), không dùng bản thu của ai nên không vướng bản quyền ghi âm.

Tạo lại bản nhạc:

```sh
python3 assets/audio/make_music.py hb.wav
ffmpeg -i hb.wav -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:a libmp3lame -b:a 128k assets/audio/happy-birthday.mp3
```

Trình duyệt không cho tự phát nhạc khi chưa có thao tác của người xem, nên trang mở bằng màn "Mở quà": bấm nút là nhạc bắt đầu. Nhạc tự tạm dừng khi phim phát hoặc khi chuyển tab, rồi phát tiếp sau đó. Nút "Nhạc nền" ở góc dưới bên phải dùng để bật hoặc tắt.

## Sửa nội dung

- Lời chúc: phần `<section class="letter">` trong `index.html`.
- Ảnh: thay file trong `assets/img/` (bản lớn `pNN.jpg`, bản nhỏ `pNN-s.jpg`), giữ nguyên tên.
- Phim: thay `assets/video/vN.mp4` và ảnh bìa `vN.jpg`; tên và thời lượng từng đoạn nằm trong danh sách `.clips`.
