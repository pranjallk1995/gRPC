1. python3 -m grpc_tools.protoc -I. --python_out=. --pyi_out=. --grpc_python_out=. async_file_upload.proto

2. python3 -m file_server

3. python3 -m client
