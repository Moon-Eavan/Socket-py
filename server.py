import os
import socket
from datetime import datetime
from email import policy
from email.parser import BytesParser


class SocketServer:
    def __init__(self):
        self.bufsize = 1024  # 버퍼 크기 설정

        with open('./response.bin', 'rb') as file:
            self.RESPONSE = file.read()  # 응답 파일 읽기

        self.DIR_PATH = './request'
        self.createDir(self.DIR_PATH)

    def createDir(self, path):
        """디렉터리 생성"""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print("Error: Failed to create the directory.")

    def run(self, ip, port):
        """서버 실행"""
        # 소켓 생성
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(10)

        print("Start the socket server...")
        print('"Ctrl+C" for stopping the server!\n')

        try:
            while True:
                # 클라이언트의 요청 대기
                clnt_sock, req_addr = self.sock.accept()
                clnt_sock.settimeout(5.0)
                print(f"Request message from {req_addr}...")

                try:
                    response = b""

                    # ① HTTP 헤더의 끝(\r\n\r\n)까지 읽기
                    while b"\r\n\r\n" not in response:
                        chunk = clnt_sock.recv(self.bufsize)
                        if not chunk:
                            raise ValueError("요청 헤더를 전부 받지 못했습니다.")
                        response += chunk

                    header_end = response.index(b"\r\n\r\n") + 4
                    header_bytes = response[:header_end]

                    # 첫 줄: POST /api_root/Post/ HTTP/1.1
                    request_line, header_lines = header_bytes.split(
                        b"\r\n", 1
                    )
                    print(request_line.decode("ascii", errors="replace"))

                    # Content-Length: 요청 본문의 전체 바이트 수
                    headers = BytesParser(
                        policy=policy.default
                    ).parsebytes(header_lines)

                    content_length = int(headers.get("Content-Length", "0"))

                    # ② 아직 받지 못한 본문이 있으면 계속 읽기
                    while len(response) - header_end < content_length:
                        remaining = content_length - (
                            len(response) - header_end
                        )
                        chunk = clnt_sock.recv(
                            min(self.bufsize, remaining)
                        )
                        if not chunk:
                            raise ValueError(
                                "요청 본문을 전부 받지 못했습니다."
                            )
                        response += chunk

                    # 정확히 이번 요청에 해당하는 바이트만 사용
                    response = response[:header_end + content_length]
                    body = response[header_end:]

                    # ③ 실습 1: HTTP 요청 전체를 .bin 파일로 저장
                    timestamp = datetime.now().strftime(
                        "%Y-%m-%d-%H-%M-%S"
                    )
                    bin_path = os.path.join(
                        self.DIR_PATH, f"{timestamp}.bin"
                    )

                    with open(bin_path, "wb") as file:
                        file.write(response)

                    print(f"요청 원본 저장: {bin_path}")

                    # ④ 실습 2: multipart에서 image 필드 추출
                    # header_lines에는 Content-Type과 boundary가 들어 있다.
                    multipart_message = BytesParser(
                        policy=policy.default
                    ).parsebytes(header_lines + body)

                    if not multipart_message.is_multipart():
                        raise ValueError(
                            "multipart/form-data 요청이 아닙니다."
                        )

                    image_saved = False

                    for part in multipart_message.iter_parts():
                        field_name = part.get_param(
                            "name",
                            header="content-disposition"
                        )

                        if field_name == "image":
                            image_data = part.get_payload(decode=True)

                            if image_data is None:
                                raise ValueError(
                                    "이미지 데이터가 비어 있습니다."
                                )

                            content_type = part.get_content_type()
                            extension = {
                                "image/jpeg": ".jpg",
                                "image/png": ".png",
                                "image/gif": ".gif",
                                "image/webp": ".webp",
                            }.get(content_type, ".bin")

                            image_path = os.path.join(
                                self.DIR_PATH,
                                f"{timestamp}_image{extension}"
                            )

                            with open(image_path, "wb") as file:
                                file.write(image_data)

                            print(f"이미지 저장: {image_path}")
                            image_saved = True
                            break

                    if not image_saved:
                        raise ValueError(
                            "요청에서 image 필드를 찾지 못했습니다."
                        )

                    # 강의자료의 response.bin을 클라이언트에 전송
                    clnt_sock.sendall(self.RESPONSE)

                except (ValueError, OSError) as error:
                    print(f"요청 처리 오류: {error}")

                    try:
                        clnt_sock.sendall(
                            b"HTTP/1.1 400 Bad Request\r\n"
                            b"Content-Length: 0\r\n"
                            b"Connection: close\r\n"
                            b"\r\n"
                        )
                    except OSError:
                        pass

                finally:
                    # 클라이언트 소켓 닫기
                    clnt_sock.close()

        except KeyboardInterrupt:
            print("\nStop the server...")

        finally:
            # 서버 소켓 닫기
            self.sock.close()


if __name__ == "__main__":
    server = SocketServer()
    server.run("127.0.0.1", 8000)