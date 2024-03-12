from faicons import icon_svg
from shiny import ui

from .utils import get_sheets

# use a CDN for assets instead of local
loading_tag = ui.tags.img(src="https://gilded-mandazi-30bb2e.netlify.app/loading.svg", height="32px", width="32px")
woman_on_smartphone = ui.tags.img(src="https://gilded-mandazi-30bb2e.netlify.app/woman_on_smartphone.svg")
woman_reminding = ui.tags.img(src="https://gilded-mandazi-30bb2e.netlify.app/woman_reminding.svg")


def record_observation(survey_config):
    return ui.nav_panel(
        "Record observation",
        ui.value_box(
            "Use this page to record your observations",
            "",
            "Once observations for a survey point are recorded, proceed to next page to upload observations \n",
            showcase=woman_on_smartphone,
            theme=("purple"),
            showcase_layout="left center",
        ),
        ui.layout_columns(
            ui.card(
                ui.accordion(
                    ui.accordion_panel(
                        "Select Data source",
                        ui.tooltip(
                            ui.input_switch(
                                "low_data_mode",
                                "Bandwidth Saver",
                                False,
                            ),
                            "Enable this mode to reduce your data usage.💰 ",
                            "It won't load images and trivia about specimen when turned on",
                            placement="top",
                            id="low_data_mode_tooltip",
                        ),
                        ui.input_radio_buttons(
                            id="data_source",
                            label="Select data source",
                            choices=survey_config["survey_data_sources"],
                        ),
                        ui.input_action_button(
                            "go_to_surveyors",
                            label="Proceed to next step",
                            class_="btn btn-info",
                            icon=icon_svg("circle-check"),
                        ),
                        value="data_source",
                        icon=icon_svg("database"),
                    ),
                    ui.accordion_panel(
                        "Select Surveyor details",
                        ui.input_date("survey_date", label="Survey Date"),
                        ui.input_selectize(
                            "location",
                            label="Select the location",
                            choices=survey_config["location"],
                        ),
                        ui.input_selectize(
                            "surveyors",
                            label="Choose Surveyor(s)*:",
                            choices=survey_config["surveyors"],
                            multiple=True,
                        ),
                        ui.input_action_button(
                            "go_to_survey_points",
                            label="Proceed to next step",
                            class_="btn btn-info",
                            icon=icon_svg("circle-check"),
                        ),
                        value="surveyors",
                        icon=icon_svg("people-group"),
                    ),
                    ui.accordion_panel(
                        "Select Survey site",
                        ui.input_text("gps_loc", label="GPS Location"),
                        ui.output_text("note_accuracy"),
                        ui.tooltip(
                            ui.input_task_button(
                                "gps",
                                "Get my location",
                                class_="btn btn-info",
                                icon=icon_svg("location-crosshairs"),
                                label_busy="Fetching...",
                                icon_busy=loading_tag,
                                auto_reset=False,
                            ),
                            "🎯 Press button multiple times to enhance accuracy within 15 meters. "
                            "Requires location access on browser",
                            id="gps_location_tooltip",
                        ),
                        ui.br(),
                        ui.br(),
                        ui.input_selectize(
                            "plot",
                            label="Select the plot",
                            choices=survey_config["plots"],
                        ),
                        ui.input_selectize(
                            "survey_point",
                            label="Select the survey point",
                            choices=survey_config["survey_points"],
                            options={"readonly": "readonly"},
                        ),
                        ui.input_selectize(
                            "survey_side",
                            label="Select the side",
                            choices=survey_config["survey_side"],
                        ),
                        ui.input_action_button(
                            "go_to_specimen",
                            label="Proceed to next step",
                            class_="btn btn-info",
                            icon=icon_svg("circle-check"),
                        ),
                        value="survey_points",
                        icon=icon_svg("location-dot"),
                    ),
                    ui.accordion_panel(
                        "Select Survey data",
                        ui.input_switch(
                            "alpha_code",
                            "Show 4-letter Alpha Code instead of Common Name",
                            False,
                        ),
                        ui.input_switch(
                            "genus_species",
                            "Show Genus + Species instead of Common Name",
                            False,
                        ),
                        ui.input_selectize(
                            "specimen", label="Select the specimen observed", choices={}
                        ),
                        ui.input_selectize(
                            "count",
                            label="Count observed",
                            choices=survey_config["count"],
                        ),
                        ui.input_radio_buttons(
                            "plant_survey",
                            "Is it a vegetation survey?",
                            ["Yes", "No"],
                            selected="No",
                            inline=True,
                        ),
                        ui.panel_conditional(
                            "input.plant_survey === 'Yes'",
                            ui.input_selectize(
                                "canopy_cover",
                                "Select the canopy cover",
                                choices=survey_config["canopy_cover"],
                            ),
                            ui.input_selectize(
                                "abundance",
                                label="Select the abundance",
                                choices=survey_config["abundance_category"],
                            ),
                            ui.input_selectize(
                                "life_stage",
                                "Select the life stage",
                                choices=survey_config["life_stage"],
                            ),
                            ui.input_numeric(
                                "height",
                                "Enter the height of the plant (in cm)",
                                0,
                                min=0,
                                max=1000,
                                step=5,
                            ),
                        ),
                        ui.input_text("notes", label="Notes"),
                        value="specimen_details",
                        icon=icon_svg("clipboard"),
                    ),
                    id="accordion_data_sources",
                    multiple=False,
                ),
                ui.tooltip(
                    ui.input_file(
                        "image_file",
                        "Upload Image file(s) for specimen (optional)",
                        accept=[".jpg", ".png", ".jpeg"],
                        multiple=True,
                    ),
                    "Uploads image to imgur.com",
                    id="upload_image_tooltip",
                ),
                ui.tooltip(
                    ui.input_task_button(
                        "submit",
                        "Record observation",
                        class_="btn btn-success",
                        icon=icon_svg("check"),
                        label_busy="Recording...",
                        icon_busy=loading_tag,
                    ),
                    "Saves the observation locally without uploading",
                    id="submit_observation_tooltip",
                ),
                ui.input_action_button(
                    "next_screen",
                    "Proceed to uploading observations",
                    class_="btn btn-outline-primary",
                    icon=icon_svg("arrow-right"),
                ),
                fillable=True,
                inline=True,
            ),
            ui.card(ui.output_ui("notes", fillable=True, inline=True)),
            col_widths=[3, 9],
            class_="shiny-input-full-width",
        ),
        icon=icon_svg("magnifying-glass"),
        value="record",
    )


