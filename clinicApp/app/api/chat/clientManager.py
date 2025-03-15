from starlette.websockets import WebSocket


class ConnectionManager:
    def __init__(self):
        # Хранение активных соединений {department_name: {doctor_id: WebSocket}}
        self.active_connections: dict[str, dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, department_name: str, doctor_id: int):
        await websocket.accept()

        if department_name not in self.active_connections:
            self.active_connections[department_name] = {}
        self.active_connections[department_name][doctor_id] = websocket

    def disconnect(self, department_name: str, doctor_id: int):
        if department_name in self.active_connections and doctor_id in self.active_connections[department_name]:
            del self.active_connections[department_name][doctor_id]
            if not self.active_connections[department_name]:
                del self.active_connections[department_name]

    async def broadcast(self, message: str, department_name: str, sender_id: int, sender_name: str, timestamp: str):
        if department_name not in self.active_connections:
            return

        message_data = {
            "msg": message,
            "timestamp": timestamp,
            "sender": sender_name,
            "isSender": False
        }

        for doctor_id, websocket in self.active_connections[department_name].items():
            message_data["isSender"] = doctor_id == sender_id
            await websocket.send_json(message_data)