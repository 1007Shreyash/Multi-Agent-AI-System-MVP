import notion_client
import os
import sys

print(f"--- DIAGNOSTIC REPORT ---")
print(f"Python Executable: {sys.executable}")
print(f"Notion Client Version: {getattr(notion_client, '__version__', 'Unknown')}")
print(f"File Location: {notion_client.__file__}")
print(f"Current Working Directory: {os.getcwd()}")
print(f"Contains 'databases' attribute? {hasattr(notion_client.Client(auth='test'), 'databases')}")
if hasattr(notion_client.Client(auth='test'), 'databases'):
    print(f"Contains 'query' method? {hasattr(notion_client.Client(auth='test').databases, 'query')}")
print(f"-------------------------")