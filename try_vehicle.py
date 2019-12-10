from dronekit import connect
import socket


def try_vehicle():
    try:
        v = connect("com15", wait_ready=True)
    except Exception as e:
        print(e)
        return
    cmds = v.commands
    cmds.download()
    cmds.wait_ready()
    print("已检测到command..., commands数量为：", len(cmds))


def send_next(index):
    client = socket.socket()
    port = 8080
    ip = "127.0.0.1"
    adress = (ip, port)
    if index:
        msg = edit_msg(index)
        while True:
            client.sendto(msg.encode("utf-8"), adress)


def edit_msg(index):
    msg = ""
    return msg


if __name__ == "__main__":
    try_vehicle()


