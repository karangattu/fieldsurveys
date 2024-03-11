import ast
import datetime
import json
from pathlib import Path
from typing import List

import gspread_dataframe as gd
import pandas as pd
import pytz
import shinyswatch
import sys
import yaml
from faicons import icon_svg
from shiny import App, reactive, render, req, ui
from shiny.types import NavSetArg
from timezonefinder import TimezoneFinder

from fieldsurveys.app_files.image_upload import (
    upload_image_to_drive,
)
from fieldsurveys.app_files.navbar_utils import (
    record_observation,
    verify_observation,
    loading_tag,
)
from fieldsurveys.app_files.utils import (
    fetch_specimen_classification,
    get_species_image,
    get_summary_for_specimen,
    get_weather_underground_temperature,
    get_workbook,
)
import os

default_survey_path = os.path.join(os.path.dirname(__file__), "survey.yaml")
default_csv_dir = os.path.join(os.path.dirname(__file__), "data")
default_keyfile_path = os.path.join(os.path.dirname(__file__), "keyfile.json")


def make_app(
    survey_path: str = default_survey_path,
    *,
    csv_dir: str = default_csv_dir,
    keyfile_path: str = default_keyfile_path,
) -> App:
    with open(survey_path, "r") as file:
        survey_config = yaml.safe_load(file)

    required_fields = {
        "surveyors": "Surveyors",
        "location": "Location",
        "plots": "Plots",
        "google_workbook_name": "Google workbook name",
        "company_logo_url": "Company logo URL",
        "survey_data_sources": "Survey data sources",
        "database_link": "Database link",
        "google_folder_id": "Google folder ID",
    }

    for field, field_name in required_fields.items():
        if field not in survey_config or not survey_config[field]:
            print(f"{field_name} is not configured in the config file")
            sys.exit(1)

    # check if survey_data_sources values are the same as the file names in the data dir
    for data_source in survey_config.get("survey_data_sources", []):
        if not os.path.exists(f"{csv_dir}/{data_source}.csv"):
            print(f"Data source {data_source}.csv is missing in the data directory")
            print(
                "Either delete the data source in the csv or add the data source to the data directory"
            )
            sys.exit(1)

    def nav_controls(prefix: str) -> List[NavSetArg]:
        return [
            record_observation(survey_config),
            verify_observation(survey_config, keyfile_path),
        ]

    default_url = "https://i.imgur.com/e2IqrgC.png"
    img_url = (
        survey_config["company_logo_url"]
        if survey_config["company_logo_url"]
        else default_url
    )
    app_ui = ui.page_navbar(
        shinyswatch.theme.minty(),
        title=ui.tags.img(src=img_url, width="125px"),
        *nav_controls("page_navbar"),
        id="page_navbar",
        header=ui.tags.link(href="styles.css", rel="stylesheet"),
        window_title="Survey App",
    )

    def server(input, output, session):
        new_df = pd.DataFrame(
            [],
            columns=[
                "Data Source",
                "Bandwidth Saver",
                "Date observed",
                "Location",
                "Plot",
                "Surveyors",
                "Survey Point",
                "Side",
                "Class",
                "Order",
                "Family",
                "Common Name",
                "Genus",
                "Species",
                "Count",
                "Notes",
                "Canopy cover",
                "Life stage",
                "Height (cm)",
                "Abundance",
            ],
        )
        val = reactive.Value(new_df)
        notes_val = reactive.Value(None)
        accuracy_val = reactive.Value(None)
        url_val = reactive.Value(None)
        index_to_delete_val = reactive.Value(None)

        @reactive.Effect
        async def _upload():
            df = data_source()
            notes_val.set(None)
            req(input.specimen())
            x = str(input.specimen())
            cols_to_check = ["Alpha Code", "Common Name", "Genus", "Species"]
            all_exist = all(elem in df.columns for elem in cols_to_check)

            if not df.empty and all_exist:
                if input.alpha_code():
                    req(any((df["Alpha Code"] == x)))
                    species_data = df.loc[df["Alpha Code"] == x].iloc[0]
                elif input.genus_species():
                    req(any((df["Genus"] + " " + df["Species"] == x)))
                    species_data = df.loc[df["Genus"] + " " + df["Species"] == x].iloc[
                        0
                    ]
                else:
                    req(any((df["Common Name"] == x)))
                    species_data = df.loc[df["Common Name"] == x].iloc[0]
                genus = species_data["Genus"]
                species = species_data["Species"]
                unknown_values = ["unknown", "Unknown", "UNKOWN", "None", "other"]
                if not input.low_data_mode():
                    id_notes = get_summary_for_specimen(genus, species)
                    if genus not in unknown_values and species not in unknown_values:
                        image_url = get_species_image(genus, species, image_number=0)
                        image_url_2 = get_species_image(genus, species, image_number=1)
                    elif genus in unknown_values and species in unknown_values:
                        results = fetch_specimen_classification(
                            genus=genus,
                            species=species,
                            common_name=species_data["Common Name"],
                        )
                        order = results["order"]
                        image_url = get_species_image(
                            order=order, genus=genus, species=species, image_number=0
                        )
                        image_url_2 = get_species_image(
                            order=order, genus=genus, species=species, image_number=1
                        )
                    elif genus not in unknown_values and species in unknown_values:
                        species = ""
                        image_url = get_species_image(genus, species, image_number=0)
                        image_url_2 = get_species_image(genus, species, image_number=1)
                    elif x.lower().startswith("unknown"):
                        results = fetch_specimen_classification(
                            genus=genus,
                            species=species,
                            common_name=species_data["Common Name"],
                        )
                        order = results["order"]
                        image_url = get_species_image(order=order, image_number=0)
                        image_url_2 = get_species_image(order=order, image_number=1)
                    if genus not in unknown_values and species not in unknown_values:
                        m = ui.TagList(
                            ui.markdown(
                                f"### <ins>{species_data['Common Name']}</ins> notes"
                            ),
                            ui.h6("Source: Wikipedia"),
                            id_notes,
                            ui.br(),
                            ui.br(),
                            ui.markdown(
                                f"### <ins>{species_data['Common Name']}</ins> pics"
                            ),
                            ui.h6("Source: iNaturalist"),
                            ui.tags.img(
                                src=image_url, style="width: 100%;height: auto"
                            ),
                            ui.tags.img(
                                src=image_url_2, style="width: 100%;height: auto"
                            ),
                        )
                        notes_val.set(m)

        @render.ui
        def notes():
            return notes_val.get()

        @reactive.Calc
        def data_source():
            df = pd.read_csv(
                f"{csv_dir}/{input.data_source()}.csv", keep_default_na=False
            )
            if "Alpha Code" not in df.columns:
                df["Alpha Code"] = None
            return df

        @reactive.Effect
        def _gps_loc():
            ui.update_text(
                "gps_loc",
                label="GPS Location",
                value=f"{input.latitude()}, {input.longitude()}",
            )

        @output
        @render.text
        def note_accuracy():
            return accuracy_val.get()

        @reactive.Effect
        def _specimen():
            df = data_source()
            if input.alpha_code():
                if "Alpha Code" in df.columns:
                    ui.update_selectize(
                        "specimen",
                        label="Select the specimen observed",
                        choices=list(df["Alpha Code"]),
                        selected="",
                    )
            elif input.genus_species():
                ui.update_selectize(
                    "specimen",
                    label="Select the specimen observed",
                    choices=list(df["Genus"] + " " + df["Species"]),
                    selected="",
                )
            else:
                if "Common Name" in df.columns:
                    ui.update_selectize(
                        "specimen",
                        label="Select the specimen observed",
                        choices=list(df["Common Name"]),
                        selected="",
                    )

        def show_deletion_modal():
            df = val.get()
            index = int(index_to_delete_val.get())
            m = ui.modal(
                ui.br(),
                ui.markdown("### Confirm deletion"),
                ui.markdown(
                    f"Are you sure you want to delete this observation for {df.loc[index, 'Common Name']}?"
                ),
                ui.br(),
                ui.br(),
                ui.layout_columns(
                    ui.input_action_button(
                        "cancel",
                        "Cancel",
                        class_="btn btn-danger",
                        icon=icon_svg("xmark"),
                    ),
                    ui.input_action_button(
                        "confirm_deletion",
                        "Delete",
                        class_="btn btn-success",
                        icon=icon_svg("trash"),
                    ),
                    col_widths=[6, 6],
                ),
                footer=None,
            )
            return m

        @reactive.Effect
        @reactive.event(input.cancel)
        def cancel():
            ui.modal_remove()

        @reactive.Effect
        @reactive.event(input.confirm_deletion)
        def confirm_deletion():
            ui.modal_remove()
            df = val.get()
            index = index_to_delete_val.get()
            df = delete_row_in_df(df, index)
            val.set(df)

            m = ui.modal(
                "Your observation has been cleared",
                easy_close=True,
                footer=None,
            )
            ui.modal_show(m)

        @reactive.Effect
        @reactive.event(input.reset)
        def _reset():
            df = val.get()
            if not df.empty:
                index_to_delete = list(input.observations_data_frame_selected_rows())
                if index_to_delete and index_to_delete[0] in df.index:
                    index_to_delete_val.set(index_to_delete[0])
                    ui.modal_show(show_deletion_modal())

        @reactive.Effect
        @reactive.event(input.upload)
        async def _send_msg_to_reset():
            await session.send_custom_message("clear", "clear")

        @reactive.Effect
        @reactive.event(input.upload)
        async def _upload():
            workbook = get_workbook(survey_config, keyfile_path)
            worksheet = workbook.worksheet(input.google_sheet_selector())
            data = worksheet.get_all_values()

            df = pd.DataFrame(data)

            nan_rows = df.index[df.isnull().all(axis=1)]
            if nan_rows.empty:
                next_row_number = worksheet.row_count
                include_column_header = False
            else:
                next_row_number = int(nan_rows[0])
                include_column_header = True
            df = val.get()
            if not df.empty:
                df = df.drop(
                    columns=[
                        "Data Source",
                        "Bandwidth Saver",
                    ]
                )
                gd.set_with_dataframe(
                    worksheet,
                    df,
                    row=next_row_number + 1,
                    resize=True,
                    include_column_header=include_column_header,
                )
                df = val.get()
                # Clear the DataFrame by creating a new empty one
                df = pd.DataFrame(columns=df.columns)
                val.set(df)
                ui.update_selectize(
                    "survey_side",
                    label="Select the side",
                    choices=survey_config["survey_side"],
                )
                ui.update_text("gps_loc", label="GPS Location", value="")
                ui.update_selectize(
                    "canopy_cover",
                    label="Select the canopy cover",
                    choices=survey_config["canopy_cover"],
                )
                ui.update_accordion_panel(
                    id="accordion_data_sources",
                    target="survey_points",
                    value="survey_points",
                    show=True,
                    icon=icon_svg("location-dot"),
                )
                m = ui.modal(
                    "Your observations have been synced",
                    easy_close=True,
                    footer=None,
                )
                ui.modal_show(m)

        @reactive.Effect
        @reactive.event(input.gps)
        def _gps():
            accuracy_val.set(None)
            ui.insert_ui(
                ui.TagList(
                    ui.tags.script(
                        """
                        $(document).ready(function () {
                            Shiny.setInputValue("accuracy", null);
                            navigator.geolocation.getCurrentPosition(onSuccess, onError, {
                                    enableHighAccuracy: true,
                                    timeout: 5000,
                                    maximumAge: 0
                            });

                            function onError(err) {
                                var errorMessage;
                                switch (err.code) {
                                case err.PERMISSION_DENIED:
                                    errorMessage = "Please approve location access";
                                    break;
                                case err.POSITION_UNAVAILABLE:
                                    errorMessage = "Location information is unavailable";
                                    break;
                                case err.TIMEOUT:
                                    errorMessage = "The request to get user location timed out";
                                    break;
                                default:
                                    errorMessage = "An unknown error occurred";
                                    break;
                                }
                                Shiny.setInputValue("lat", errorMessage);
                            }

                            function onSuccess(position) {
                                var coords = position.coords;
                                Shiny.setInputValue("latitude", coords.latitude);
                                Shiny.setInputValue("longitude", coords.longitude);
                                Shiny.setInputValue("gps_loc", coords.latitude + ", " + coords.longitude);
                                Shiny.setInputValue("accuracy", coords.accuracy);
                            }
                            });
                        """
                    ),
                ),
                selector="#gps",
                where="afterBegin",
            )

        @reactive.Effect
        def _accuracy_val():
            req(input.accuracy())
            accuracy_val.set(f"Accuracy of location: {input.accuracy()} meters")
            ui.update_task_button(id="gps", state="ready")

        @reactive.Effect
        def _genus_species_toggle():
            req(input.genus_species())
            ui.update_switch(id="alpha_code", value=False)

        @reactive.Effect
        def _alpha_code_toggle():
            req(input.alpha_code())
            ui.update_switch(id="genus_species", value=False)

        @reactive.Effect
        @reactive.event(input.submit)
        def _submit():
            if not str(input.surveyors()) == "" and not str(input.specimen()):
                m = (
                    ui.modal(
                        "Surveyor(s) and specimen observed are required fields.",
                        title="Missing required fields",
                        easy_close=True,
                    ),
                )
                ui.modal_show(m)
            req(input.surveyors())
            req(input.specimen())
            df = data_source()
            if input.alpha_code():
                species = df.loc[
                    df["Alpha Code"] == str(input.specimen()), "Species"
                ].values[0]
                genus = df.loc[
                    df["Alpha Code"] == str(input.specimen()), "Genus"
                ].values[0]
                common_name = df.loc[
                    df["Alpha Code"] == str(input.specimen()), "Common Name"
                ].values[0]
            elif input.genus_species():
                species = str(input.specimen()).split(" ")[1]
                genus = str(input.specimen()).split(" ")[0]
                common_name = df.loc[
                    df["Genus"] + " " + df["Species"] == str(input.specimen()),
                    "Common Name",
                ].values[0]
            else:
                species = df.loc[
                    df["Common Name"] == str(input.specimen()), "Species"
                ].values[0]
                genus = df.loc[
                    df["Common Name"] == str(input.specimen()), "Genus"
                ].values[0]
                common_name = str(input.specimen())
            results = fetch_specimen_classification(
                genus=genus, species=species, common_name=common_name
            )
            if input.image_file() and input.image_file() is not None:
                url_list = []
                for image in input.image_file():
                    path = image["datapath"]
                    url = upload_image_to_drive(survey_config, path, keyfile_path)
                    url_list.append(url)
                url_val.set(url_list)
                file_id = url_val.get()[0].split('=')[-1]
                thumbnail_link = f"https://drive.google.com/thumbnail?id={file_id}&sz=640"
                input.image_file().clear()
                ui.remove_ui(selector="div:has(> #image_file-label)")
                ui.insert_ui(
                    ui.input_file(
                        "image_file",
                        "Upload Image File (optional)",
                        accept=[".jpg", ".png", ".jpeg"],
                        multiple=False,
                    ),
                    selector="#submit",
                    where="beforeBegin",
                )
                m = ui.modal(
                    ui.br(),
                    ui.markdown("### Verify your observation"),
                    ui.markdown(f"**Genus:** *{results['genus']}*"),
                    ui.markdown(f"**Species:** *{results['species']}*"),
                    ui.markdown(f"**Common Name:** *{common_name}*"),
                    ui.markdown(f"**Count:** *{str(input.count())}*"),
                    ui.br(),
                    ui.tags.img(src=thumbnail_link, height="100%", width="100%"),
                    ui.br(),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button(
                            "edit",
                            "Edit observation",
                            class_="btn btn-danger",
                            icon=icon_svg("pen-to-square"),
                        ),
                        ui.input_task_button(
                            "submit_verify",
                            "Looks good",
                            class_="btn btn-success",
                            icon=icon_svg("check"),
                            label_busy="Submitting...",
                            icon_busy=loading_tag,
                        ),
                        col_widths=[6, 6],
                    ),
                    footer=None,
                )
            else:
                m = ui.modal(
                    ui.br(),
                    ui.markdown("### Verify your observation"),
                    ui.markdown(f"**Genus:** *{results['genus']}*"),
                    ui.markdown(f"**Species:** *{results['species']}*"),
                    ui.markdown(f"**Common Name:** *{common_name}*"),
                    ui.markdown(f"**Count:** *{str(input.count())}*"),
                    ui.br(),
                    ui.layout_columns(
                        ui.input_action_button(
                            "edit",
                            "Edit observation",
                            class_="btn btn-danger",
                            icon=icon_svg("pen-to-square"),
                        ),
                        ui.input_task_button(
                            "submit_verify",
                            "Looks good",
                            class_="btn btn-success",
                            icon=icon_svg("check"),
                            label_busy="Submitting...",
                            icon_busy=loading_tag,
                        ),
                        col_widths=[6, 6],
                    ),
                    footer=None,
                )
            ui.modal_show(m)

        def delete_row_in_df(df, index):
            df.drop(index, inplace=True)
            df = pd.DataFrame(df)
            # Reindex the DataFrame
            df.reset_index(drop=True, inplace=True)
            return df

        @output
        @render.ui
        def observations_list():
            m = []
            for index, row in val.get().iterrows():
                m.append(get_card_data(index=index, row=row))
            return ui.TagList(
                m,
            )

        def get_card_data(index, row):
            date_observed = row["Date observed"]
            location = row["Location"]
            plot = row["Plot"]
            surveyors = row["Surveyors"]
            survey_point = row["Survey Point"]
            side = row["Side"]
            common_name = row["Common Name"]
            count = row["Count"]
            notes = row["Notes"]
            canopy_cover = row["Canopy cover"]
            life_stage = row["Life stage"]
            height = row["Height (cm)"]
            abundance = row["Abundance"]
            if str(input.plant_survey()) == "Yes":
                return ui.card(
                    ui.card_header(
                        ui.h4(f"{common_name}"),
                    ),
                    ui.markdown(f"**Date observed:** {date_observed}"),
                    ui.markdown(f"**Location:** {location}"),
                    ui.markdown(f"**Plot:** {plot}"),
                    ui.markdown(f"**Survey Point:** {survey_point}"),
                    ui.markdown(f"**Side:** {side}"),
                    ui.markdown(f"**Count:** {count}"),
                    ui.markdown(f"**Notes:** {notes}"),
                    ui.markdown(f"**Canopy cover:** {canopy_cover}"),
                    ui.markdown(f"**Life stage:** {life_stage}"),
                    ui.markdown(f"**Height (cm):** {height}"),
                    ui.markdown(f"**Abundance:** {abundance}"),
                    ui.input_action_button(
                        f"delete_{index}",
                        label="",
                        icon=icon_svg("trash"),
                        class_="btn btn-outline-danger",
                        width="px",
                    ),
                )
            else:
                return ui.card(
                    ui.card_header(
                        ui.h4(f"{common_name}"),
                    ),
                    ui.markdown(f"**Date observed:** {date_observed}"),
                    ui.markdown(f"**Location:** {location}"),
                    ui.markdown(f"**Plot:** {plot}"),
                    ui.markdown(f"**Survey Point:** {survey_point}"),
                    ui.markdown(f"**Side:** {side}"),
                    ui.markdown(f"**Count:** {count}"),
                    ui.markdown(f"**Notes:** {notes}"),
                    ui.input_action_button(
                        f"delete_{index}",
                        label="",
                        icon=icon_svg("trash"),
                        class_="btn btn-outline-danger",
                    ),
                )

        delete_hooks: list[reactive.Effect] = []

        @reactive.effect
        @reactive.event(val)
        def _delete_hooks():
            def make_hook(index):
                @reactive.Effect
                @reactive.event(input[f"delete_{index}"])
                def delete_row():
                    index_to_delete_val.set(index)
                    ui.modal_show(show_deletion_modal())

                return delete_row

            for index in range(len(val.get().index)):
                if index >= len(delete_hooks):
                    delete_hooks.append(make_hook(index))

        @output
        @render.data_frame
        def observations_data_frame():
            if str(input.plant_survey()) == "Yes":
                return render.DataGrid(
                    val.get()[
                        [
                            "Date observed",
                            "Location",
                            "Plot",
                            "Surveyors",
                            "Survey Point",
                            "Side",
                            "Common Name",
                            "Count",
                            "Notes",
                            "Canopy cover",
                            "Life stage",
                            "Height (cm)",
                            "Abundance",
                        ]
                    ],
                    row_selection_mode="single",
                )
            else:
                return render.DataGrid(
                    val.get()[
                        [
                            "Date observed",
                            "Location",
                            "Plot",
                            "Survey Point",
                            "Side",
                            "Common Name",
                            "Count",
                            "Notes",
                        ]
                    ],
                    row_selection_mode="single",
                )

        @reactive.Effect
        @reactive.event(input.restore)
        async def _send_msg_to_restore():
            await session.send_custom_message("restore", "restore")

        @reactive.Effect
        @reactive.event(input.restore_df)
        async def _restore_observations():
            df_string = input.restore_df()
            req(df_string)
            newValue = val.get()
            if df_string and newValue.empty:
                df_json = json.loads(df_string)
                restored_val = str(df_json)
                restored_df = pd.DataFrame(ast.literal_eval(restored_val))
                if not newValue.equals(restored_df):
                    ui.update_selectize(
                        id="surveyors",
                        label="Choose Surveyor(s)*:",
                        choices=survey_config["surveyors"],
                        selected=restored_df.iloc[-1]["Surveyors"].split(", "),
                    )
                    ui.update_selectize(
                        id="location",
                        label="Select the location",
                        choices=survey_config["location"],
                        selected=restored_df.iloc[-1]["Location"],
                    )
                    ui.update_selectize(
                        id="plot",
                        label="Select the plot",
                        choices=survey_config["plots"],
                        selected=restored_df.iloc[-1]["Plot"],
                    )
                    ui.update_selectize(
                        id="survey_point",
                        label="Select the survey point",
                        choices=survey_config["survey_points"],
                        selected=restored_df.iloc[-1]["Survey Point"],
                    )
                    ui.update_selectize(
                        id="survey_side",
                        label="Select the side",
                        choices=survey_config["survey_side"],
                        selected=restored_df.iloc[-1]["Side"],
                    )
                    ui.update_switch(
                        id="low_data_mode",
                        label="Bandwidth Saver",
                        value=restored_df.iloc[-1]["Bandwidth Saver"] == "True",
                    )
                    ui.update_radio_buttons(
                        id="data_source",
                        label="Select data source",
                        choices=survey_config["survey_data_sources"],
                        selected=restored_df.iloc[-1]["Data Source"],
                    )

                    ui.update_accordion_panel(
                        id="accordion_data_sources",
                        target="data_source",
                        title=f"Data source: {restored_df.iloc[-1]['Data Source']}",
                        value="data_source",
                        show=False,
                    )

                    ui.update_accordion_panel(
                        id="accordion_data_sources",
                        target="specimen_details",
                        value="specimen_details",
                        show=True,
                    )

                    ui.update_accordion_panel(
                        id="accordion_data_sources",
                        target="surveyors",
                        title="Surveyors: " + (restored_df.iloc[-1]["Surveyors"]),
                        value="surveyors",
                        show=False,
                    )

                    ui.update_accordion_panel(
                        id="accordion_data_sources",
                        target="survey_points",
                        title="Survey Point: "
                        + restored_df.iloc[-1]["Plot"]
                        + f" - {restored_df.iloc[-1]['Survey Point']}",
                        value="survey_points",
                        show=False,
                    )

                    val.set(restored_df)
                m = ui.modal(
                    "Your observations have been restored",
                    easy_close=True,
                    footer=None,
                )
                ui.modal_show(m)
            else:
                m = ui.modal(
                    "Nothing to restore",
                    easy_close=True,
                    footer=None,
                )
                ui.modal_show(m)
            await session.send_custom_message("restore", "complete")

        @reactive.Effect
        @reactive.event(input.next_screen)
        def _next_page():
            ui.update_navs("page_navbar", selected="verify")

        @reactive.Effect
        @reactive.event(input.previous_screen)
        def _prev_page():
            ui.update_navs("page_navbar", selected="record")

        @reactive.Effect
        @reactive.event(input.edit)
        def _edit_observation():
            ui.modal_remove()

        @reactive.Effect
        @reactive.event(input.submit_verify)
        def _submit_observation():
            df = data_source()
            if input.gps_loc():
                latitude = input.latitude()
                longitude = input.longitude()
                gps_location = input.gps_loc()
            else:
                # use the default location of the SF bay for weather if user did not provide
                latitude = "37.4803"
                longitude = "-122.0786"
                gps_location = "None given"
            if survey_config.get("timezone"):
                tz = pytz.timezone(survey_config["timezone"])
                now = datetime.datetime.now(tz)
            else:
                tf = TimezoneFinder()
                now = datetime.datetime.now(
                    pytz.timezone(
                        tf.certain_timezone_at(
                            lng=float(longitude), lat=float(latitude)
                        )
                    )
                )
            if str(input.plant_survey()) == "Yes":
                canopy_cover = str(input.canopy_cover())
                life_stage = str(input.life_stage())
                height = str(input.height())
                abundance = str(input.abundance())
            else:
                canopy_cover = None
                life_stage = None
                height = None
                abundance = None

            if input.alpha_code():
                alpha_code = str(input.specimen())
                common_name = df.loc[
                    df["Alpha Code"] == str(input.specimen()), "Common Name"
                ].values[0]
                species = df.loc[
                    df["Alpha Code"] == str(input.specimen()), "Species"
                ].values[0]
                genus = df.loc[
                    df["Alpha Code"] == str(input.specimen()), "Genus"
                ].values[0]
            elif input.genus_species():
                species = str(input.specimen()).split(" ")[1]
                genus = str(input.specimen()).split(" ")[0]
                alpha_code = df.loc[
                    df["Genus"] + " " + df["Species"] == str(input.specimen()),
                    "Alpha Code",
                ].values[0]
                common_name = df.loc[
                    df["Genus"] + " " + df["Species"] == str(input.specimen()),
                    "Common Name",
                ].values[0]
            else:
                species = df.loc[
                    df["Common Name"] == str(input.specimen()), "Species"
                ].values[0]
                genus = df.loc[
                    df["Common Name"] == str(input.specimen()), "Genus"
                ].values[0]
                alpha_code = df.loc[
                    df["Common Name"] == str(input.specimen()), "Alpha Code"
                ].values[0]
                common_name = str(input.specimen())
            results = fetch_specimen_classification(
                genus=genus, species=species, common_name=common_name
            )
            data = {
                "fields": {
                    "Bandwidth Saver": str(input.low_data_mode()),
                    "Data Source": str(input.data_source()),
                    "Date observed": str(input.survey_date()),
                    "Time observed": str(now.strftime("%I:%M %p")),
                    "Location": str(input.location()),
                    "Plot": str(input.plot()),
                    "Survey Point": str(input.survey_point()),
                    "Side": str(input.survey_side()),
                    "Genus": results["genus"],
                    "Species": results["species"],
                    "Class": results["class"],
                    "Order": results["order"],
                    "Family": results["family"],
                    "Common Name": common_name,
                    "Alpha Code": alpha_code,
                    "Count": str(input.count()),
                    "Notes": str(input.notes()),
                    "Surveyors": str(", ".join(input.surveyors())),
                    "Url": (
                        ", ".join(url_val.get()) if url_val.get() is not None else ""
                    ),
                    "Weather": get_weather_underground_temperature(
                        str(latitude), str(longitude)
                    ),
                    "GPS Location": str(gps_location),
                    "Canopy cover": canopy_cover,
                    "Life stage": life_stage,
                    "Height (cm)": height,
                    "Abundance": abundance,
                }
            }

            newValue = val.get()
            newValue = newValue._append(data["fields"], ignore_index=True)
            val.set(newValue)
            ui.notification_show(
                "Your observation has been recorded.", duration=2, type="message"
            )
            if input.alpha_code():
                ui.update_selectize(
                    "specimen",
                    label="Select the specimen observed",
                    choices=list(df["Alpha Code"]),
                    selected="",
                )
            elif input.genus_species():
                ui.update_selectize(
                    "specimen",
                    label="Select the specimen observed",
                    choices=list(df["Genus"] + " " + df["Species"]),
                    selected="",
                )
            else:
                ui.update_selectize(
                    "specimen",
                    label="Select the specimen observed",
                    choices=list(df["Common Name"]),
                    selected="",
                )
            ui.update_selectize(
                "count",
                label="Count observed",
                choices=survey_config["count"],
            )
            ui.update_selectize(
                "life_stage",
                label="Select the life stage",
                choices=survey_config["life_stage"],
            )
            ui.update_numeric(
                "height",
                label="Enter the height of the plant (in cm)",
                value=0,
                min=0,
                max=1000,
                step=5,
            )
            ui.update_selectize(
                "abundance",
                label="Select the abundance",
                choices=survey_config["abundance_category"],
            )
            ui.update_text("notes", label="Notes", value="")
            accuracy_val.set(None)
            ui.modal_remove()
            url_val.set(None)

        @reactive.Effect
        @reactive.event(input.submit_verify)
        async def _submit_msg():
            await session.send_custom_message(
                "df", str(val.get().to_json(orient="records"))
            )

        @reactive.Effect
        @reactive.event(input.go_to_surveyors)
        def _go_to_surveyors():
            ui.update_accordion_panel(
                id="accordion_data_sources",
                target="surveyors",
                value="surveyors",
                show=True,
            )
            ui.update_accordion_panel(
                id="accordion_data_sources",
                target="data_source",
                title=f"Data source: {input.data_source()}",
                value="data_source",
                show=False,
            )

        @reactive.Effect
        @reactive.event(input.go_to_survey_points)
        def _go_to_survey_points():
            req(input.surveyors())
            ui.update_accordion_panel(
                id="accordion_data_sources",
                target="survey_points",
                value="survey_points",
                show=True,
            )
            ui.update_accordion_panel(
                id="accordion_data_sources",
                target="surveyors",
                title="Surveyors: " + str(", ".join(input.surveyors())),
                value="surveyors",
                show=False,
            )

        @reactive.Effect
        @reactive.event(input.go_to_specimen)
        def _go_to_specimen():
            req(input.survey_point())
            ui.update_accordion_panel(
                id="accordion_data_sources",
                target="specimen_details",
                value="specimen_details",
                show=True,
            )
            ui.update_accordion_panel(
                id="accordion_data_sources",
                target="survey_points",
                title="Survey Point: "
                + f"{str(input.plot())} - {str(input.survey_point())}",
                value="survey_points",
                show=False,
            )

    app_dir = Path(__file__).parent
    app = App(app_ui, server, static_assets=app_dir / "www")
    return app
