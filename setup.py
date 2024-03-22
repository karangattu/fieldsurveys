from setuptools import setup, find_packages

setup(
    name="fieldsurveys",
    version="0.1.41",
    author="Karan Gathani",
    author_email="karan.gathani+fieldsurveysapp@posit.co",
    packages=find_packages(),
    description="A Python package for creating and managing field surveys.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/karangattu/fieldsurveys",
    include_package_data=True,
    package_data={"fieldsurveys": ["*"]},
    entry_points={"console_scripts": ["fieldsurveys = fieldsurveys:copy_app_files"]},
    setup_requires=["wheel"],
    install_requires=[
        "beautifulsoup4==4.12.3",
        "colorama==0.4.6",
        "cryptography==42.0.5",
        "faicons==0.2.2",
        "geopy==2.4.1",
        "google-api-python-client==2.120.0",
        "google-auth-httplib2==0.2.0",
        "google-auth-oauthlib==1.2.0",
        "google-auth==2.28.1",
        "gspread-dataframe==3.3.1",
        "gspread==6.0.2",
        "htmltools==0.5.1",
        "pandas==2.2.1",
        "plotly==5.19.0",
        "pytz==2024.1",
        "PyYAML==6.0.1",
        "questionary==2.0.1",
        "requests==2.31.0",
        "rsconnect_python==1.22.0",
        "shiny==0.7.1",
        "shinyswatch==0.4.2",
        "timezonefinder==6.4.1",
        "us==3.1.1",
        "Wikipedia-API==0.6.0",
    ],
    extras_require={
        "tests": [
            "playwright==1.41.2",
            "pytest==8.0.2",
            "pytest-mock==3.12.0",
            "pytest-playwright==0.4.4",
        ]
    },
)
