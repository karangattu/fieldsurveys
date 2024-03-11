from playwright.sync_api import Page, expect
import time
import pytest
import subprocess

PORT = "63092"


def dismiss_modal(page: Page) -> None:
    page.locator("#shiny-modal").press("Escape")
    time.sleep(0.5)  # TODO: This is added to prevent tests being too fast to click
    page.locator("#shiny-modal").click()


# TODO - Create a temp app
@pytest.fixture(scope="session")
def start_shiny_app():
    # Start the app locally
    shiny_app_process = subprocess.Popen(
        ["python", "-m", "shiny", "run", "--port", PORT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the app to load successfully
    timeout = 30  # Timeout in seconds
    start_time = time.time()
    while True:
        output = shiny_app_process.stderr.readline().decode().strip()
        if "Application startup complete." in output:
            break
        if time.time() - start_time > timeout:
            raise TimeoutError("Timeout: Shiny app did not load within the specified time.")
        time.sleep(1)

    yield

    shiny_app_process.terminate()


@pytest.mark.only_browser("chromium")
def test_shiny_app(page: Page, start_shiny_app) -> None:
    page.goto(f"http://localhost:{PORT}/")

    # verify value box on landing page
    expect(page.get_by_text("Use this page to record your")).to_be_visible()
    # check if the first accordion is the data source accordion panel
    expect(page.locator("#accordion_data_sources")).to_contain_text(
        "Select Data source"
    )

    # disable bandwidth saver for test
    page.get_by_label("Bandwidth Saver").check()
    page.get_by_text("butterfly").click()
    page.get_by_role("button", name="Proceed to next step").click()

    # Assert that accordion panel title is updated
    expect(page.locator("#accordion_data_sources")).to_contain_text(
        "Data source: butterfly"
    )
    page.locator("#surveyors").locator("..").locator("> .multi").click()
    # Cole is the first one on the list
    page.get_by_text("Cole").click()
    page.get_by_label("Choose Surveyor(s)*:").press("Escape")
    page.get_by_role("button", name="Proceed to next step").click()
    expect(page.locator("#accordion_data_sources")).to_contain_text("Surveyors: Cole")

    # Location accordion panel
    page.get_by_text("GPS Location").click()
    expect(page.locator("#plot-label")).to_contain_text("Select the plot")
    page.get_by_role("button", name="Proceed to next step").click()
    expect(page.locator("#accordion_data_sources")).to_contain_text(
        "Survey Point: P1 - 0a"
    )

    # Specimen accordion panel

    # check if alpha code is toggled, genus+species selection is reset and vice versa
    page.get_by_label("Show 4-letter Alpha Code").check()
    expect(page.get_by_label("Show 4-letter Alpha Code")).to_be_checked()
    expect(page.get_by_label("Show Genus + Species instead")).not_to_be_checked()
    page.locator("#specimen").locator("..").locator("> .single").click()
    page.get_by_text("ADCA").click()
    page.get_by_label("Show Genus + Species instead").check()
    expect(page.get_by_label("Show 4-letter Alpha Code")).not_to_be_checked()
    expect(page.get_by_label("Show Genus + Species instead")).to_be_checked()
    page.locator("#specimen").locator("..").locator("> .single").click()
    page.get_by_text("Adelpha californica").click()
    page.get_by_label("Show Genus + Species instead").uncheck()
    expect(page.get_by_label("Show 4-letter Alpha Code")).not_to_be_checked()
    expect(page.get_by_label("Show 4-letter Alpha Code")).not_to_be_checked()

    # Look up by common name - most common use case
    page.locator("#specimen").locator("..").locator("> .single").click()
    page.get_by_text("Lange's Metalmark").click()
    page.get_by_role("button", name="Record observation").click()
    expect(page.get_by_role("heading")).to_contain_text("Verify your observation")
    expect(page.locator("#submit_verify")).to_contain_text("Looks good")
    expect(page.locator("#edit")).to_contain_text("Edit observation")
    page.get_by_role("button", name="Looks good").click()
    expect(page.get_by_text("Your observation has been")).to_be_visible()
    page.get_by_role("button", name="Proceed to uploading").click()

    # upload page
    expect(page.locator("tbody")).to_contain_text("Lange's Metalmark")
    page.get_by_role("cell", name="Lange's Metalmark").click()
    page.get_by_role("button", name="Clear selected observation").click()
    page.get_by_role("button", name="Delete").click()
    expect(page.locator("#shiny-modal")).to_contain_text(
        "Your observation has been cleared"
    )
    dismiss_modal(page)
    page.get_by_label("Select Google Sheet to upload").click()

    # check restore functionality
    page.get_by_role("button", name="Restore observation(s)").click()
    expect(page.locator("#shiny-modal")).to_contain_text(
        "Your observations have been restored"
    )
    dismiss_modal(page)
    expect(page.locator("tbody")).to_contain_text("Lange's Metalmark")
    page.get_by_role("button", name="Go back to recording").click()

    # record observations page -> assert restore remembered user choices
    expect(page.get_by_role("button", name="Surveyors: Cole")).to_be_visible()
    expect(page.get_by_role("button", name="Survey Point: P1 - 0a")).to_be_visible()
    expect(page.get_by_role("button", name="Data source: butterfly")).to_be_visible()
    page.get_by_role("button", name="Data source: butterfly").click()
    page.get_by_label("Bandwidth Saver").uncheck()
    page.get_by_role("button", name="Select Survey data").click()
    page.locator("#specimen").locator("..").locator("> .single").click()
    page.get_by_text("California Sister").click()
    expect(page.get_by_role("heading", name="Source: iNaturalist")).to_be_visible()
    expect(
        page.get_by_role("heading", name="California Sister pics").get_by_role(
            "insertion"
        )
    ).to_be_visible()
    expect(
        page.get_by_role("heading", name="California Sister notes").get_by_role(
            "insertion"
        )
    ).to_be_visible()
    expect(page.get_by_role("heading", name="Source: Wikipedia")).to_be_visible()

    # check vegetation survey conditional UI
    page.get_by_label("Yes").check()
    expect(page.get_by_text("Select the canopy cover")).to_be_visible()
    expect(page.get_by_text("Select the abundance")).to_be_visible()
    expect(page.get_by_text("Select the life stage")).to_be_visible()
    expect(page.get_by_text("Enter the height of the plant")).to_be_visible()
    page.get_by_label("No", exact=True).check()
    expect(page.get_by_text("Select the canopy cover")).not_to_be_visible()
    expect(page.get_by_text("Select the abundance")).not_to_be_visible()
    expect(page.get_by_text("Select the life stage")).not_to_be_visible()
    expect(page.get_by_text("Enter the height of the plant")).not_to_be_visible()
