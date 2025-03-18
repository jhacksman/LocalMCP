# Manus-Open Tools Summary

## Browser Tools (13)
- action_browser_click
- action_browser_console_exec
- action_browser_console_view
- action_browser_input
- action_browser_move_mouse
- action_browser_navigate
- action_browser_press_key
- action_browser_restart
- action_browser_screenshot
- action_browser_scroll_down
- action_browser_scroll_up
- action_browser_select_option
- action_browser_view

## Terminal Tools (6)
- terminal_execute_command
- terminal_send_control
- terminal_send_key
- terminal_send_line
- terminal_kill_process
- terminal_reset

## Text Editor Tools (8)
- text_editor_view_dir
- text_editor_view
- text_editor_str_replace
- text_editor_find_content
- text_editor_find_file
- text_editor_read_file
- text_editor_write_file

## API Endpoints (16)
./server.py:@app.get("/browser/status")
./server.py:@app.get("/file")
./server.py:@app.get("/healthz")
./server.py:@app.get("/terminal/{terminal_id}/view")
./server.py:@app.post("/browser/action")
./server.py:@app.post("/file/multipart_upload_to_s3")
./server.py:@app.post("/file/upload_to_s3")
./server.py:@app.post("/init-sandbox")
./server.py:@app.post("/request-download-attachments")
./server.py:@app.post("/terminal/reset-all")
./server.py:@app.post("/terminal/{terminal_id}/kill")
./server.py:@app.post("/terminal/{terminal_id}/reset")
./server.py:@app.post("/terminal/{terminal_id}/write")
./server.py:@app.post("/text_editor")
./server.py:@app.post("/zip-and-upload")
./server.py:@app.websocket("/terminal")

## Total Tool Count
- Browser Tools: 13
- Terminal Tools: 6
- Text Editor Tools: 8
- Total Primary Tools: 27
- API Endpoints: 16