def verify_observation(survey_config, keyfile_path):
    return (
        ui.nav_panel(
            "Upload observations",
            ui.value_box(
                "Remember to upload your data!",
                "",
                ui.markdown(
                    "To ensure your field data is not lost, please take a minute to upload your data to Google Sheets by clicking on the **ϟ Upload all observations** button.",
                ),
                showcase=woman_reminding,
                theme="bg-gradient-orange-yellow",
                id="reminder",
            ),
            ui.card(
                ui.tags.script(
                    """
                    let isWide = null;
                    function updateIsWide() {
                        const prevIsWide = isWide;
                        isWide = window.innerWidth > 600;
                        if (prevIsWide !== isWide) {
                            Shiny.setInputValue("isWide", isWide);
                        }
                    }
                    const setIsWide = function() {
                        if (Shiny.setInputValue) {
                            updateIsWide();
                        } else {
                            setTimeout(setIsWide, 2);
                        }
                    }
                    $( window ).on( "resize", setIsWide );
                    setIsWide();
                    """
                ),
                ui.panel_conditional(
                    "input.isWide",
                    ui.TagList(
                        ui.output_data_frame("observations_data_frame"),
                        ui.br(),
                        ui.br(),
                        ui.tooltip(
                            ui.input_action_button(
                                "reset",
                                "Clear selected observation",
                                class_="btn btn-outline-danger",
                                icon=icon_svg("snowplow"),
                                width="300px",
                            ),
                            "In case user entered an observation in error",
                            id="clear_observation_tooltip",
                        ),
                    ),
                ),
                ui.panel_conditional(
                    "!input.isWide", ui.output_ui("observations_list")
                ),
            ),
            ui.page_fluid(
                ui.card(
                    ui.card(
                        ui.input_radio_buttons(
                            id="google_sheet_selector",
                            label="Select Google Sheet to upload data",
                            choices=get_sheets(survey_config, keyfile_path),
                            selected=None,
                            inline=True,
                        ),
                        id="google_sheets_selector",
                    ),
                    ui.tooltip(
                        ui.input_task_button(
                            "upload",
                            "Upload all observations",
                            class_="btn btn-success",
                            icon=icon_svg("bolt-lightning"),
                            width="300px",
                            label_busy="uploading...",
                            icon_busy=loading_tag,
                        ),
                        "Saves all the observations to the database",
                        id="upload_all_observations",
                    ),
                    ui.markdown(
                        f"""
            Find all uploaded observations in this [link]({survey_config["database_link"]})
            """
                    ),
                    ui.input_action_button(
                        "previous_screen",
                        "Go back to recording observation(s)",
                        class_="btn btn-outline-primary",
                        icon=icon_svg("arrow-left"),
                        width="300px",
                    ),
                    ui.markdown(
                        """
                    If your observations got lost because <br>
                    of a bad connection or page refresh before uploading, don't worry!<br>
                    You can bring them back by clicking<br>
                    the **"Restore Observation(s)"** button below.
                    """
                    ),
                    ui.tooltip(
                        ui.input_task_button(
                            "restore",
                            "Restore observation(s)",
                            class_="btn btn-warning",
                            icon=icon_svg("trash-arrow-up"),
                            width="300px",
                            label_busy="Restoring...",
                            icon_busy=loading_tag,
                        ),
                        "In case you want to restore an observation which was lost before it could be uploaded",
                        id="restore_observation_tooltip",
                    ),
                    ui.tags.script(
                        """
                        $(document).ready(function () {
                        Shiny.addCustomMessageHandler("restore", function (message) {

                            if (message === "restore") {
                                Shiny.setInputValue("restore_df", localStorage.getItem("df"));
                            } else if (message === "complete") {
                                Shiny.setInputValue("restore_df", null);
                                }

                        });
                        

                        Shiny.addCustomMessageHandler("df", function (message) {
                            localStorage.setItem("df", message);
                            Shiny.setInputValue("local_storage_df", localStorage.getItem("df"));
                        });


                        Shiny.addCustomMessageHandler("clear", function (message) {
                            if (message === "clear") {
                            console.log("clear the store");
                                localStorage.removeItem("df");
                                return;
                            }
                        });
                        });
                    """
                    ),
                ),
            ),
            icon=icon_svg("cloud-arrow-up"),
            value="verify",
        ),
    )
