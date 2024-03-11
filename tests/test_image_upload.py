from fieldsurveys.app_files.image_upload import upload_image_to_drive

# TODO: Fix tests
def test_upload_image_to_drive_failure(
    monkeypatch,
):
    monkeypatch.setattr(
        "fieldsurveys.app_files.image_upload.service_account.Credentials.from_service_account_file",
        lambda *args, **kwargs: "mock_creds",
    )
    monkeypatch.setattr(
        "fieldsurveys.app_files.image_upload.build", lambda *args, **kwargs: mock_build
    )
    monkeypatch.setattr(
        "fieldsurveys.app_files.image_upload.MediaFileUpload",
        lambda *args, **kwargs: mock_media_file_upload,
    )
    monkeypatch.setattr(
        "fieldsurveys.app_files.image_upload.service.permissions",
        lambda *args, **kwargs: mock_service_permissions,
    )

    survey_config = {"imgur_app_id": "test"}
    image_path = "tests/assets/sample.jpeg"
    keyfile_json = "path/to/keyfile.json"

    result = upload_image_to_drive(survey_config, image_path, keyfile_json)

    assert result is None
    mock_service_account.Credentials.from_service_account_file.assert_called_once_with(
        keyfile_json, scopes=["https://www.googleapis.com/auth/drive"]
    )
    mock_build.assert_called_once_with("drive", "v3", credentials="mock_creds")
    mock_media_file_upload.assert_called_once_with(
        image_path, mimetype="image/jpeg", resumable=True
    )
    mock_build.return_value.files.return_value.create.assert_called_once_with(
        body={"parents": ["your_folder_id"]},
        media_body=mock_media_file_upload.return_value,
        fields="id",
    )
    mock_service_permissions.return_value.create.assert_not_called()
