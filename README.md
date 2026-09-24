# Python Socket HTTP Upload Server

Python의 `socket` 모듈로 만든 간단한 HTTP 서버입니다. `curl`이 보낸 `multipart/form-data` POST 요청을 받아, 요청 전체를 이진 파일로 기록하고 `image` 필드의 이미지 데이터를 별도 파일로 저장합니다.

## 동작 방식

1. `127.0.0.1:8000`에서 클라이언트 연결을 기다립니다.
2. HTTP 헤더에서 `Content-Length`를 확인하고 요청 본문을 끝까지 받습니다.
3. 요청 줄, 헤더, 본문을 포함한 원본 바이트를 `request/년-월-일-시-분-초.bin`에 저장합니다.
4. 멀티파트 본문에서 `image` 필드를 찾아 `request/년-월-일-시-분-초_image.jpg`와 같은 이미지 파일로 저장합니다.
5. `response.bin`에 담긴 HTTP 응답을 클라이언트에 보냅니다.

## 파일 구성

- `server.py`: 소켓 서버와 요청 처리 코드
- `response.bin`: 클라이언트에 전송할 HTTP 응답
- `request/`: 수신한 요청 원본과 추출한 이미지가 저장되는 폴더

별도의 웹 프레임워크 없이 TCP 소켓에서 HTTP 요청을 직접 읽고, 멀티파트 데이터를 처리하는 예제입니다.