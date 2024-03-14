# Field surveys App

We developed an interactive web application to facilitate multi-taxon field sampling and data collection using the Shiny for Python platform. This app serves the following purposes:

1. It allows researchers, citizen scientists, students, and others to easily design and conduct standardized surveys for various organisms, such as arthropods, birds, and plants.
2. The app is accessible on any device with an internet connection, including desktops, laptops, tablets, and smartphones.

This user-friendly application streamlines the process of field sampling and data collection, making it more efficient and accessible to a wide range of users, regardless of their technical expertise or location.

![App Demo](https://tinyurl.com/demoimg)

## Table of contents

- [Field surveys App](#field-surveys-app)
  - [Table of contents](#table-of-contents)
  - [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Data CSV files](#data-csv-files)
  - [keyfile.json](#keyfilejson)
    - [Enable API Access for a Project](#enable-api-access-for-a-project)
    - [Using Service Account](#using-service-account)
  - [Google sheets and Google Drive folder configured](#google-sheets-and-google-drive-folder-configured)
  - [survey.yaml file](#surveyyaml-file)
  - [Run the app on your machine](#run-the-app-on-your-machine)
  - [Deploying the app on the web (so it can be accessed from anywhere)](#deploying-the-app-on-the-web-so-it-can-be-accessed-from-anywhere)
  - [Demo](#demo)
  - [Issues/Feature requests](#issuesfeature-requests)

## Installation

```bash
pip install fieldsurveys
```

## Prerequisites

- Python 3.9 or higher (Install python from [here](https://www.python.org/downloads/))
- Data CSV files (see instructions [below](#data-csv-files))
- keyfile.json (see instructions [below](#keyfilejson))
- Google sheets and Google Drive folders shared with the client_email from the keyfile.json file (see instructions [below](#google-sheets-and-google-drive-folder-configured))
- survey.yaml file (see instructions [below](#surveyyaml-file))

Please ensure that you have all the prerequisites before proceeding with running the app.

## Data CSV files

If you do not know what a CSV file is or how to create one, read this [article](https://www.computerhope.com/issues/ch001356.htm) to get you started.
The app requires users to upload data CSV files. These CSV files should contain the data that the user wants to collect during the survey. The CSV files must have the following headers (first line) in the specified order:

1. Common Name
2. Genus
3. Species

The app also supports an additional column called ***Alpha Code***, but it is not mandatory.

An example is shown below:

```csv
Alpha Code,Common Name,Genus,Species
PLOC,American sycamore,Platanus,occidentalis
SALA,Arroyo willow,Salix,lasiolepis
PEAM,Avocado,Persea,americana
ARGL,Big berry manzanita,Arctostaphylos,glauca
ACMA,Bigleaf maple,Acer,macrophyllum
```

Ensure your CSV file follows the required format before uploading. You can use multiple CSV files, one for each survey type (e.g., plants, trees, grasses).

## keyfile.json

To download the keyfile.json for your Google Cloud account as a first-time user, follow these steps:


### Enable API Access for a Project
- Head to [Google Developers Console](https://console.developers.google.com/) and create a new project (or select the one you already have).

- In the box labeled “Search for APIs and Services”, search for “Google Drive API” and enable it.

- In the box labeled “Search for APIs and Services”, search for “Google Sheets API” and enable it.

### Using Service Account
A service account is a special type of Google account intended to represent a non-human user that needs to authenticate and be authorized to access data in Google APIs.

Since it’s a separate account, by default it does not have access to any spreadsheet until you share it with this account. Just like any other Google account.

Here’s how to get one:

1. Enable API Access for a Project if you haven’t done it yet.

2. Go to “APIs & Services > Credentials” and choose “Create credentials > Service account key”.

3. Fill out the form

4. Click “Create” and “Done”.

5. Press “Manage service accounts” above Service Accounts.

6. Press on ⋮ near recently created service account and select “Manage keys” and then click on “ADD KEY > Create new key”.

7. Select JSON key type and press “Create”.

8. You will automatically download a JSON file with credentials. It may look like this:

    ```json
    {
        "type": "service_account",
        "project_id": "api-project-XXX",
        "private_key_id": "2cd … ba4",
        "private_key": "-----BEGIN PRIVATE KEY-----\nNrDyLw … jINQh/9\n-----END PRIVATE KEY-----\n",
        "client_email": "473000000000-yoursisdifferent@developer.gserviceaccount.com",
        "client_id": "473 … hd.apps.googleusercontent.com",
        ...
    }
    ```

9. Navigate to the path to the downloaded credentials filerename and rename this file to `keyfile.json`
10. Open the `keyfile.json` file and get the value of client_email from this file.
11. Proceed to the next section to configure your Google sheets and Google drive folder.

## Google sheets and Google Drive folder configured

1. Create a new google spreadsheet that you want your survey data to live in. You can create a new workbook by going to [Google Sheets](https://docs.google.com/spreadsheets/u/0/) and clicking on the **+** button for blank spreadsheet. You can also use an existing workbook if you have one. Give it an appropriate name and make sure it has the same name as the one you provide in the survey.yaml file.
  
2. Using that spreadsheet name and share it with a client_email from the step above. Just like you do with any other Google account. Make sure the service account has editor access to the google sheet.

3. Create a new Google Drive folder where you want to store the specimen images during the survey. You can create a new folder by going to [Google Drive](https://drive.google.com/drive/my-drive) and clicking on the "+ New" button for new folder. You can also use an existing folder if you have one. Give it an appropriate name.

4. To share that Google Drive folder, right-click on the folder and select "Share". Then, share it with the client_email from the step above. Make sure the service account has editor access to the Google Drive folder.

## survey.yaml file

This is the config file that allows the user to configure the app to their specific needs. The *survey.yaml* file should be created using the **Survey App config generator** over [here](https://nafcillincat.shinyapps.io/survey_config_generator/). The **Survey App config generator** allows the user to create a survey.yaml file by providing the following information in a step-by-step process:

1. Surveyor names
2. Survey locations
3. Survey plots
4. Survey points
5. Survey sides
6. Survey data sources
7. Company logo url
8. Database link
9. Google Workbook Name
10. Google Drive Folder Id

## Run the app on your machine

To instantiate the app, run the following command in your terminal:

```bash
fieldsurveys
```

Follow the instructions on the screen to select your survey.yaml, data CSV files, and keyfile.json. It will then ask you for the directory where you want to store the app. Once you have provided all the necessary information, the app will be created in the specified directory.

## Deploying the app on the web (so it can be accessed from anywhere)

To deploy the app on the web, you can use the Shinyapps.io platform. You can follow the instructions [here](https://docs.posit.co/shinyapps.io/getting-started.html#working-with-shiny-for-python) to deploy your app on the Shinyapps.io platform.

## Demo

If you want to play around with the app before setting up one for your case, feel free to go over to this [link](https://nafcillincat.shinyapps.io/demo_app) and explore the app and the features it offers.

## Issues/Feature requests

If you encounter any issues or have any feature requests, please feel free to open an issue on the GitHub repository [here](https://github.com/karangattu/fieldsurveys/issues)