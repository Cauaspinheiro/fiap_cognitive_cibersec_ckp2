import socket
import threading

from termcolor import colored

from constants import *

HOST = "localhost"


def connect_client():
    username = input("Digite seu nome de usuário: ")

    username = username.replace(" ", "-")

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    client.settimeout(1)

    client.send(f"{Actions.DEFINE_USERNAME} {username}".encode())

    print(
        colored("[SISTEMA]: Conectado com sucesso! Você já pode digitar", SYSTEM_COLOR)
    )

    return client


client = connect_client()


def receive():
    while True:
        try:
            message = client.recv(1024).decode()

            if not message:
                client.close()
                break

            print(message)
        except socket.timeout:  # Does not get any message, just try again
            pass
        except OSError:  # Connection closed, break without logging
            break
        except:  # Something went wrong
            print(
                colored(
                    "[SISTEMA]: Ocorreu um erro ao receber a mensagem", SYSTEM_COLOR
                )
            )
            client.close()
            break

    client.close()


def send():
    while True:
        message = input()

        if not message.strip():  # ignore empty messages
            continue

        if message.lower() == Actions.QUIT:
            try:
                client.send(Actions.QUIT.encode("utf-8"))
            except:
                pass

            client.close()

            print(colored("[SISTEMA]: Desconectado com sucesso!", SYSTEM_COLOR))

            break

        client.send(message.encode("utf-8"))


receive_thread = threading.Thread(target=receive)
send_thread = threading.Thread(target=send)

receive_thread.start()
send_thread.start()
