import grpc
import time
import pandas
import asyncio

from async_file_upload_pb2 import PingRequest, File, MetaData, FileUploadRequest, FileUploadResponse
from async_file_upload_pb2_grpc import FileTransforToServerStub as Stub

def load_file_metadata() -> MetaData:
    return MetaData(file_name="file-coderstool.csv", file_type="CSV")

def load_file_data(file_meta_data: MetaData) -> File:
    if file_meta_data.file_type == "CSV":
        for data_chunk in pandas.read_csv(file_meta_data.file_name, chunksize=100):
            yield File(file_data_bytes=data_chunk.to_json().encode())
    
async def busy_with_other_task(delay) -> None:
    await asyncio.sleep(delay)
    print(f"Busy for {delay} seconds while file uploads")

async def run() -> None:
    session_id = None
    client_id = "69420"
    upload_status = None
    async with grpc.aio.insecure_channel("localhost:50051") as grpc_channel:
        stub = Stub(grpc_channel)
        
        print("Sending a handshake to server...")
        ping_response = await stub.Handshake(PingRequest(client_id=client_id))
        session_id = ping_response.session_id
        print(f"Connected to server with the Session ID: {session_id}")

        file_meta_data = load_file_metadata()
        print(f"Requesting to Upload file: {file_meta_data.file_name}")
        upload_response = stub.UploadToServer(FileUploadRequest(client_id=client_id, session_id=session_id, meta_data=file_meta_data))
        async for response in upload_response:
            upload_status = response.upload_status
            print(f"Status from server: {upload_status}")

        if upload_status == "PENDING":                  # to avoid this, use Enum in protobuf
            print("Sending file data to server...")
            for chunk_id, file_chunck in enumerate(load_file_data(file_meta_data)):
                start_time = time.time()
                secondary_task = asyncio.create_task(busy_with_other_task(2))
                tertiary_task = asyncio.create_task(busy_with_other_task(3))
                data_upload_response = stub.UploadToServer(FileUploadRequest(client_id=client_id, session_id=session_id, file_data=file_chunck))
                async for response in data_upload_response:
                    print(f"Status from server for chunck {chunk_id}: {response.upload_status}")
                await secondary_task
                await tertiary_task
                print(f"Total waiting time: {time.time() - start_time}")

if __name__ == "__main__":
    asyncio.run(run())
