from termcolor import COLORS, colored
import socket
import threading

from constants import *


class ServerUser:
    address: str
    connection: socket.socket
    username: str
    color: str
    room_code: str

    def __init__(self, connection: socket.socket, address: str) -> None:
        self.address = address
        self.connection = connection

        self.username = ""
        self.color = "white"
        self.room_code = ""

    def username_chat(self):
        return colored(self.username, self.color)


class Room:
    code: str
    users: list[ServerUser]

    def __init__(self, code: str) -> None:
        self.code = code
        self.users = []


HOST = ""

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

users: list[ServerUser] = []
rooms: list[Room] = []


def send_system_message(sender: ServerUser, message: str):
    sender.connection.send(colored(f"[SISTEMA]: {message}", SYSTEM_COLOR).encode())


def send_chat_message(sender: ServerUser, message: str):
    for user in users:
        if (
            user.room_code == sender.room_code
            and user.room_code != ""
            and not user is sender
        ):
            user.connection.send(colored(f"[CHAT]: {message}", CHAT_COLOR).encode())


def send_user_message(sender: ServerUser, message: str):
    for user in users:
        if (
            user.room_code == sender.room_code
            and user.room_code != ""
            and not user is sender
        ):
            user.connection.send(
                colored(f"\t\t\t\t{sender.username}: {message}", sender.color).encode()
            )


def remove_user(user: ServerUser):
    if user in users:
        users.remove(user)


has_room = lambda room_code: len(
    list(filter(lambda room: room.code == room_code, rooms))
)


def get_action_and_content(message: str):
    splitted = message.split(" ")

    action = splitted[0]

    if not action.startswith("/"):
        return "", message

    content = ""

    if len(splitted) > 1:
        content = "".join(splitted[1:])

    return action, content


def help_action(sender: ServerUser):
    send_system_message(
        sender,
        f"""Comandos disponíveis:
/quit: Desconecta você do sistema
/help: Exibe essa mensagem
/username: Troca seu nome de usuário
/color: Troca sua cor no chat
/enter: Entra em uma sala com um código
/create: Cria uma nova sala
/list: Exibe todos os usuários da sala

{"Você já pode digitar uma mensagem para enviar para os usuários da sua sala" if sender.room_code else "Entre em uma sala para poder enviar mensagens"}""",
    )


def quit_action(sender: ServerUser):
    send_chat_message(sender, f"{sender.username_chat()} se desconectou")
    remove_user(sender)


def define_color_action(sender: ServerUser, content: str):
    if not content in list(COLORS.keys()):
        return send_system_message(
            sender,
            f"Cor não existe, essas são as cores possíveis: {list(COLORS.keys())}",
        )

    if "grey" in content:
        return send_system_message(sender, f"Essa cor pertence ao sistema!")

    old_color = sender.color
    sender.color = content
    send_system_message(sender, colored("Cor definida!", sender.color))
    send_chat_message(
        sender,
        f"{colored(sender.username, old_color)} mudou de cor para {sender.username_chat()}",
    )


def define_username_action(sender: ServerUser, content: str):
    old_username = sender.username
    sender.username = content

    if not old_username:
        return

    send_system_message(sender, "Username trocado com sucesso!")
    send_chat_message(
        sender,
        f"{colored(old_username, sender.color)} agora é {sender.username_chat()}",
    )


def create_room_action(sender: ServerUser, content: str):
    if has_room(content):
        return send_system_message(sender, "Sala já existe!")

    new_room = Room(content)

    rooms.append(new_room)

    send_system_message(sender, "Sala criada!")
    send_chat_message(sender, f"{sender.username_chat()} saiu da sala!")

    sender.room_code = new_room.code


def enter_room_action(sender: ServerUser, content: str):
    if has_room(content):
        send_chat_message(sender, f"{sender.username_chat()} saiu da sala!")

        sender.room_code = content

        send_chat_message(sender, f"{sender.username_chat()} entrou na sala!")
    else:
        send_system_message(sender, "Sala não encontrada!")


def list_room_users_action(sender: ServerUser):
    if not has_room(sender.room_code):
        return send_system_message(sender, "Você não está em um sala!")

    room_users = ""

    for user in users:
        if user.room_code == user.room_code:
            room_users += f"{user.username_chat()}, "

    room_users.removesuffix(", ")

    send_system_message(sender, f"Usuários na sala: {room_users}")


def handle_actions(sender: ServerUser, action: str, content: str):
    match action.lower():
        case Actions.HELP:
            return help_action(sender)
        case Actions.QUIT:
            return quit_action(sender)
        case Actions.DEFINE_COLOR:
            return define_color_action(sender, content)
        case Actions.DEFINE_USERNAME:
            return define_username_action(sender, content)
        case Actions.CREATE_ROOM:
            return create_room_action(sender, content)
        case Actions.ENTER_ROOM:
            return enter_room_action(sender, content)
        case Actions.LIST_ROOM_USERS:
            return list_room_users_action(sender)
        case _:
            handle_send_message_action(sender, content)


def handle_send_message_action(sender: ServerUser, content: str):
    if not has_room(sender.room_code):
        return send_system_message(sender, "Entre ou crie uma sala por favor")

    if not content:
        return

    send_user_message(sender, content)


def handle_user(user: ServerUser):
    while True:
        try:
            message = user.connection.recv(1024).decode()

            if not message:
                remove_user(user)
                break

            action, content = get_action_and_content(message)

            handle_actions(user, action, content)

        except socket.error:
            remove_user(user)
            break


print("Servidor iniciado. Aguardando conexões...")


def connect_clients_to_server():
    connection, address = server.accept()

    user = ServerUser(connection, address)

    users.append(user)

    thread = threading.Thread(target=handle_user, args=(user,))

    thread.start()


while True:
    connect_clients_to_server()
