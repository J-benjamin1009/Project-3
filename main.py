import PySimpleGUI as sg
import requests
import os
import mimetypes
from canvasapi import Canvas

def notify_canvas(course_id, assignment_id, user_id, file_path, access_token):
    api_url = "https://canvas.instructure.com"
    canvas = Canvas(api_url, access_token)

    notify_url = f"{api_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}/comments/files"
    notify_headers = {"Authorization": f"Bearer {access_token}"}

    # Get file size dynamically using os.path.getsize
    file_size = os.path.getsize(file_path)

    # Auto-detect file name and content type using os.path.splitext and mimetypes.guess_type
    file_name = os.path.basename(file_path)
    content_type, _ = mimetypes.guess_type(file_name)

    notify_payload = {
        "name": file_name,
        "size": file_size,
        "content_type": content_type or "application/octet-stream"
    }

    notify_response = requests.post(notify_url, headers=notify_headers, data=notify_payload)

    if notify_response.status_code != 200:
        print(f"Error notifying Canvas. Status code: {notify_response.status_code}")
        print(f"Response content: {notify_response.text}")
        return None

    # Extract information from the notification response
    upload_url = notify_response.json().get("upload_url")
    upload_params = notify_response.json().get("upload_params")

    # Use the correct key for the file parameter
    file_param_key = upload_params.get("file_param", "file")

    return upload_url, file_param_key

def upload_file(upload_url, file_param_key, file_path):
    with open(file_path, "rb") as file:
        files = {file_param_key: (os.path.basename(file_path), file)}
        upload_response = requests.post(upload_url, files=files)
        file_id = upload_response.json().get("id")

        if upload_response.status_code != 201:
            print(f"Error uploading file. Status code: {upload_response.status_code}")
            print(f"Response content: {upload_response.text}")
            return None

    return file_id

def update_submission(course_id, assignment_id, user_id, file_id, access_token):
    api_url = "https://canvas.instructure.com"
    submission_url = f"{api_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
    payload = {
        "submission_type": "online_upload",
        "comment": {
            "file_ids": [[file_id]],
            # Add any other necessary fields
        }
    }



    put_response = requests.put(submission_url, headers={"Authorization": f"Bearer {access_token}"}, json=payload)

    if put_response.status_code == 200:
        print("Submission updated successfully")
    else:
        print(f"Error updating submission. Status code: {put_response.status_code}")
        print(f"Response content: {put_response.text}")

def batch_upload_feedback(course_id, assignment_id, user_ids, file_path, access_token):
    for user_id in user_ids:
        try:
            upload_url, file_param_key = notify_canvas(course_id, assignment_id, user_id, file_path, access_token)

            if upload_url is not None:
                file_id = upload_file(upload_url, file_param_key, file_path)

                if file_id is not None:
                    update_submission(course_id, assignment_id, user_id, file_id, access_token)

        except Exception as e:
            print(f"An error occurred for user {user_id}: {str(e)}")

def main():
    sg.theme("DarkGrey5")

    api_url = "https://canvas.instructure.com"
    access_token = "7~fWXkcEh26rA9X1qLQ6awjhNbE48kzzP8jnDsrnulwuOQSk0VSxB5g9unNXGwg6YO"
    course_id = "8195723"

    layout = [
        [sg.Text("Assignment ID"), sg.InputText(key="assignment_id")],
        [sg.Text("User ID (Student)"), sg.InputText(key="user_id")],
        [sg.Text("File Path"), sg.InputText(key="file_path"), sg.FileBrowse()],
        [sg.Button("Submit"), sg.Button("Batch"), sg.Button("Exit")]
    ]

    window = sg.Window("Canvas API Interaction", layout)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Exit"):
            break
        elif event == "Submit":
            assignment_id = values["assignment_id"]
            user_id = values["user_id"]
            file_path = values["file_path"]

            try:
                upload_url, file_param_key = notify_canvas(course_id, assignment_id, user_id, file_path, access_token)

                if upload_url is not None:
                    file_id = upload_file(upload_url, file_param_key, file_path)

                    if file_id is not None:
                        update_submission(course_id, assignment_id, user_id, file_id, access_token)

            except Exception as e:
                print(f"An error occurred: {str(e)}")

        elif event == "Batch":
            layout_batch = [
                [sg.Text("Assignment ID"), sg.InputText(key="assignment_id")],
                [sg.Text("User IDs (comma-separated)"), sg.InputText(key="user_ids")],
                [sg.Text("File Path"), sg.InputText(key="file_path"), sg.FileBrowse()],
                [sg.Button("Submit Batch"), sg.Button("Back")]
            ]

            window_batch = sg.Window("Batch Upload", layout_batch)

            while True:
                event_batch, values_batch = window_batch.read()

                if event_batch in (sg.WINDOW_CLOSED, "Back"):
                    break
                elif event_batch == "Submit Batch":
                    assignment_id_batch = values_batch["assignment_id"]
                    user_ids_batch = [user_id.strip() for user_id in values_batch["user_ids"].split(',')]
                    file_path_batch = values_batch["file_path"]

                    try:
                        batch_upload_feedback(course_id, assignment_id_batch, user_ids_batch, file_path_batch, access_token)

                    except Exception as e:
                        print(f"An error occurred: {str(e)}")

            window_batch.close()

    window.close()

if __name__ == "__main__":
    main()