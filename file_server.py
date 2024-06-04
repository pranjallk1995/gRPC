import grpc
import uuid
import asyncio

from enum import Enum
from typing import AsyncIterable
from async_file_upload_pb2 import PingResponse, FileUploadRequest, FileUploadResponse
from async_file_upload_pb2_grpc import FileTransforToServerServicer as Servicer
from async_file_upload_pb2_grpc import add_FileTransforToServerServicer_to_server as add_to_server

class UploadStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

class ServicerSub(Servicer):

    def __init__(self) -> None:
        self.connected_clients = {}
        self.file_meta_datas = {}

    async def Handshake(self, request: PingResponse, unused_context):
        if request.client_id is not None:
            self.connected_clients[request.client_id] = str(uuid.uuid4())
            print(f"Got a connection request from Client: {request.client_id}")
            print(f"Assigning Session ID: {self.connected_clients[request.client_id]} to {request.client_id}")
            return PingResponse(client_id=request.client_id, session_id=self.connected_clients[request.client_id])

    async def UploadToServer(self, request_iterator: AsyncIterable[FileUploadRequest], unused_context) -> FileUploadResponse:
        if str(request_iterator.meta_data) != "":
            if request_iterator.session_id == self.connected_clients[request_iterator.client_id]:
                self.file_meta_datas[request_iterator.session_id] = request_iterator.meta_data
                print(f"Got request from Client to store: {request_iterator.meta_data.file_name}")
                yield FileUploadResponse(file_name=request_iterator.meta_data.file_name, upload_status=UploadStatus.PENDING.value)
        elif str(request_iterator.file_data) != "":
            with open("file_data_server.json", "a") as file:
                file.write(request_iterator.file_data.file_data_bytes.decode())
                yield FileUploadResponse(file_name=self.file_meta_datas[request_iterator.session_id].file_name, upload_status=UploadStatus.IN_PROGRESS.value)
        else:
            yield FileUploadResponse(upload_status=UploadStatus.FAILED.value)

async def serve() -> None:
    server = grpc.aio.server()
    add_to_server(ServicerSub(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("Server is running... ")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
