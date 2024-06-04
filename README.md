python3 -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. async_file_upload.proto
python3 -m file_server
python3 -m client
